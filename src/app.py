"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
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
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# Load teachers from JSON file
def load_teachers():
    try:
        with open(os.path.join(Path(__file__).parent.parent, "teachers.json"), "r") as f:
            data = json.load(f)
            return {t["username"]: t["password"] for t in data.get("teachers", [])}
    except Exception as e:
        print(f"Error loading teachers: {e}")
        return {}

teachers_db = load_teachers()

# In-memory authenticated users (teacher username)
authenticated_users = set()


def is_teacher_authenticated(auth_header: str = Header(None)) -> bool:
    """Check if the provided authentication header contains a valid teacher username"""
    if not auth_header:
        return False
    # Auth header format: "Bearer <username>"
    try:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            username = parts[1]
            return username in authenticated_users
    except:
        pass
    return False


def get_authenticated_teacher(auth_header: str = Header(None)) -> str:
    """Extract and validate teacher username from auth header"""
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            username = parts[1]
            if username in authenticated_users:
                return username
    except:
        pass
    raise HTTPException(status_code=401, detail="Invalid or expired authentication")


@app.post("/auth/login")
def login(username: str = Query(...), password: str = Query(...)):
    """Authenticate a teacher and return a token"""
    if username not in teachers_db:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if teachers_db[username] != password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Add to authenticated users
    authenticated_users.add(username)
    return {"message": f"Logged in as {username}", "token": f"Bearer {username}"}


@app.post("/auth/logout")
def logout(auth_header: str = Header(None)):
    """Log out an authenticated teacher"""
    username = get_authenticated_teacher(auth_header)
    authenticated_users.discard(username)
    return {"message": f"Logged out {username}"}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, authorization: str = Header(None)):
    """Sign up a student for an activity (requires teacher authentication)"""
    # Check teacher authentication
    teacher = get_authenticated_teacher(authorization)
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}", "teacher": teacher}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, authorization: str = Header(None)):
    """Unregister a student from an activity (requires teacher authentication)"""
    # Check teacher authentication
    teacher = get_authenticated_teacher(authorization)
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}", "teacher": teacher}
