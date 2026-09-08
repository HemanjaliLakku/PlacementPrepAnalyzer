import sqlite3
import csv


def get_db_connection():
    conn = sqlite3.connect("placement.db")
    conn.row_factory = sqlite3.Row
    return conn


conn = get_db_connection()


# --------------------------------------------------
# USERS TABLE
# --------------------------------------------------

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# --------------------------------------------------
# QUESTIONS TABLE
# --------------------------------------------------

conn.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'Programming',
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


# --------------------------------------------------
# PERFORMANCE / ATTEMPTS TABLE
# --------------------------------------------------

conn.execute("""
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    subject TEXT NOT NULL,
    topic TEXT,
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    wrong_answers INTEGER NOT NULL,
    score INTEGER NOT NULL,
    percentage REAL NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# --------------------------------------------------
# CSV QUESTION IMPORT
# --------------------------------------------------

try:

    with open("questions.csv", "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        added = 0
        skipped = 0

        for row in reader:

            question_text = row["question"].strip()

            # Check whether the question already exists
            existing = conn.execute(
                "SELECT id FROM questions WHERE question = ?",
                (question_text,)
            ).fetchone()

            if existing:
                skipped += 1
                continue

            conn.execute("""
                INSERT INTO questions
                (
                    category,
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["category"].strip(),
                row["subject"].strip(),
                row["topic"].strip(),
                row["difficulty"].strip(),
                question_text,
                row["option_a"].strip(),
                row["option_b"].strip(),
                row["option_c"].strip(),
                row["option_d"].strip(),
                row["correct_answer"].strip().upper(),
                row["explanation"].strip()
            ))

            added += 1

    print(f"Questions added: {added}")
    print(f"Duplicates skipped: {skipped}")

except FileNotFoundError:

    print("questions.csv not found. Skipping CSV import.")


# --------------------------------------------------
# SAVE CHANGES
# --------------------------------------------------

conn.commit()
conn.close()

print("Database setup completed successfully!")