from fastapi import FastAPI, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
import csv
import os
from typing import List, Optional

# --- 1. Konfiguracja SQLAlchemy ---
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Tworzymy plik bazy danych SQLite w bieżącym katalogu
SQLALCHEMY_DATABASE_URL = "sqlite:///./movies.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# --- 2. Modele Bazy Danych (SQLAlchemy) ---

class MovieModel(Base):
    __tablename__ = "movies"

    movie_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    # Bazy SQL nie przechowują list natywnie w prosty sposób,
    # więc przechowamy gatunki jako tekst rozdzielony "|" (jak w CSV)
    genres = Column(String)


class LinkModel(Base):
    __tablename__ = "links"

    movieId = Column(Integer, primary_key=True, index=True)  # Zakładamy, że movieId jest unikalne w links
    imdbId = Column(Integer)
    tmdbId = Column(Integer, nullable=True)


class RatingModel(Base):
    __tablename__ = "ratings"

    # Dodajemy sztuczny klucz główny (id), bo SQLAlchemy go wymaga,
    # a CSV go nie ma (kluczem jest para userId + movieId)
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movie_id"))
    rating = Column(Float)
    timestamp = Column(DateTime)


class TagModel(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movie_id"))
    tag = Column(String)
    timestamp = Column(DateTime)


# --- 3. Schematy Pydantic (DTO) ---

class MovieSchema(BaseModel):
    movie_id: int
    title: str
    genres: List[str]

    model_config = ConfigDict(from_attributes=True)

    # Validator konwertuje string z bazy "Action|Comedy" na listę ["Action", "Comedy"]
    @field_validator('genres', mode='before')
    @classmethod
    def split_genres(cls, v):
        if isinstance(v, str):
            return v.split('|') if v else []
        return v


class LinkSchema(BaseModel):
    movieId: int
    imdbId: int
    tmdbId: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RatingSchema(BaseModel):
    userId: int
    movieId: int
    rating: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class TagSchema(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- 4. Funkcja Inicjalizująca (Ładowanie CSV do DB) ---

def init_db():
    # Tworzymy tabele
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Sprawdzamy czy baza jest pusta, żeby nie dublować danych przy restarcie
    if db.query(MovieModel).first():
        print("Baza danych już zawiera dane. Pomijam import CSV.")
        db.close()
        return

    print("Rozpoczynam import danych z CSV do bazy danych...")

    # -- Import Movies --
    if os.path.exists("Database/movies.csv"):
        with open("Database/movies.csv", mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            movies_to_add = []
            for row in reader:
                try:
                    movies_to_add.append(MovieModel(
                        movie_id=int(row['movieId']),
                        title=row['title'],
                        genres=row['genres']  # Zapisujemy jako string
                    ))
                except Exception as e:
                    print(f"Error parsing movie: {e}")
            db.add_all(movies_to_add)
            db.commit()
            print(f"Zaimportowano {len(movies_to_add)} filmów.")

    # -- Import Links --
    if os.path.exists("Database/links.csv"):
        with open("Database/links.csv", mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            links_to_add = []
            for row in reader:
                try:
                    tmdb = int(row['tmdbId']) if row.get('tmdbId') and row['tmdbId'].strip() else None
                    links_to_add.append(LinkModel(
                        movieId=int(row['movieId']),
                        imdbId=int(row['imdbId']),
                        tmdbId=tmdb
                    ))
                except Exception as e:
                    print(f"Error parsing link: {e}")
            db.add_all(links_to_add)
            db.commit()
            print(f"Zaimportowano {len(links_to_add)} linków.")

    # -- Import Ratings --
    # Uwaga: Tabela ratings może być duża, import może chwilę potrwać
    if os.path.exists("Database/ratings.csv"):
        with open("Database/ratings.csv", mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ratings_to_add = []
            for row in reader:
                try:
                    ratings_to_add.append(RatingModel(
                        userId=int(row['userId']),
                        movieId=int(row['movieId']),
                        rating=float(row['rating']),
                        timestamp=datetime.fromtimestamp(int(float(row['timestamp'])))
                    ))
                except Exception as e:
                    print(f"Error parsing rating: {e}")
            # Bulk insert w paczkach lub całość (dla prostoty całość)
            db.add_all(ratings_to_add)
            db.commit()
            print(f"Zaimportowano {len(ratings_to_add)} ocen.")

    # -- Import Tags --
    if os.path.exists("Database/tags.csv"):
        with open("Database/tags.csv", mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            tags_to_add = []
            for row in reader:
                try:
                    tags_to_add.append(TagModel(
                        userId=int(row['userId']),
                        movieId=int(row['movieId']),
                        tag=row['tag'],
                        timestamp=datetime.fromtimestamp(int(float(row['timestamp'])))
                    ))
                except Exception as e:
                    print(f"Error parsing tag: {e}")
            db.add_all(tags_to_add)
            db.commit()
            print(f"Zaimportowano {len(tags_to_add)} tagów.")

    db.close()


# --- 5. Aplikacja FastAPI ---

# Uruchomienie importu przy starcie (można też użyć lifespan w nowszym FastAPI)
init_db()

app = FastAPI()


# Dependency: Uzyskiwanie sesji bazy danych dla każdego żądania
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "World", "Info": "Data is now served from SQLite database"}


# Dodano parametry 'skip' i 'limit' dla paginacji,
# ponieważ baza danych może zawierać tysiące rekordów.

@app.get("/movies", response_model=List[MovieSchema])
def get_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = db.query(MovieModel).offset(skip).limit(limit).all()
    return movies


@app.get("/links", response_model=List[LinkSchema])
def get_links(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    links = db.query(LinkModel).offset(skip).limit(limit).all()
    return links


@app.get("/ratings", response_model=List[RatingSchema])
def get_ratings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ratings = db.query(RatingModel).offset(skip).limit(limit).all()
    return ratings


@app.get("/tags", response_model=List[TagSchema])
def get_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tags = db.query(TagModel).offset(skip).limit(limit).all()
    return tags