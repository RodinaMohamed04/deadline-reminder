from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Assignment, User, utcnow
from ..schemas import AssignmentCreate, AssignmentOut, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])

DUE_SOON_HOURS = 24


def to_out(a: Assignment) -> AssignmentOut:
    now = utcnow()
    hours_left = (a.due_at - now).total_seconds() / 3600
    if a.completed_at:
        st = "completed"
    elif hours_left < 0:
        st = "overdue"
    elif hours_left <= DUE_SOON_HOURS:
        st = "due_soon"
    else:
        st = "pending"
    out = AssignmentOut.model_validate(a)
    out.status = st
    out.hours_left = None if a.completed_at else round(hours_left, 1)
    return out


def get_owned(db: Session, user: User, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    # 404 (not 403) for other people's rows so ids can't be probed
    if a is None or a.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return a


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    body: AssignmentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    a = Assignment(user_id=user.id, **body.model_dump())
    db.add(a)
    db.commit()
    return to_out(a)


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    status_filter: Literal["pending", "due_soon", "overdue", "completed"] | None = Query(
        default=None, alias="status"
    ),
    course: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Assignment).where(Assignment.user_id == user.id).order_by(Assignment.due_at)
    if course:
        q = q.where(Assignment.course == course)
    items = [to_out(a) for a in db.scalars(q)]
    if status_filter:
        items = [i for i in items if i.status == status_filter]
    return items


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_out(get_owned(db, user, assignment_id))


@router.patch("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: int,
    body: AssignmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = get_owned(db, user, assignment_id)
    data = body.model_dump(exclude_unset=True)
    completed = data.pop("completed", None)
    for key, value in data.items():
        if value is None and key != "notes":
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{key} cannot be null")
        setattr(a, key, value)
    if completed is True and a.completed_at is None:
        a.completed_at = utcnow()
    elif completed is False:
        a.completed_at = None
    db.commit()
    return to_out(a)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_owned(db, user, assignment_id))
    db.commit()
