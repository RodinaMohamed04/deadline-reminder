from datetime import datetime, timedelta, timezone

from conftest import make_user


def iso(hours: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def new_assignment(client, auth, hours=48, **extra):
    body = {"course": "Algorithms", "title": "PS5", "due_at": iso(hours), **extra}
    return client.post("/assignments", json=body, headers=auth)


# ---------- auth ----------
def test_register_duplicate_and_validation(client):
    ok = client.post("/auth/register", json={"email": "x@example.com", "name": "X", "password": "password123"})
    assert ok.status_code == 201 and "password" not in ok.text
    dup = client.post("/auth/register", json={"email": "X@example.com", "name": "X", "password": "password123"})
    assert dup.status_code == 409
    weak = client.post("/auth/register", json={"email": "y@example.com", "name": "Y", "password": "short"})
    assert weak.status_code == 422


def test_login_wrong_password(client):
    make_user(client)
    r = client.post("/auth/login", data={"username": "a@example.com", "password": "nope-nope-nope"})
    assert r.status_code == 401


def test_protected_routes_need_token(client):
    assert client.get("/assignments").status_code == 401
    assert client.get("/reports/weekly.pdf").status_code == 401
    assert client.get("/reminders").status_code == 401
    bad = {"Authorization": "Bearer not.a.token"}
    assert client.get("/assignments", headers=bad).status_code == 401


# ---------- assignments ----------
def test_assignment_crud_and_status(client, auth):
    r = new_assignment(client, auth, hours=48)
    assert r.status_code == 201
    a = r.json()
    assert a["status"] == "pending" and 47 < a["hours_left"] <= 48

    assert client.patch(f"/assignments/{a['id']}", json={"completed": True}, headers=auth).json()["status"] == "completed"
    assert client.patch(f"/assignments/{a['id']}", json={"completed": False}, headers=auth).json()["status"] == "pending"

    assert client.delete(f"/assignments/{a['id']}", headers=auth).status_code == 204
    assert client.get(f"/assignments/{a['id']}", headers=auth).status_code == 404


def test_status_filter_and_validation(client, auth):
    new_assignment(client, auth, hours=-5)
    new_assignment(client, auth, hours=10)
    new_assignment(client, auth, hours=100)
    assert [a["status"] for a in client.get("/assignments?status=overdue", headers=auth).json()] == ["overdue"]
    assert len(client.get("/assignments", headers=auth).json()) == 3
    assert client.get("/assignments?status=bogus", headers=auth).status_code == 422
    bad = client.post("/assignments", json={"course": "", "title": "x", "due_at": "not-a-date"}, headers=auth)
    assert bad.status_code == 422


def test_users_cannot_see_each_others_assignments(client, auth):
    a = new_assignment(client, auth).json()
    other = make_user(client, "b@example.com")
    assert client.get(f"/assignments/{a['id']}", headers=other).status_code == 404
    assert client.delete(f"/assignments/{a['id']}", headers=other).status_code == 404
    assert client.get("/assignments", headers=other).json() == []


# ---------- reminder job ----------
def test_reminder_scan_is_idempotent_and_picks_tightest_window(client, auth):
    new_assignment(client, auth, hours=2)  # 3h window
    new_assignment(client, auth, hours=200)  # too far away, no reminder
    first = client.post("/reminders/run", headers=auth).json()
    assert [r["kind"] for r in first] == ["3h"]
    assert client.post("/reminders/run", headers=auth).json() == []  # nothing new the second time
    assert len(client.get("/reminders", headers=auth).json()) == 1


def test_overdue_reminder_and_completed_is_skipped(client, auth):
    late = new_assignment(client, auth, hours=-3).json()
    done = new_assignment(client, auth, hours=-3).json()
    client.patch(f"/assignments/{done['id']}", json={"completed": True}, headers=auth)
    kinds = [(r["assignment_id"], r["kind"]) for r in client.post("/reminders/run", headers=auth).json()]
    assert kinds == [(late["id"], "overdue")]


def test_reminder_escalates_as_deadline_nears(client, auth):
    from app.database import SessionLocal
    from app.models import utcnow
    from app.reminders import run_scan

    new_assignment(client, auth, hours=60)
    db = SessionLocal()
    now = utcnow()
    kinds = []
    for hours_ahead in (0, 40, 70):  # 60h left -> 20h left -> -10h
        kinds += [r.kind for r in run_scan(db, now=now + timedelta(hours=hours_ahead))]
    db.close()
    assert kinds == ["72h", "24h", "overdue"]


# ---------- PDF ----------
def test_weekly_pdf(client, auth):
    new_assignment(client, auth, hours=-5)
    new_assignment(client, auth, hours=30)
    r = client.get("/reports/weekly.pdf", headers=auth)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and len(r.content) > 1000
