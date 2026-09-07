import sqlite3
import csv


def get_db_connection():
    conn = sqlite3.connect("placement.db")
    conn.row_factory = sqlite3.Row
    return conn


conn = get_db_connection()


# Users table
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# Questions table
conn.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question TEXT NOT NULL UNIQUE,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL
)
""")


# Import questions from CSV only if they are not already present
with open("questions.csv", "r", encoding="utf-8") as file:

    reader = csv.DictReader(file)

    for row in reader:

        existing_question = conn.execute(
            "SELECT id FROM questions WHERE question = ?",
            (row["question"],)
        ).fetchone()

        if existing_question is None:

            conn.execute("""
                INSERT INTO questions
                (
                    subject,
                    topic,
                    difficulty,
                    question,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_answer,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["subject"],
                row["topic"],
                row["difficulty"],
                row["question"],
                row["option_a"],
                row["option_b"],
                row["option_c"],
                row["option_d"],
                row["correct_answer"],
                row["explanation"]
            ))


conn.commit()
conn.close()

print("Database setup completed successfully!")