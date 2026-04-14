from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.security import decode_token
from app.services import AuditService, AuthorizationService, IdentityService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_token_payload(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1)
    try:
        return decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def get_current_user(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    user = IdentityService.resolve_user_from_payload(db, payload)
    if not user:
        AuditService.log(
            db,
            event_type="login_rejected",
            action="login",
            resource="auth",
            result="failure",
            metadata={"reason": "missing_local_identity", "email": payload.get("email")},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local user not found")

    if user.status != "active":
        AuditService.log(
            db,
            event_type="login_rejected",
            action="login",
            resource="auth",
            result="failure",
            actor_user_id=user.id,
            target_user_id=user.id,
            metadata={"reason": f"invalid_status:{user.status}"},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User status is {user.status}")

    return user


def require_permission(resource: str, action: str):
    def dependency(user=Depends(get_current_user), db: Session = Depends(get_db)):
        allowed = AuthorizationService.authorize(db, user, resource, action)
        if not allowed:
            AuditService.log(
                db,
                event_type="access_denied",
                actor_user_id=user.id,
                target_user_id=user.id,
                action=action,
                resource=resource,
                result="failure",
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency
