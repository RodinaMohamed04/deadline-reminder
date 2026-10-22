# Deadline Reminder

Students miss assignment deadlines because the dates live in five different places (course pages, chats, emails, notes). **Deadline Reminder** is one small backend where you put every assignment once, and it reminds you as each deadline gets close and sends you a weekly PDF of what is overdue, due soon, and done.

> FlyRank Internship · Backend Track · Capstone "Your 10x Solution" — Rodina Mohamed

## Concepts implemented (5 of 7, no swaps)

| # | Concept | Where it lives in the code |
|---|---------|----------------------------|
| 1 | API endpoints (status codes + validation) | `app/routers/*.py`, `app/schemas.py` |
| 2 | Database (SQLite, survives restarts) | `app/database.py`, `app/models.py` |
| 3 | Authentication (JWT, protected routes) | `app/security.py`, `app/deps.py`, `app/routers/auth.py` |
| 4 | Background / cron job (reminder scan every N minutes) | `app/reminders.py`, scheduler set up in `app/main.py` |
| 5 | Reporting — PDF | `app/pdf_report.py`, `GET /reports/weekly.pdf` |

Not used: caching, LLM integration. Swaps used: none.

## Run it (clean machine, Python 3.11+)

```bash
pip install -r requirements.txt
python seed.py                         # creates demo data (optional)
uvicorn app.main:app --reload          # http://127.0.0.1:8000/docs
```

Optional: `cp .env.example .env` and set a real `SECRET_KEY`. No secrets are needed to run the demo.

Tests (no server needed): `python -m pytest -q`

## 5-minute demo path

1. Run the three commands above and open **http://127.0.0.1:8000/docs**.
2. `POST /auth/login` → click **Authorize** (top right) → username `demo@example.com`, password `demo12345`.
3. `GET /assignments` → the seeded list shows each status: `overdue`, `due_soon`, `pending`, `completed`.
4. `POST /reminders/run` → reminders are created: one overdue, and 72h / 24h / 3h ones. Run it again → empty list (each reminder is sent only once).
5. `GET /reminders` → your reminder inbox.
6. `PATCH /assignments/{id}` with `{"completed": true}` on the overdue one → it stops generating reminders.
7. `GET /reports/weekly.pdf` → download the weekly report.
8. Try `GET /assignments` after clicking **Logout** in the Authorize dialog → `401`.

You can also register your own account with `POST /auth/register`.

## How the reminder job works

- A background scheduler (APScheduler) runs `scheduled_scan` every `SCAN_INTERVAL_MINUTES` (default 15).
- For each unfinished assignment it finds the tightest window it has entered (`REMINDER_WINDOWS_HOURS`, default 72/24/3 hours), or `overdue`.
- A unique constraint on `(assignment_id, kind)` makes the job idempotent: running it twice never double-sends.
- Reminders are stored in the database (your inbox). If `SMTP_HOST` is set, they are also emailed.
- All times are stored in UTC. Send `due_at` as an ISO datetime, e.g. `2026-11-03T23:59:00+02:00`. A value without a timezone is treated as UTC.

## API summary

| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/register` | 201, 409 if email exists, 422 on weak password |
| POST | `/auth/login` | form fields `username` (email) + `password`; returns a bearer token |
| GET | `/auth/me` | current user |
| POST/GET | `/assignments` | create (201) / list, filter with `?status=` and `?course=` |
| GET/PATCH/DELETE | `/assignments/{id}` | 404 for other users' rows; PATCH `completed: true/false` |
| GET | `/reminders` | your reminder inbox |
| POST | `/reminders/run` | run the scan now for your assignments |
| GET | `/reports/weekly.pdf` | weekly PDF report |

## Scope

- **Core features (5):** accounts, assignment tracking, status view, automatic reminders, weekly PDF.
- **Non-goal:** no web or mobile front end, and no syncing with real course platforms (Moodle, Classroom). Assignments are entered through the API.

## Future ideas

- Pull deadlines from a calendar (.ics) file
- Weekly PDF delivered by email on a schedule
- Simple front-end page
- Cache the report for repeated requests

## Security notes

- Passwords are hashed with PBKDF2-SHA256 and a per-user salt; they are never returned or logged.
- `.env`, databases and generated files are in `.gitignore`.
- The demo user is seed data only. Do not reuse the demo password anywhere.
