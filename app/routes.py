from flask import Blueprint, render_template, request, redirect
from database import get_db_connection

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()

        except Exception as e:
            conn.close()
            return f"Registration failed: {e}"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        subject = request.form["subject"]
        topic = request.form["topic"]
        difficulty = request.form["difficulty"]
        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_answer = request.form["correct_answer"]
        explanation = request.form["explanation"]

        conn = get_db_connection()

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
        ))

        conn.commit()
        conn.close()

        return "Question added successfully!"

    return render_template("admin.html")


@main.route("/practice")
def practice():

    subject = request.args.get("subject")
    count = request.args.get("count", 5, type=int)

    if not subject:
        return render_template("practice.html")

    conn = get_db_connection()

    questions = conn.execute("""
        SELECT *
        FROM questions
        WHERE subject = ?
        ORDER BY RANDOM()
        LIMIT ?
    """, (subject, count)).fetchall()

    conn.close()

    return render_template(
        "practice.html",
        questions=questions,
        subject=subject
    )


@main.route("/submit-practice", methods=["POST"])
def submit_practice():

    subject = request.form["subject"]

    # Get only the questions shown in the current practice session
    question_ids = request.form.getlist("question_ids")

    conn = get_db_connection()

    questions = []

    for question_id in question_ids:

        question = conn.execute(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,)
        ).fetchone()

        if question:
            questions.append(question)

    conn.close()

    score = 0
    total = len(questions)

    for q in questions:

        user_answer = request.form.get(
            f"question_{q['id']}"
        )

        if user_answer == q["correct_answer"]:
            score += 1

    return f"Your Score: {score}/{total}"