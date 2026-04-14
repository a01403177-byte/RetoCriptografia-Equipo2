from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db, require_permission
from app.jobs import start_scheduler
from app.models import AuditLog, User
from app.schemas import AuditLogOut, MeOut, RoleChange, StatusChange, UserCreate, UserOut, UserUpdate
from app.services import AuditService, AuthorizationService, UserService


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/me", response_model=MeOut)
def get_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    permissions = AuthorizationService.get_permissions(db, user)
    AuditService.log(
        db,
        event_type="login_success",
        actor_user_id=user.id,
        target_user_id=user.id,
        action="login",
        resource="auth",
        result="success",
    )
    return {"user": user, "role": user.role, "permissions": permissions}


@app.post("/api/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    admin=Depends(require_permission("users", "create")),
    db: Session = Depends(get_db),
):
    user = UserService.create_user(db, **payload.model_dump())
    AuditService.log(
        db,
        event_type="user_created",
        actor_user_id=admin.id,
        target_user_id=user.id,
        action="create",
        resource="users",
        result="success",
    )
    return user


@app.get("/api/users", response_model=list[UserOut])
def list_users(
    _admin=Depends(require_permission("users", "view")),
    db: Session = Depends(get_db),
):
    return UserService.list_users(db)


@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    _admin=Depends(require_permission("users", "view")),
    db: Session = Depends(get_db),
):
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin=Depends(require_permission("users", "update")),
    db: Session = Depends(get_db),
):
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = UserService.update_user(db, user, **payload.model_dump(exclude_unset=True))
    AuditService.log(
        db,
        event_type="user_updated",
        actor_user_id=admin.id,
        target_user_id=updated.id,
        action="update",
        resource="users",
        result="success",
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


def _change_status(user_id: int, new_status: str, event_type: str, reason: str | None, admin, db: Session):
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = UserService.update_status(db, user, new_status)
    AuditService.log(
        db,
        event_type=event_type,
        actor_user_id=admin.id,
        target_user_id=updated.id,
        action=new_status,
        resource="users",
        result="success",
        metadata={"reason": reason} if reason else {},
    )
    return updated


@app.post("/api/users/{user_id}/activate", response_model=UserOut)
def activate_user(
    user_id: int,
    body: StatusChange,
    admin=Depends(require_permission("users", "activate")),
    db: Session = Depends(get_db),
):
    return _change_status(user_id, "active", "user_activated", body.reason, admin, db)


@app.post("/api/users/{user_id}/revoke", response_model=UserOut)
def revoke_user(
    user_id: int,
    body: StatusChange,
    admin=Depends(require_permission("users", "revoke")),
    db: Session = Depends(get_db),
):
    return _change_status(user_id, "revoked", "user_revoked", body.reason, admin, db)


@app.post("/api/users/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(
    user_id: int,
    body: StatusChange,
    admin=Depends(require_permission("users", "reactivate")),
    db: Session = Depends(get_db),
):
    return _change_status(user_id, "active", "user_reactivated", body.reason, admin, db)


@app.post("/api/users/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    payload: RoleChange,
    admin=Depends(require_permission("users", "change_role")),
    db: Session = Depends(get_db),
):
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = UserService.change_role(db, user, payload.role_id)
    AuditService.log(
        db,
        event_type="role_changed",
        actor_user_id=admin.id,
        target_user_id=updated.id,
        action="change_role",
        resource="users",
        result="success",
        metadata={"role_id": payload.role_id},
    )
    return updated


@app.get("/api/audit-logs", response_model=list[AuditLogOut])
def get_audit_logs(
    limit: int = 100,
    admin=Depends(require_permission("audit", "view")),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    AuditService.log(
        db,
        event_type="audit_viewed",
        actor_user_id=admin.id,
        target_user_id=admin.id,
        action="view",
        resource="audit",
        result="success",
    )
    return rows
