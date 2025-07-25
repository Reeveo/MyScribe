import sqlite3
from datetime import datetime

DB_PATH = 'myscribe.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            cleaned_text TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_transcription(audio_path, cleaned_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO transcriptions (audio_path, timestamp, cleaned_text)
        VALUES (?, ?, ?)
    ''', (audio_path, datetime.now().isoformat(), cleaned_text))
    conn.commit()
    conn.close()

def fetch_all_transcriptions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, audio_path, timestamp, cleaned_text FROM transcriptions ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return rows 