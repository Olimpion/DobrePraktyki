import os
import csv
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel, ConfigDict, field_validator

# --- Konfiguracja Bazy Danych ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./movies.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Modele SQLAlchemy (Tabele) ---

class MovieModel(Base):
    __tablename__ = "movies"
    movie_id = Column(Integer, primary_key=True, index=True) # Uwaga: w Twoim kodzie było movie_id
    title = Column(String)
    genres = Column(String)

class LinkModel(Base):
    __tablename__ = "links"
    movieId = Column(Integer, primary_key=True, index=True)
    imdbId = Column(Integer)
    tmdbId = Column(Integer, nullable=True)

class RatingModel(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movie_id"))
    rating = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TagModel(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movie_id"))
    tag = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Schematy Pydantic (DTO) ---

# 1. Movies Schemas
class MovieBase(BaseModel):
    title: str
    genres: List[str] # Przyjmujemy listę, w bazie zapiszemy jako string

class MovieCreate(MovieBase):
    movie_id: int # W tym zbiorze danych ID często podajemy ręcznie, ale można by to pominąć

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genres: Optional[List[str]] = None

class MovieSchema(MovieBase):
    movie_id: int
    model_config = ConfigDict(from_attributes=True)

    @field_validator('genres', mode='before')
    @classmethod
    def split_genres(cls, v):
        if isinstance(v, str):
            return v.split('|') if v else []
        return v

# 2. Links Schemas
class LinkBase(BaseModel):
    imdbId: int
    tmdbId: Optional[int] = None

class LinkCreate(LinkBase):
    movieId: int

class LinkUpdate(BaseModel):
    imdbId: Optional[int] = None
    tmdbId: Optional[int] = None

class LinkSchema(LinkBase):
    movieId: int
    model_config = ConfigDict(from_attributes=True)

# 3. Ratings Schemas
class RatingBase(BaseModel):
    userId: int
    movieId: int
    rating: float

class RatingCreate(RatingBase):
    pass # timestamp dodamy automatycznie

class RatingUpdate(BaseModel):
    rating: Optional[float] = None

class RatingSchema(RatingBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# 4. Tags Schemas
class TagBase(BaseModel):
    userId: int
    movieId: int
    tag: str

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    tag: Optional[str] = None

class TagSchema(TagBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

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


# --- ENDPOINTY CRUD ---

# === 1. MOVIES ===

@app.post("/movies", response_model=MovieSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.movie_id == movie.movie_id).first()
    if db_movie:
        raise HTTPException(status_code=400, detail="Movie with this ID already exists")

    # Konwersja listy gatunków na string rozdzielony |
    genres_str = "|".join(movie.genres) if movie.genres else ""

    new_movie = MovieModel(
        movie_id=movie.movie_id,
        title=movie.title,
        genres=genres_str
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@app.get("/movies/{movie_id}", response_model=MovieSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.movie_id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.put("/movies/{movie_id}", response_model=MovieSchema)
def update_movie(movie_id: int, movie_update: MovieUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.movie_id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie_update.title is not None:
        db_movie.title = movie_update.title
    if movie_update.genres is not None:
        db_movie.genres = "|".join(movie_update.genres)

    db.commit()
    db.refresh(db_movie)
    return db_movie


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.movie_id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(db_movie)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# === 2. LINKS ===

@app.post("/links", response_model=LinkSchema, status_code=status.HTTP_201_CREATED)
def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    if db.query(LinkModel).filter(LinkModel.movieId == link.movieId).first():
        raise HTTPException(status_code=400, detail="Link for this movie already exists")

    new_link = LinkModel(**link.model_dump())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@app.get("/links/{movieId}", response_model=LinkSchema)
def get_link(movieId: int, db: Session = Depends(get_db)):
    link = db.query(LinkModel).filter(LinkModel.movieId == movieId).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@app.put("/links/{movieId}", response_model=LinkSchema)
def update_link(movieId: int, link_update: LinkUpdate, db: Session = Depends(get_db)):
    db_link = db.query(LinkModel).filter(LinkModel.movieId == movieId).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link_update.imdbId is not None:
        db_link.imdbId = link_update.imdbId
    if link_update.tmdbId is not None:
        db_link.tmdbId = link_update.tmdbId

    db.commit()
    db.refresh(db_link)
    return db_link


@app.delete("/links/{movieId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(movieId: int, db: Session = Depends(get_db)):
    db_link = db.query(LinkModel).filter(LinkModel.movieId == movieId).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(db_link)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# === 3. RATINGS ===

@app.post("/ratings", response_model=RatingSchema, status_code=status.HTTP_201_CREATED)
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    # Tutaj ID generuje się automatycznie
    new_rating = RatingModel(
        userId=rating.userId,
        movieId=rating.movieId,
        rating=rating.rating,
        timestamp=datetime.utcnow()
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


@app.get("/ratings/{id}", response_model=RatingSchema)
def get_rating(id: int, db: Session = Depends(get_db)):
    rating = db.query(RatingModel).filter(RatingModel.id == id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@app.put("/ratings/{id}", response_model=RatingSchema)
def update_rating(id: int, rating_update: RatingUpdate, db: Session = Depends(get_db)):
    db_rating = db.query(RatingModel).filter(RatingModel.id == id).first()
    if not db_rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    if rating_update.rating is not None:
        db_rating.rating = rating_update.rating

    db.commit()
    db.refresh(db_rating)
    return db_rating


@app.delete("/ratings/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(id: int, db: Session = Depends(get_db)):
    db_rating = db.query(RatingModel).filter(RatingModel.id == id).first()
    if not db_rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(db_rating)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# === 4. TAGS ===

@app.post("/tags", response_model=TagSchema, status_code=status.HTTP_201_CREATED)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    new_tag = TagModel(
        userId=tag.userId,
        movieId=tag.movieId,
        tag=tag.tag,
        timestamp=datetime.utcnow()
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


@app.get("/tags/{id}", response_model=TagSchema)
def get_tag(id: int, db: Session = Depends(get_db)):
    tag = db.query(TagModel).filter(TagModel.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@app.put("/tags/{id}", response_model=TagSchema)
def update_tag(id: int, tag_update: TagUpdate, db: Session = Depends(get_db)):
    db_tag = db.query(TagModel).filter(TagModel.id == id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag_update.tag is not None:
        db_tag.tag = tag_update.tag

    db.commit()
    db.refresh(db_tag)
    return db_tag


@app.delete("/tags/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(id: int, db: Session = Depends(get_db)):
    db_tag = db.query(TagModel).filter(TagModel.id == id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(db_tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# List Endpoints (zachowane z oryginału)
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


# Inicjalizacja przy starcie (tylko tabele, bez importu CSV dla czystości testów)
if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)