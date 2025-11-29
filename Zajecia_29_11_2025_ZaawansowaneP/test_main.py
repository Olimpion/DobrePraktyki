import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app, get_db, Base, get_password_hash, UserModel

# --- Konfiguracja bazy testowej (In-Memory SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="session")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed Admin User for tests
    admin_user = UserModel(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role="ROLE_ADMIN"
    )
    db.add(admin_user)

    # Seed Regular User for tests
    regular_user = UserModel(
        username="user",
        hashed_password=get_password_hash("user123"),
        role="ROLE_USER"
    )
    db.add(regular_user)

    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- POMOCNICY AUTORYZACJI ---

def get_auth_headers(client, username, password):
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="admin_headers")
def admin_headers_fixture(client):
    return get_auth_headers(client, "admin", "admin123")


@pytest.fixture(name="user_headers")
def user_headers_fixture(client):
    return get_auth_headers(client, "user", "user123")


# --- TESTY AUTH ---

def test_login_success(client):
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_failure(client):
    response = client.post("/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401


def test_user_details(client, admin_headers):
    response = client.get("/user_details", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"] == "ROLE_ADMIN"


def test_user_details_no_token(client):
    response = client.get("/user_details")
    assert response.status_code == 401


# --- TESTY TWORZENIA UŻYTKOWNIKÓW (RBAC) ---

def test_create_user_as_admin(client, admin_headers):
    response = client.post("/users", json={
        "username": "newuser",
        "password": "password",
        "role": "ROLE_USER"
    }, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"


def test_create_user_as_normal_user_forbidden(client, user_headers):
    response = client.post("/users", json={
        "username": "hacker",
        "password": "password",
        "role": "ROLE_ADMIN"
    }, headers=user_headers)
    assert response.status_code == 403  # Forbidden


# --- TESTY DLA MOVIES (z Auth) ---

def test_create_movie(client, admin_headers):
    response = client.post("/movies", json={
        "movie_id": 1,
        "title": "Test Movie",
        "genres": ["Action", "Comedy"]
    }, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Movie"


def test_get_movie_without_auth(client):
    response = client.get("/movies/1")
    assert response.status_code == 401


def test_get_movie(client, user_headers):
    # Setup by admin
    admin_auth = get_auth_headers(client, "admin", "admin123")
    client.post("/movies", json={"movie_id": 2, "title": "Get Me", "genres": ["Drama"]}, headers=admin_auth)

    # Read by user
    response = client.get("/movies/2", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


def test_update_movie(client, admin_headers):
    client.post("/movies", json={"movie_id": 3, "title": "Old Title", "genres": ["Drama"]}, headers=admin_headers)
    response = client.put("/movies/3", json={"title": "New Title"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_delete_movie(client, admin_headers):
    client.post("/movies", json={"movie_id": 4, "title": "Delete Me", "genres": []}, headers=admin_headers)
    response = client.delete("/movies/4", headers=admin_headers)
    assert response.status_code == 204
    assert client.get("/movies/4", headers=admin_headers).status_code == 404


# --- TESTY DLA LINKS ---

def test_create_link(client, admin_headers):
    response = client.post("/links", json={
        "movieId": 1,
        "imdbId": 123456,
        "tmdbId": 789
    }, headers=admin_headers)
    assert response.status_code == 201


# --- TESTY DLA RATINGS ---

def test_create_rating(client, user_headers):
    # User can create ratings
    response = client.post("/ratings", json={
        "userId": 1,
        "movieId": 100,
        "rating": 4.5
    }, headers=user_headers)
    assert response.status_code == 201
    assert response.json()["rating"] == 4.5


# --- TESTY DLA TAGS ---

def test_create_tag(client, user_headers):
    response = client.post("/tags", json={
        "userId": 1,
        "movieId": 200,
        "tag": "funny"
    }, headers=user_headers)
    assert response.status_code == 201
    assert response.json()["tag"] == "funny"