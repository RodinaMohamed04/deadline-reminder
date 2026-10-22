# My 10x Solution - Rodina Mohamed

## 1. What is the problem I am solving?

Students juggle assignments from many courses, and the deadlines are scattered across course pages, group chats, emails and notes. It is easy to forget one, or to notice it only when it is already late. A missed deadline costs marks, and the student only finds out afterwards.

This problem affects any student with several courses at once. Existing calendars do not know which assignments are finished, so they cannot tell you "this one is still open and due in three hours".

**My 10x claim:** instead of re-checking several places every day to see what is due, a student enters each assignment once and the system tells them when it is getting close. Nothing has to be remembered or checked by hand.

**Non-goal:** no front-end app and no automatic syncing with course platforms. Assignments are entered through the API.

## 2. How did I implement my solution?

**Deadline Reminder** is a backend built with Python, FastAPI and SQLite. Everything is free and runs locally with no credit card.

A student registers and logs in, then adds assignments (course, title, due date). The system labels each one as `pending`, `due_soon`, `overdue` or `completed`. A background job checks every 15 minutes and creates a reminder when an unfinished assignment enters the 72-hour, 24-hour or 3-hour window before its deadline, or when it becomes overdue. Each reminder is created only once. The student reads them in their reminder inbox, and can download a weekly PDF report showing what is overdue, due in the next 7 days, and completed this week.

### The 5 concepts

| # | Concept | How it is used |
|---|---------|----------------|
| 1 | API endpoints | REST API with proper status codes (201, 204, 401, 404, 409, 422) and input validation |
| 2 | Database | SQLite via SQLAlchemy: users, assignments, reminders; data survives restarts |
| 3 | Authentication | Register/login with hashed passwords and JWT tokens; every other route is protected and each user only sees their own data |
| 4 | Background / cron job | A scheduler runs the reminder scan every 15 minutes, off the request path; it is idempotent |
| 5 | Reporting (PDF) | `GET /reports/weekly.pdf` builds a weekly report with reportlab |

**Swaps used:** none.

### Steps to run

1. `pip install -r requirements.txt`
2. `python seed.py` (creates a demo account `demo@example.com` / `demo12345` with sample assignments)
3. `uvicorn app.main:app --reload`
4. Open `http://127.0.0.1:8000/docs`, log in with the demo account, and follow the demo path in the README.

Tests: `python -m pytest -q` (10 tests: auth, ownership, validation, reminder idempotency and escalation, PDF).
