"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities include Chess Club and Programming Class"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_count(self):
        """Test that we have exactly 9 activities"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) == 9


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=testuser@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up testuser@mergington.edu for Chess Club" in response.json()["message"]

    def test_signup_duplicate_student(self):
        """Test that signing up twice returns 400 error"""
        # Sign up first time
        response1 = client.post(
            "/activities/Programming%20Class/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200

        # Try to sign up again
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that a signed-up student appears in the activities list"""
        email = "verify@mergington.edu"
        
        # Sign up
        response1 = client.post(
            f"/activities/Art%20Studio/signup?email={email}"
        )
        assert response1.status_code == 200

        # Verify participant is in the list
        response2 = client.get("/activities")
        activities = response2.json()
        assert email in activities["Art Studio"]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_delete_existing_participant(self):
        """Test removing an existing participant"""
        email = "remove_me@mergington.edu"
        
        # First, sign up the participant
        client.post(
            f"/activities/Drama%20Club/signup?email={email}"
        )

        # Then delete them
        response = client.delete(
            f"/activities/Drama%20Club/participants/{email}"
        )
        assert response.status_code == 200
        assert f"Removed {email} from Drama Club" in response.json()["message"]

    def test_delete_nonexistent_participant(self):
        """Test deleting a non-existent participant returns 404"""
        response = client.delete(
            "/activities/Basketball%20Team/participants/nobody@mergington.edu"
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_delete_from_nonexistent_activity(self):
        """Test deleting from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake%20Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_delete_removes_participant_from_list(self):
        """Test that deleted participant is removed from the list"""
        email = "verify_delete@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/Swimming%20Club/signup?email={email}"
        )

        # Delete
        response1 = client.delete(
            f"/activities/Swimming%20Club/participants/{email}"
        )
        assert response1.status_code == 200

        # Verify participant is no longer in the list
        response2 = client.get("/activities")
        activities = response2.json()
        assert email not in activities["Swimming Club"]["participants"]

    def test_delete_nonexistent_activity(self):
        """Test that deleting from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participants/test@mergington.edu"
        )
        assert response.status_code == 404


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that the root path redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_signup_with_special_characters_in_email(self):
        """Test signup with email containing special characters"""
        response = client.post(
            "/activities/Science%20Club/signup?email=test%2Bsub@mergington.edu"
        )
        assert response.status_code == 200

    def test_activity_name_with_spaces(self):
        """Test that activity names with spaces work correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify we can access activities with spaces in names
        assert "Basketball Team" in activities
        assert "Programming Class" in activities
        assert "Art Studio" in activities

    def test_max_participants_field_exists(self):
        """Test that max_participants field is present and is an integer"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0
