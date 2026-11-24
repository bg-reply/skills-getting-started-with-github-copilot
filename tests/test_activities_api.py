import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Fridays",
            "max_participants": 10,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_web_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_list_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Fridays",
            "max_participants": 10,
            "participants": ["existing@example.com"],
        }
    }


def test_signup_adds_participant(client):
    email = "new@example.com"

    response = client.post("/activities/Test%20Activity/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Test Activity"}
    assert client.get("/activities").json()["Test Activity"]["participants"] == [
        "existing@example.com",
        email,
    ]


def test_duplicate_signup_is_rejected(client):
    email = "existing@example.com"

    response = client.post("/activities/Test%20Activity/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert client.get("/activities").json()["Test Activity"]["participants"] == [email]


def test_unregister_removes_participant(client):
    email = "existing@example.com"
    app_module.activities["Test Activity"]["participants"].append("other@example.com")

    response = client.delete("/activities/Test%20Activity/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Test Activity"}
    assert client.get("/activities").json()["Test Activity"]["participants"] == ["other@example.com"]


def test_unregister_missing_participant_is_rejected(client):
    email = "missing@example.com"

    response = client.delete("/activities/Test%20Activity/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert client.get("/activities").json()["Test Activity"]["participants"] == ["existing@example.com"]


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_is_rejected(client, method):
    response = client.request(method, "/activities/Missing/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_or_unregister_requires_email(client, method):
    response = client.request(method, "/activities/Test%20Activity/signup")

    assert response.status_code == 422
    assert client.get("/activities").json()["Test Activity"]["participants"] == ["existing@example.com"]
