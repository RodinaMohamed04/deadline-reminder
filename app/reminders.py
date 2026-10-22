"""The background job: find assignments that are getting close and remind the student.

Idempotent: the (assignment_id, kind) unique constraint means each reminder is created once,
no matter how many times the scan runs.
"""
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import Assignment, Reminder, User, utcnow

log = logging.getLogger("reminders")


def pick_kind(hours_left: float, windows: list[int]) -> str | None:
    """Which reminder is due right now? Returns the tightest window we have entered."""
    if hours_left < 0:
        return "overdue"
    for w in sorted(windows):  # smallest first -> most urgent wins
        if hours_left <= w:
            return f"{w}h"
    return None


def build_message(a: Assignment, kind: str, hours_left: float) -> str:
    if kind == "overdue":
        return f"OVERDUE: '{a.title}' ({a.course}) was due {abs(hours_left):.0f}h ago. Submit it if you still can."
    return f"'{a.title}' ({a.course}) is due in about {max(hours_left, 0):.0f}h."


def send_email(to: str, subject: str, body: str) -> bool:
    """Optional. Only used when SMTP_HOST is configured. Never raises."""
    if not settings.SMTP_HOST:
        return False
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to, subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception:
        log.exception("email failed")
        return False


def run_scan(db: Session, now: datetime | None = None, user_id: int | None = None) -> list[Reminder]:
    now = now or utcnow()
    query = select(Assignment).where(Assignment.completed_at.is_(None))
    if user_id is not None:
        query = query.where(Assignment.user_id == user_id)

    created: list[Reminder] = []
    for a in db.scalars(query):
        hours_left = (a.due_at - now).total_seconds() / 3600
        kind = pick_kind(hours_left, settings.REMINDER_WINDOWS_HOURS)
        if kind is None:
            continue
        exists = db.scalar(
            select(Reminder.id).where(Reminder.assignment_id == a.id, Reminder.kind == kind)
        )
        if exists:
            continue
        r = Reminder(
            user_id=a.user_id,
            assignment_id=a.id,
            kind=kind,
            message=build_message(a, kind, hours_left),
        )
        db.add(r)
        try:
            db.flush()
        except IntegrityError:  # another worker beat us to it
            db.rollback()
            continue
        user = db.get(User, a.user_id)
        r.emailed = send_email(user.email, f"Deadline reminder: {a.title}", r.message)
        log.info("reminder for user %s: %s", a.user_id, r.message)
        created.append(r)
    db.commit()
    return created


def scheduled_scan() -> None:
    """Entry point for the scheduler (its own DB session, its own error handling)."""
    db = SessionLocal()
    try:
        n = len(run_scan(db))
        log.info("scan finished, %d new reminder(s)", n)
    except Exception:
        log.exception("scan failed")
    finally:
        db.close()
