"""
Test suite for the High School Management System API.

- Uses pytest and FastAPI TestClient
- Follows Arrange-Act-Assert (AAA) pattern
- Ensures data isolation between tests
- To run: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
import sys
from pathlib import Path

# Arrange: Import app and activities from src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from app import app, activities

# Store original activities data for isolation
ORIGINAL_ACTIVITIES = deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before and after each test."""
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))

@pytest.fixture
def client():
    """Provide a TestClient for making requests to the app."""
    return TestClient(app)

@pytest.fixture
def sample_email():
    return "test.student@mergington.edu"

class TestGetActivities:
    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        # ...nothing to arrange, state is reset
        # Act
        response = client.get("/activities")
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_contains_required_fields(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.get("/activities")
        # Assert
        data = response.json()
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_returns_correct_initial_state(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.get("/activities")
        # Assert
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2

class TestSignupForActivity:
    def test_signup_success(self, client, sample_email):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.post("/activities/Chess Club/signup", params={"email": sample_email})
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert sample_email in response.json()["message"]

    def test_signup_adds_participant_to_activity(self, client, sample_email):
        # Arrange
        # ...nothing to arrange
        # Act
        client.post("/activities/Chess Club/signup", params={"email": sample_email})
        response = client.get("/activities")
        # Assert
        participants = response.json()["Chess Club"]["participants"]
        assert sample_email in participants

    def test_signup_nonexistent_activity_returns_404(self, client, sample_email):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.post("/activities/Nonexistent Club/signup", params={"email": sample_email})
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up_returns_400(self, client):
        # Arrange
        email = "michael@mergington.edu"
        # Act
        response = client.post("/activities/Chess Club/signup", params={"email": email})
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

class TestRemoveParticipant:
    def test_remove_participant_success(self, client):
        # Arrange
        email = "michael@mergington.edu"
        # Act
        response = client.delete(f"/activities/Chess Club/participants/{email}")
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email in response.json()["message"]

    def test_remove_participant_actually_removes(self, client):
        # Arrange
        email = "michael@mergington.edu"
        # Act
        client.delete(f"/activities/Chess Club/participants/{email}")
        response = client.get("/activities")
        # Assert
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants

    def test_remove_participant_decreases_count(self, client):
        # Arrange
        email = "michael@mergington.edu"
        response_before = client.get("/activities")
        initial_count = len(response_before.json()["Chess Club"]["participants"])
        # Act
        client.delete(f"/activities/Chess Club/participants/{email}")
        response_after = client.get("/activities")
        updated_count = len(response_after.json()["Chess Club"]["participants"])
        # Assert
        assert updated_count == initial_count - 1

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.delete("/activities/Nonexistent Club/participants/test@example.com")
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonexistent_participant_returns_404(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.delete("/activities/Chess Club/participants/nonexistent@example.com")
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

class TestRoot:
    def test_root_redirects_to_static_index(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.get("/", follow_redirects=False)
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_root_redirect_with_follow(self, client):
        # Arrange
        # ...nothing to arrange
        # Act
        response = client.get("/", follow_redirects=True)
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

class TestIntegration:
    def test_signup_and_remove_workflow(self, client, sample_email):
        # Arrange
        activity_name = "Debate Club"
        # Act
        signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": sample_email})
        check_response = client.get("/activities")
        remove_response = client.delete(f"/activities/{activity_name}/participants/{sample_email}")
        final_response = client.get("/activities")
        # Assert
        assert signup_response.status_code == 200
        assert sample_email in check_response.json()[activity_name]["participants"]
        assert remove_response.status_code == 200
        assert sample_email not in final_response.json()[activity_name]["participants"]
