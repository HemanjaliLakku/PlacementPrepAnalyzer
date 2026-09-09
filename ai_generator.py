import json
import sqlite3
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def clean_json_text(text):
    """
    Extract JSON object from Ollama response.
    Handles markdown fences or extra text around JSON.
    """

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    text = text.strip()

    # Find first JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text


def generate_questions(subject, topic, difficulty, count=5):
    """
    Generate placement MCQs using local Ollama model.
    """

    prompt = f"""
Generate exactly {count} multiple-choice placement questions.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

Return ONLY one valid JSON object.
Do not use markdown.
Do not write any text before or after the JSON.

Use exactly this structure:

{{
  "questions": [
    {{
      "question": "Question text",
      "option_a": "Option A",
      "option_b": "Option B",
      "option_c": "Option C",
      "option_d": "Option D",
      "correct_answer": "A",
      "explanation": "Short explanation"
    }}
  ]
}}

Rules:
- correct_answer must be only A, B, C, or D.
- Exactly four options for every question.
- Every question must be relevant to {subject} and {topic}.
- Avoid duplicate questions.
- Keep explanations short.
- Do not put quotation marks inside values unless necessary.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        },
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    text = data.get("response", "").strip()

    if not text:
        raise ValueError(
            "Ollama returned an empty response."
        )

    cleaned_text = clean_json_text(text)

    try:

        result = json.loads(cleaned_text)

    except json.JSONDecodeError as e:

        print("\n----- OLLAMA RAW RESPONSE -----\n")
        print(text)
        print("\n-------------------------------\n")

        raise ValueError(
            f"Ollama returned invalid JSON: {e}"
        )

    questions = result.get("questions", [])

    if not isinstance(questions, list):

        raise ValueError(
            "Invalid JSON structure: questions must be a list."
        )

    return questions


def validate_question(q):
    """
    Basic question validation.
    """

    required_fields = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "explanation"
    ]

    for field in required_fields:

        value = q.get(field)

        if not isinstance(value, str):
            return False

        if not value.strip():
            return False

    if q["correct_answer"].strip().upper() not in {
        "A", "B", "C", "D"
    }:
        return False

    return True


def save_questions(
    questions,
    category,
    subject,
    topic,
    difficulty
):
    """
    Save generated questions into SQLite.
    Duplicate questions are skipped.
    """

    conn = sqlite3.connect("placement.db")

    added = 0
    skipped = 0
    invalid = 0

    for q in questions:

        if not isinstance(q, dict):

            invalid += 1
            continue

        if not validate_question(q):

            invalid += 1
            continue

        question = q["question"].strip()

        option_a = q["option_a"].strip()
        option_b = q["option_b"].strip()
        option_c = q["option_c"].strip()
        option_d = q["option_d"].strip()

        correct_answer = (
            q["correct_answer"]
            .strip()
            .upper()
        )

        explanation = q["explanation"].strip()


        # Duplicate check
        existing = conn.execute(
            """
            SELECT id
            FROM questions
            WHERE LOWER(TRIM(question))
                = LOWER(TRIM(?))
            """,
            (question,)
        ).fetchone()


        if existing:

            skipped += 1
            continue


        # Insert
        conn.execute(
            """
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
            """,
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
        )

        added += 1


    conn.commit()
    conn.close()


    return {
        "added": added,
        "skipped": skipped,
        "invalid": invalid
    }