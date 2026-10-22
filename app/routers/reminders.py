from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Reminder, User
from ..reminders import run_scan
from ..schemas import ReminderOut

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
def my_reminders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Your reminder inbox, newest first."""
    q = select(Reminder).where(Reminder.user_id == user.id).order_by(Reminder.created_at.desc(), Reminder.id.desc())
    return list(db.scalars(q))


@router.post("/run", response_model=list[ReminderOut])
def run_now(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Run the reminder scan right now for your own assignments (the scheduler does this automatically)."""
    return run_scan(db, user_id=user.id)
