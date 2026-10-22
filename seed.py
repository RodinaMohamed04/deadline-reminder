"""Create a demo student with assignments in every state.  Run:  python seed.py

Demo login:  demo@example.com / demo12345
Safe to run repeatedly (it resets the demo user's data).
"""
from datetime import timedelta

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.models import Assignment, User, utcnow
from app.security import hash_password

EMAIL, PASSWORD = "demo@example.com", "demo12345"


def main() -> None:
    init_db()
    db = SessionLocal()
    old = db.scalar(select(User).where(User.email == EMAIL))
    if old:
        db.delete(old)
        db.commit()

    user = User(email=EMAIL, name="Demo Student", password_hash=hash_password(PASSWORD))
    db.add(user)
    db.flush()

    now = utcnow()
    h = lambda hours: now + timedelta(hours=hours)  # noqa: E731
    rows = [
        ("Data Structures", "Assignment 3: Binary trees", h(-20), None),  # overdue
        ("Algorithms", "Problem set 5: Dynamic programming", h(2), None),  # inside the 3h window
        ("Digital Design", "Lab report: FSM design", h(20), None),  # inside the 24h window
        ("Microcontrollers", "Project milestone 2", h(60), None),  # inside the 72h window
        ("DSP", "Homework 4: FFT", h(24 * 6), None),  # later this week
        ("Computer Architecture", "Cache simulation", h(24 * 14), None),  # far away
        ("Algorithms", "Problem set 4: Graphs", h(-72), h(-80)),  # completed on time
    ]
    for course, title, due, done in rows:
        db.add(Assignment(user_id=user.id, course=course, title=title, due_at=due, completed_at=done))
    db.commit()
    print(f"Seeded {len(rows)} assignments. Login: {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
