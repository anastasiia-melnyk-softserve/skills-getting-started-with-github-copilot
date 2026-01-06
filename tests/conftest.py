"""Pytest configuration and fixtures for FastAPI tests"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join the school basketball team and compete in inter-school tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Swimming Club": {
            "description": "Improve your swimming techniques and participate in competitions",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["sarah@mergington.edu", "ryan@mergington.edu"]
        },
        "Drama Club": {
            "description": "Explore acting, directing, and stagecraft through theatrical productions",
            "schedule": "Thursdays, 3:30 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["emily@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Express creativity through painting, drawing, and sculpture",
            "schedule": "Wednesdays, 3:00 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["ava@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop critical thinking and public speaking skills through competitive debates",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["william@mergington.edu", "isabella@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Prepare for science competitions and conduct exciting experiments",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["ethan@mergington.edu"]
        },
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)
