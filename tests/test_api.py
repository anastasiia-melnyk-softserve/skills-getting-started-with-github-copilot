"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestActivitiesAPI:
    """Test suite for activities API endpoints"""

    def test_root_redirect(self):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_structure(self):
        """Test that activities have the expected structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Test a specific activity exists and has correct structure
        assert "Chess Club" in activities
        chess_club = activities["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) >= 0


class TestSignupEndpoint:
    """Test suite for activity signup functionality"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]

    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self):
        """Test that duplicate signup returns 400 error"""
        email = "duplicate@mergington.edu"
        activity = "Programming Class"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]

    def test_signup_updates_participant_list(self):
        """Test that signup actually adds participant to the list"""
        email = "newparticipant@mergington.edu"
        activity = "Art Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        initial_count = len(initial_participants)
        
        # Sign up new participant
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Check participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert len(updated_participants) == initial_count + 1
        assert email in updated_participants


class TestUnregisterEndpoint:
    """Test suite for activity unregister functionality"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        activity = "Drama Society"
        
        # First sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Then unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]
        assert email in result["message"]
        assert activity in result["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"

    def test_unregister_not_registered_participant(self):
        """Test unregister for non-registered participant returns 400"""
        response = client.delete(
            "/activities/Math Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from the list"""
        email = "removeme@mergington.edu"
        activity = "Science Olympiad"
        
        # Sign up participant
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant is in the list
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert email in participants
        initial_count = len(participants)
        
        # Unregister participant
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify participant is removed
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert email not in updated_participants
        assert len(updated_participants) == initial_count - 1


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""

    def test_signup_with_special_characters_in_email(self):
        """Test signup with special characters in email"""
        email = "test+special@mergington.edu"
        activity = "Basketball Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

    def test_signup_with_spaces_in_activity_name(self):
        """Test signup with activity names containing spaces"""
        email = "spaces@mergington.edu"
        activity = "Soccer Team"  # Contains space
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

    def test_activity_name_encoding(self):
        """Test that activity names are properly URL encoded"""
        # This tests the client's ability to handle URL encoding
        email = "encoding@mergington.edu"
        
        # Use requests directly to test URL encoding
        import urllib.parse
        encoded_activity = urllib.parse.quote("Soccer Team")
        
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
        assert response.status_code == 200


class TestDataIntegrity:
    """Test suite for data integrity and consistency"""

    def test_max_participants_not_exceeded(self):
        """Test that activities maintain their max participant limits"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participants_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert participants_count <= max_participants, f"{activity_name} has too many participants"

    def test_participants_are_unique(self):
        """Test that each activity has unique participants"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            unique_participants = set(participants)
            assert len(participants) == len(unique_participants), f"{activity_name} has duplicate participants"

    def test_all_required_activities_exist(self):
        """Test that all expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Soccer Team", "Basketball Club", "Art Club",
            "Drama Society", "Math Club", "Science Olympiad"
        ]
        
        for expected_activity in expected_activities:
            assert expected_activity in activities, f"Missing activity: {expected_activity}"


@pytest.fixture(autouse=True)
def reset_test_data():
    """Reset test data after each test to ensure test isolation"""
    # This fixture runs before and after each test
    yield
    # Cleanup: Remove any test participants that were added
    test_emails = [
        "test@mergington.edu",
        "duplicate@mergington.edu", 
        "newparticipant@mergington.edu",
        "unregister@mergington.edu",
        "removeme@mergington.edu",
        "test+special@mergington.edu",
        "spaces@mergington.edu",
        "encoding@mergington.edu"
    ]
    
    # Get current activities
    response = client.get("/activities")
    if response.status_code == 200:
        activities = response.json()
        
        # Remove test emails from all activities
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            for email in test_emails:
                if email in participants:
                    # Remove the test participant
                    client.delete(f"/activities/{activity_name}/unregister?email={email}")