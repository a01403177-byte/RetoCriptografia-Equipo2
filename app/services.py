from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, Permission, Role, RolePermission, User

ROLE_DEFINITIONS = {
    "ADMIN": {
        "name": "Administrador",
        "permissions": [
            ("users", "create"),
            ("users", "view"),
            ("users", "activate"),
            ("users", "revoke"),
            ("users", "reactivate"),
            ("users", "change_role"),
            ("audit", "view"),
        ],
    },
    "HUMANITARIA": {
        "name": "Humanitaria",
        "permissions": [("records", "view"), ("records", "edit")],
    },
    "LEGAL_TI": {
        "name": "Legal TI",
        "permissions": [("documents", "view"), ("documents", "edit")],
    },
    "LECTURA": {
        "name": "Solo lectura",
        "permissions": [("records", "view"), ("documents", "view")],
    },
    "EXTERNAL": {
        "name": "Externo",
        "permissions": [("documents", "view")],
    },
}

DEMO_USERS = [
    {"full_name": "Admin Demo", "email": "admin@demo.local", "role_code": "ADMIN", "status": "active"},
    {"full_name": "Ana Humanitaria", "email": "humanitaria@demo.local", "role_code": "HUMANITARIA", "status": "active"},
    {"full_name": "Luis Externo", "email": "externo@demo.local", "role_code": "EXTERNAL", "status": "pending"},
]


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

    @staticmethod
    def list_recent(db: Session, limit: int = 20) -> list[AuditLog]:
        return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all())


class BootstrapService:
    @staticmethod
    def seed(db: Session) -> None:
        roles = list(db.scalars(select(Role)).all())
        if not roles:
            role_by_code: dict[str, Role] = {}
            permission_by_key: dict[tuple[str, str], Permission] = {}

            for code, config in ROLE_DEFINITIONS.items():
                role = Role(code=code, name=config["name"])
                db.add(role)
                db.flush()
                role_by_code[code] = role

            for config in ROLE_DEFINITIONS.values():
                for resource, action in config["permissions"]:
                    key = (resource, action)
                    if key not in permission_by_key:
                        permission = Permission(resource=resource, action=action)
                        db.add(permission)
                        db.flush()
                        permission_by_key[key] = permission

            for code, config in ROLE_DEFINITIONS.items():
                role = role_by_code[code]
                for resource, action in config["permissions"]:
                    db.add(
                        RolePermission(
                            role_id=role.id,
                            permission_id=permission_by_key[(resource, action)].id,
                        )
                    )

            db.commit()

        users = list(db.scalars(select(User)).all())
        if not users:
            roles_by_code = {role.code: role for role in db.scalars(select(Role)).all()}
            for item in DEMO_USERS:
                db.add(
                    User(
                        full_name=item["full_name"],
                        email=item["email"],
                        role_id=roles_by_code[item["role_code"]].id,
                        status=item["status"],
                    )
                )
            db.commit()


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
                    metadata_json={},
                )
            )

        db.commit()
        return len(users)


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
        if not user or user.status != "active":
            return False
        return any(
            item["resource"] == resource and item["action"] == action
            for item in AuthorizationService.get_permissions(db, user)
        )


class UserService:
    @staticmethod
    def create_user(db: Session, *, email: str, full_name: str, role_id: int, end_date=None) -> User:
        user = User(
            email=email.lower(),
            full_name=full_name,
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
        ExpirationService.expire_users(db)
        return list(db.scalars(select(User).options(joinedload(User.role)).order_by(User.id.desc())).all())

    @staticmethod
    def get_actor(db: Session, actor_id: int | None = None) -> User | None:
        ExpirationService.expire_users(db)
        if actor_id is not None:
            return UserService.get_user(db, actor_id)
        actor = db.scalar(
            select(User).options(joinedload(User.role)).join(Role).where(Role.code == "ADMIN").limit(1)
        )
        if actor:
            return actor
        return db.scalar(select(User).options(joinedload(User.role)).limit(1))

    @staticmethod
    def list_roles(db: Session) -> list[Role]:
        return list(db.scalars(select(Role).order_by(Role.name.asc())).all())

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
