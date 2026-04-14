from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    user_type: str
    role_id: int
    end_date: datetime | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    user_type: str | None = None
    end_date: datetime | None = None


class RoleChange(BaseModel):
    role_id: int


class StatusChange(BaseModel):
    reason: str | None = None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auth_sub: str | None
    email: EmailStr
    full_name: str
    user_type: str
    role_id: int
    status: str
    end_date: datetime | None
    created_at: datetime
    updated_at: datetime


class PermissionOut(BaseModel):
    resource: str
    action: str


class MeOut(BaseModel):
    user: UserOut
    role: RoleOut
    permissions: list[PermissionOut]


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    actor_user_id: int | None
    target_user_id: int | None
    action: str
    resource: str | None
    result: str
    metadata_json: dict | None
    created_at: datetime
