import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static index.html"""
        client = TestClient(app)
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify activities exist
        assert "Chess Club" in data
        assert "Basketball Team" in data
        assert "Swimming Club" in data
    
    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_participant_data(self, client):
        """Test that participant data is accurate"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert chess_club["max_participants"] == 12


class TestSignupForActivity:
    """Test the signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup is rejected"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for two activities
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Basketball Team"]["participants"]
    
    def test_signup_fills_activity(self, client):
        """Test signing up for activities with limited spots"""
        # Art Studio has max 18 participants with 1 already signed up
        response = client.get("/activities")
        art_studio = response.json()["Art Studio"]
        initial_count = len(art_studio["participants"])
        
        # Sign up a new student
        response = client.post(
            "/activities/Art Studio/signup?email=newartist@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()["Art Studio"]["participants"])
        assert new_count == initial_count + 1
