from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _to_naive_utc(value: datetime) -> datetime:
    """Accept any ISO datetime. Naive values are treated as UTC."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AssignmentCreate(BaseModel):
    course: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    due_at: datetime
    notes: str | None = Field(default=None, max_length=2000)

    _norm_due = field_validator("due_at")(_to_naive_utc)


class AssignmentUpdate(BaseModel):
    course: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None

    @field_validator("due_at")
    @classmethod
    def _norm_due(cls, v):
        return _to_naive_utc(v) if v is not None else v


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course: str
    title: str
    notes: str | None
    due_at: datetime
    completed_at: datetime | None
    status: str = "pending"
    hours_left: float | None = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assignment_id: int
    kind: str
    message: str
    emailed: bool
    created_at: datetime
