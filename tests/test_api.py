import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)
    yield
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)


@pytest.fixture
def client():
    # Arrange
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    expected_activity = "Chess Club"
    expected_description_prefix = "Learn"

    # Act
    response = client.get("/activities")

    # Assert
    payload = response.json()
    assert response.status_code == 200
    assert expected_activity in payload
    assert payload[expected_activity]["description"].startswith(expected_description_prefix)


def test_get_activities_returns_complete_activity_shape(client):
    # Arrange
    activity_name = "Chess Club"
    expected_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    activity = response.json()[activity_name]
    assert response.status_code == 200
    assert set(activity) == expected_keys
    assert isinstance(activity["participants"], list)


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    expected_message = f"Signed up {email} for {activity_name}"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == expected_message
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_for_activity_persists_in_catalog(client):
    # Arrange
    activity_name = "Chess Club"
    email = "catalogstudent@mergington.edu"

    # Act
    client.post(f"/activities/{activity_name}/signup", params={"email": email})
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert email in response.json()[activity_name]["participants"]


def test_signup_for_missing_activity_returns_not_found(client):
    # Arrange
    activity_name = "Missing Club"
    email = "student@mergington.edu"
    expected_detail = "Activity not found"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail


def test_signup_for_duplicate_email_returns_bad_request(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    expected_detail = "Student already signed up for this activity"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == expected_detail


def test_signup_for_full_activity_returns_bad_request(client):
    # Arrange
    activity_name = "Chess Club"
    activity = app_module.activities[activity_name]
    activity["participants"] = [
        f"participant{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    email = "waitlisted@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_without_email_returns_validation_error(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_from_activity_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    expected_message = f"Unregistered {email} from {activity_name}"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == expected_message
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_from_activity_persists_in_catalog(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert email not in response.json()[activity_name]["participants"]


def test_unregister_for_non_member_returns_bad_request(client):
    # Arrange
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    expected_detail = "Student is not registered for this activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == expected_detail


def test_unregister_for_missing_activity_returns_not_found(client):
    # Arrange
    activity_name = "Missing Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_without_email_returns_validation_error(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister")

    # Assert
    assert response.status_code == 422


def test_static_index_is_served(client):
    # Arrange
    expected_content_marker = "Mergington High School"

    # Act
    response = client.get("/static/index.html")

    # Assert
    assert response.status_code == 200
    assert expected_content_marker in response.text
