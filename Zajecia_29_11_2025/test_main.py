import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importujemy app i Base z naszego pliku main.py
from main import app, get_db, Base

# --- Konfiguracja bazy testowej (In-Memory SQLite) ---
# Używamy StaticPool, aby baza w pamięci była współdzielona między wątkami
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixture bazy danych - tworzy tabele przed testem i usuwa po teście
@pytest.fixture(name="session")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Fixture klienta API, nadpisuje zależność get_db
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


# --- TESTY DLA MOVIES ---

def test_create_movie(client):
    response = client.post("/movies", json={
        "movie_id": 1,
        "title": "Test Movie",
        "genres": ["Action", "Comedy"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Movie"
    assert data["genres"] == ["Action", "Comedy"]
    assert data["movie_id"] == 1


def test_get_movie(client):
    # Najpierw dodajemy film
    client.post("/movies", json={"movie_id": 2, "title": "Get Me", "genres": ["Drama"]})

    # Pobieramy
    response = client.get("/movies/2")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


def test_get_movie_not_found(client):
    response = client.get("/movies/999")
    assert response.status_code == 404


def test_update_movie(client):
    client.post("/movies", json={"movie_id": 3, "title": "Old Title", "genres": ["Drama"]})

    response = client.put("/movies/3", json={"title": "New Title", "genres": ["Horror"]})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["genres"] == ["Horror"]


def test_delete_movie(client):
    client.post("/movies", json={"movie_id": 4, "title": "Delete Me", "genres": []})

    response = client.delete("/movies/4")
    assert response.status_code == 204

    # Sprawdź czy zniknął
    response = client.get("/movies/4")
    assert response.status_code == 404


# --- TESTY DLA LINKS ---

def test_create_link(client):
    response = client.post("/links", json={
        "movieId": 1,
        "imdbId": 123456,
        "tmdbId": 789
    })
    assert response.status_code == 201
    assert response.json()["imdbId"] == 123456


def test_get_link(client):
    client.post("/links", json={"movieId": 2, "imdbId": 111, "tmdbId": 222})
    response = client.get("/links/2")
    assert response.status_code == 200
    assert response.json()["tmdbId"] == 222


def test_update_link(client):
    client.post("/links", json={"movieId": 3, "imdbId": 111})
    response = client.put("/links/3", json={"tmdbId": 999})
    assert response.status_code == 200
    assert response.json()["tmdbId"] == 999
    assert response.json()["imdbId"] == 111  # Nie powinno się zmienić


def test_delete_link(client):
    client.post("/links", json={"movieId": 4, "imdbId": 444})
    response = client.delete("/links/4")
    assert response.status_code == 204
    assert client.get("/links/4").status_code == 404


# --- TESTY DLA RATINGS ---

def test_create_rating(client):
    # Wymaga utworzenia filmu, aby klucz obcy zadziałał (jeśli SQLite wymusza FK, tu może przejść bez filmu w zależności od configu, ale dodajmy dla pewności)
    client.post("/movies", json={"movie_id": 100, "title": "Rated Movie", "genres": []})

    response = client.post("/ratings", json={
        "userId": 1,
        "movieId": 100,
        "rating": 4.5
    })
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 4.5
    assert "id" in data  # ID powinno być auto-generowane


def test_get_rating(client):
    client.post("/movies", json={"movie_id": 101, "title": "M", "genres": []})
    create_res = client.post("/ratings", json={"userId": 1, "movieId": 101, "rating": 5.0})
    rating_id = create_res.json()["id"]

    response = client.get(f"/ratings/{rating_id}")
    assert response.status_code == 200
    assert response.json()["rating"] == 5.0


def test_update_rating(client):
    client.post("/movies", json={"movie_id": 102, "title": "M", "genres": []})
    create_res = client.post("/ratings", json={"userId": 1, "movieId": 102, "rating": 3.0})
    rating_id = create_res.json()["id"]

    response = client.put(f"/ratings/{rating_id}", json={"rating": 1.0})
    assert response.status_code == 200
    assert response.json()["rating"] == 1.0


def test_delete_rating(client):
    client.post("/movies", json={"movie_id": 103, "title": "M", "genres": []})
    create_res = client.post("/ratings", json={"userId": 1, "movieId": 103, "rating": 3.0})
    rating_id = create_res.json()["id"]

    response = client.delete(f"/ratings/{rating_id}")
    assert response.status_code == 204
    assert client.get(f"/ratings/{rating_id}").status_code == 404


# --- TESTY DLA TAGS ---

def test_create_tag(client):
    client.post("/movies", json={"movie_id": 200, "title": "Tagged Movie", "genres": []})

    response = client.post("/tags", json={
        "userId": 1,
        "movieId": 200,
        "tag": "funny"
    })
    assert response.status_code == 201
    assert response.json()["tag"] == "funny"


def test_get_tag(client):
    client.post("/movies", json={"movie_id": 201, "title": "M", "genres": []})
    create_res = client.post("/tags", json={"userId": 1, "movieId": 201, "tag": "dark"})
    tag_id = create_res.json()["id"]

    response = client.get(f"/tags/{tag_id}")
    assert response.status_code == 200
    assert response.json()["tag"] == "dark"


def test_update_tag(client):
    client.post("/movies", json={"movie_id": 202, "title": "M", "genres": []})
    create_res = client.post("/tags", json={"userId": 1, "movieId": 202, "tag": "boring"})
    tag_id = create_res.json()["id"]

    response = client.put(f"/tags/{tag_id}", json={"tag": "exciting"})
    assert response.status_code == 200
    assert response.json()["tag"] == "exciting"


def test_delete_tag(client):
    client.post("/movies", json={"movie_id": 203, "title": "M", "genres": []})
    create_res = client.post("/tags", json={"userId": 1, "movieId": 203, "tag": "delete_me"})
    tag_id = create_res.json()["id"]

    response = client.delete(f"/tags/{tag_id}")
    assert response.status_code == 204
    assert client.get(f"/tags/{tag_id}").status_code == 404

