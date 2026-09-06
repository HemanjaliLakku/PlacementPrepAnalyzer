import sqlite3

def get_db_connection():
    conn = sqlite3.connect("placement.db")
    conn.row_factory = sqlite3.Row
    return conn


conn = get_db_connection()

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Database created successfully!")