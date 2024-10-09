import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.main import app
from app.db import get_session

# Create SQLite database for testing
SQLITE_URL = "sqlite:///./test.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

# Override the get_session function to use the test SQLite database
def override_get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module")
def client():
    # Set up a FastAPI TestClient and initialize the database
    with TestClient(app) as client:
        SQLModel.metadata.create_all(engine)
        yield client
        SQLModel.metadata.drop_all(engine)

def test_signup(client):
    # Test that a new user can be created successfully
    response = client.post(
        "/signup",
        json={"username": "testuser", "email": "testuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "hashed_password" not in data

    # Test that the same user cannot be created again
    response = client.post(
        "/signup",
        json={"username": "testuser", "email": "testuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login(client):
    # First, ensure the user is created by calling the signup
    client.post("/signup", json={
        "username": "testuser",
        "email": "testlogin@example.com",
        "password": "password123"
    })

    # Use the email as the username in the headers
    response = client.post("/login", data={
        "username": "testlogin@example.com",  # Email as username
        "password": "password123"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()  # Ensure access_token is in the response

def test_protected_route(client):
    # First, log in to get a token
    response = client.post("/login", data={
        "username": "testlogin@example.com",  # Email as username
        "password": "password123"
    })
    
    # Check if the access_token is available
    assert response.status_code == 200
    access_token = response.json().get("access_token")
    assert access_token is not None, "Access token is missing"

    # Access the protected route with the access token
    response = client.get("/protected-route", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()["msg"] == "You have access"


def test_refresh_token(client):
    # First, log in to get a token using the correct email
    response = client.post("/login", data={
        "username": "testlogin@example.com",  # Use the same email as the test_login test
        "password": "password123"
    })

    assert response.status_code == 200
    access_token = response.json().get("access_token")
    assert access_token is not None, "Access token is missing"

    # Use the token to refresh
    response = client.post("/token/refresh", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert "access_token" in response.json()  # Ensure access_token is in the response
