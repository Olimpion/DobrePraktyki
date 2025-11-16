from fastapi import FastAPI
from pydantic import BaseModel
import csv

# Definicja klasy Pydantic do mapowania danych filmów
class Movie(BaseModel):
    movie_id: int
    title: str
    genres: list[str]

# Funkcja do wczytywania i przetwarzania danych z CSV
def load_movies_from_csv(file_path: str) -> list[Movie]:
    movies = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Parsowanie gatunków, zakładając, że są oddzielone znakiem '|'
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

# Wczytaj filmy podczas uruchamiania aplikacji
# Możesz zmienić ścieżkę do pliku CSV, jeśli jest inna
MOVIES_DATA = load_movies_from_csv("Database/movies.csv")




app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/movies", response_model=list[Movie])
def get_movies():
    """
    Zwraca listę wszystkich filmów.
    """
    return MOVIES_DATA


