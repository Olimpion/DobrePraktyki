from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import csv

class Movie(BaseModel):
    movie_id: int
    title: str
    genres: list[str]

class Link(BaseModel):
    movieId: int
    imdbId: int
    tmdbId: int | None = None

class Rating(BaseModel):
    userId: int
    movieId: int
    rating: float
    timestamp: datetime

class Tag(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: datetime

def load_movies_from_csv(file_path: str) -> list[Movie]:
    movies = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                genres_list = row['genres'].split('|') if row['genres'] else []
                movie = Movie(
                    movie_id=int(row['movieId']),
                    title=row['title'],
                    genres=genres_list
                )
                movies.append(movie)
            except ValueError as e:
                print(f"Błąd podczas przetwarzania wiersza: {row} - {e}")
            except KeyError as e:
                print(f"Brakujący klucz w wierszu: {row} - {e}")
    return movies

def load_links_from_csv(file_path: str) -> list[Link]:
    links = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                raw_tmdb = row.get('tmdbId', '')

                if raw_tmdb and raw_tmdb.strip():
                    tmdb_id = int(raw_tmdb)
                else:
                    tmdb_id = None

                link = Link(
                    movieId=int(row['movieId']),
                    imdbId=int(row['imdbId']),
                    tmdbId=tmdb_id
                )
                links.append(link)
            except ValueError as e:
                print(f"Błąd podczas przetwarzania wiersza: {row} - {e}")
            except KeyError as e:
                print(f"Brakujący klucz w wierszu: {row} - {e}")
    return links

def load_ratings_from_csv(file_path: str) -> list[Rating]:
    ratings = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                rating = Rating(
                    userId=int(row['userId']),
                    movieId=int(row['movieId']),
                    rating=float(row['rating']),
                    timestamp=datetime.fromtimestamp(int(float(row['timestamp'])))
                )
                ratings.append(rating)
            except ValueError as e:
                print(f"Błąd podczas przetwarzania wiersza: {row} - {e}")
            except KeyError as e:
                print(f"Brakujący klucz w wierszu: {row} - {e}")
    return ratings

def load_tags_from_csv(file_path: str) -> list[Tag]:
    tags = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                tag = Tag(
                    userId=int(row['userId']),
                    movieId=int(row['movieId']),
                    tag=row['tag'],
                    timestamp=datetime.fromtimestamp(int(float(row['timestamp'])))
                )
                tags.append(tag)
            except ValueError as e:
                print(f"Błąd podczas przetwarzania wiersza: {row} - {e}")
            except KeyError as e:
                print(f"Brakujący klucz w wierszu: {row} - {e}")
    return tags

MOVIES_DATA = load_movies_from_csv("Database/movies.csv")
LINKS_DATA = load_links_from_csv("Database/links.csv")
RATINGS_DATA = load_ratings_from_csv("Database/ratings.csv")
TAGS_DATA = load_tags_from_csv("Database/tags.csv")




app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/movies", response_model=list[Movie])
def get_movies():
    return MOVIES_DATA

@app.get("/links", response_model=list[Link])
def get_movies():
    return LINKS_DATA

@app.get("/ratings", response_model=list[Rating])
def get_movies():
    return RATINGS_DATA

@app.get("/tags", response_model=list[Tag])
def get_movies():
    return TAGS_DATA
