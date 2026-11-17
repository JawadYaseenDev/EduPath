import os
import tempfile

import pytest

_db_file = os.path.join(tempfile.mkdtemp(prefix="unirah-test-"), "test.db")
os.environ["UNIRAH_DATABASE_URL"] = f"sqlite:///{_db_file}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    """Register a fresh student and return auth headers."""
    import uuid

    email = f"student-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/v1/auth/register", json={"email": email, "password": "Strong-pass-1",
                                               "full_name": "Test Student",
                                               "accept_terms": True})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
