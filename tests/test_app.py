"""Tests for the High School Management System API"""
import pytest
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that the root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # We have 9 activities
        
        # Check some expected activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client):
        """Test that signing up with an already registered email returns 400"""
        # First signup
        response1 = client.post(
            "/activities/Swimming Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to signup again with the same email
        response2 = client.post(
            "/activities/Swimming Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_existing_participant(self, client):
        """Test that an existing participant cannot sign up again"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""
    
    def test_unregister_from_activity_success(self, client):
        """Test successful unregistration from an activity"""
        # First, signup a new student
        client.post(
            "/activities/Drama Club/signup",
            params={"email": "temp@mergington.edu"}
        )
        
        # Now unregister
        response = client.delete(
            "/activities/Drama Club/unregister",
            params={"email": "temp@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Unregistered temp@mergington.edu from Drama Club"
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "temp@mergington.edu" not in activities_data["Drama Club"]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistration from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a non-existent participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Participant not found in this activity"
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        # daniel@mergington.edu is already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "daniel@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify removal
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "daniel@mergington.edu" not in activities_data["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete user scenarios"""
    
    def test_complete_signup_and_unregister_flow(self, client):
        """Test a complete flow of signup and unregister"""
        email = "flow@mergington.edu"
        activity = "Art Studio"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        initial_count = len(initial_participants)
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify signup
        after_signup = client.get("/activities")
        after_signup_participants = after_signup.json()[activity]["participants"]
        assert len(after_signup_participants) == initial_count + 1
        assert email in after_signup_participants
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify unregistration
        after_unregister = client.get("/activities")
        after_unregister_participants = after_unregister.json()[activity]["participants"]
        assert len(after_unregister_participants) == initial_count
        assert email not in after_unregister_participants
    
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multi@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
