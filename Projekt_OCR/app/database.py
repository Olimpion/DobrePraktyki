import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "results.db"))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabela na wyniki OCR
    c.execute('''CREATE TABLE IF NOT EXISTS plate_results 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  plate_text TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_result(text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO plate_results (plate_text) VALUES (?)", (text,))
    conn.commit()
    conn.close()