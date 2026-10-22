import os
import sys
import tempfile
from pathlib import Path

# Must be set before the app is imported: isolated DB, no background scheduler, no SMTP
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["ENABLE_SCHEDULER"] = "0"
os.environ["SMTP_HOST"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-32b"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # lifespan creates the tables
        yield c


def make_user(client, email="a@example.com", password="password123"):
    client.post("/auth/register", json={"email": email, "name": "Test", "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return make_user(client)
