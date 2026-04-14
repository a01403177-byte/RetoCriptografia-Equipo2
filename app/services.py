from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, Permission, RolePermission, User


class AuditService:
    @staticmethod
    def log(
        db: Session,
        *,
        event_type: str,
        action: str,
        result: str,
        actor_user_id: int | None = None,
        target_user_id: int | None = None,
        resource: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        db.add(
            AuditLog(
                event_type=event_type,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                action=action,
                resource=resource,
                result=result,
                metadata_json=metadata or {},
            )
        )
        db.commit()


class IdentityService:
    @staticmethod
    def resolve_user_from_payload(db: Session, payload: dict) -> User | None:
        sub = payload.get("sub")
        email = payload.get("email")

        user = db.scalar(select(User).options(joinedload(User.role)).where(User.auth_sub == sub))
        if user:
            return IdentityService._apply_expiration_if_needed(db, user)

        if email:
            user = db.scalar(select(User).options(joinedload(User.role)).where(User.email == email.lower()))
            if user and user.auth_sub is None:
                user.auth_sub = sub
                if user.status == "pending":
                    user.status = "active"
                user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(user)
                return IdentityService._apply_expiration_if_needed(db, user)

        return None

    @staticmethod
    def _apply_expiration_if_needed(db: Session, user: User) -> User:
        if user.end_date and user.status == "active" and user.end_date < datetime.utcnow():
            user.status = "expired"
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user


class AuthorizationService:
    @staticmethod
    def get_permissions(db: Session, user: User) -> list[dict]:
        rows = db.execute(
            select(Permission.resource, Permission.action)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == user.role_id)
        ).all()
        return [{"resource": row.resource, "action": row.action} for row in rows]

    @staticmethod
    def authorize(db: Session, user: User | None, resource: str, action: str) -> bool:
        if not user:
            return False
        if user.status != "active":
            return False
        permissions = AuthorizationService.get_permissions(db, user)
        return any(item["resource"] == resource and item["action"] == action for item in permissions)


class UserService:
    @staticmethod
    def create_user(db: Session, *, email: str, full_name: str, user_type: str, role_id: int, end_date=None) -> User:
        user = User(
            email=email.lower(),
            full_name=full_name,
            user_type=user_type,
            role_id=role_id,
            status="pending",
            end_date=end_date,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user(db: Session, user_id: int) -> User | None:
        return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))

    @staticmethod
    def list_users(db: Session) -> list[User]:
        return list(db.scalars(select(User).options(joinedload(User.role)).order_by(User.id.desc())).all())

    @staticmethod
    def update_user(db: Session, user: User, *, full_name=None, user_type=None, end_date=...) -> User:
        if full_name is not None:
            user.full_name = full_name
        if user_type is not None:
            user.user_type = user_type
        if end_date is not ...:
            user.end_date = end_date
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_status(db: Session, user: User, status: str) -> User:
        user.status = status
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_role(db: Session, user: User, role_id: int) -> User:
        user.role_id = role_id
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user


class ExpirationService:
    @staticmethod
    def expire_users(db: Session) -> int:
        users = list(
            db.scalars(
                select(User).where(
                    User.status == "active",
                    User.end_date.is_not(None),
                    User.end_date < datetime.utcnow(),
                )
            ).all()
        )

        for user in users:
            user.status = "expired"
            user.updated_at = datetime.utcnow()
            db.add(
                AuditLog(
                    event_type="user_expired",
                    actor_user_id=None,
                    target_user_id=user.id,
                    action="expire",
                    resource="users",
                    result="success",
                    metadata_json={"expired_at": datetime.now(timezone.utc).isoformat()},
                )
            )

        db.commit()
        return len(users)
