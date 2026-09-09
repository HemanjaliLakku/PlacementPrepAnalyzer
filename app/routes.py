from flask import Blueprint, render_template, request, redirect, session
from database import get_db_connection
import csv

main = Blueprint("main", __name__)


# ==================================================
# HOME
# ==================================================

@main.route("/")
def home():
    return render_template("index.html")


# ==================================================
# REGISTER
# ==================================================

@main.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db_connection()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                password
            ))

            conn.commit()

        except Exception as e:

            conn.close()
            return f"Registration failed: {e}"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ==================================================
# LOGIN
# ==================================================

@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
        """, (
            email,
            password
        )).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")


# ==================================================
# LOGOUT
# ==================================================

@main.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ==================================================
# DASHBOARD
# ==================================================

@main.route("/dashboard")
def dashboard():

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name")
    )


# ==================================================
# ADMIN - ADD / VIEW QUESTIONS
# ==================================================

@main.route("/admin", methods=["GET", "POST"])
def admin():

    conn = get_db_connection()

    if request.method == "POST":

        category = request.form["category"].strip()
        subject = request.form["subject"].strip()
        topic = request.form["topic"].strip()
        difficulty = request.form["difficulty"].strip()

        question = request.form["question"].strip()

        option_a = request.form["option_a"].strip()
        option_b = request.form["option_b"].strip()
        option_c = request.form["option_c"].strip()
        option_d = request.form["option_d"].strip()

        correct_answer = request.form[
            "correct_answer"
        ].strip().upper()

        explanation = request.form[
            "explanation"
        ].strip()


        try:

            # Duplicate check
            existing = conn.execute("""
                SELECT id
                FROM questions
                WHERE question = ?
            """, (
                question,
            )).fetchone()


            if existing:

                conn.close()

                return "This question already exists."


            # Insert question
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
            ))


            conn.commit()

        except Exception as e:

            conn.close()

            return f"Question could not be added: {e}"


        conn.close()

        return redirect("/admin")


    # Get all questions
    questions = conn.execute("""
        SELECT *
        FROM questions
        ORDER BY id DESC
    """).fetchall()

    conn.close()


    return render_template(
        "admin.html",
        questions=questions
    )


# ==================================================
# BULK CSV IMPORT
# ==================================================

@main.route("/import-questions", methods=["POST"])
def import_questions():

    file = request.files.get(
        "question_file"
    )


    if not file:

        return "Please select a CSV file."


    if file.filename == "":

        return "Please select a CSV file."


    if not file.filename.lower().endswith(".csv"):

        return "Only CSV files are allowed."


    conn = get_db_connection()

    added = 0
    skipped = 0


    try:

        content = file.stream.read().decode(
            "utf-8-sig"
        ).splitlines()


        reader = csv.DictReader(content)


        required_columns = {
            "category",
            "subject",
            "topic",
            "difficulty",
            "question",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "explanation"
        }


        if not reader.fieldnames:

            conn.close()

            return "CSV file is empty."


        missing_columns = (
            required_columns
            - set(reader.fieldnames)
        )


        if missing_columns:

            conn.close()

            return (
                "Missing CSV columns: "
                + ", ".join(missing_columns)
            )


        for row in reader:

            question_text = row[
                "question"
            ].strip()


            if not question_text:

                continue


            existing = conn.execute("""
                SELECT id
                FROM questions
                WHERE question = ?
            """, (
                question_text,
            )).fetchone()


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


        conn.commit()
        conn.close()


        return (
            f"Import completed! "
            f"{added} questions added, "
            f"{skipped} duplicate questions skipped."
        )


    except Exception as e:

        conn.rollback()
        conn.close()

        return f"Import failed: {e}"


# ==================================================
# PRACTICE
# ==================================================

@main.route("/practice")
def practice():

    category = request.args.get(
        "category"
    )

    subject = request.args.get(
        "subject"
    )

    topic = request.args.get(
        "topic"
    )

    difficulty = request.args.get(
        "difficulty"
    )

    count = request.args.get(
        "count",
        5,
        type=int
    )


    # Prevent invalid question count
    if count < 1:

        count = 5


    # One test maximum = 100 questions
    if count > 100:

        count = 100


    conn = get_db_connection()


    # --------------------------------------------------
    # DYNAMIC CATEGORIES
    # --------------------------------------------------

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM questions
        WHERE category IS NOT NULL
        AND TRIM(category) != ''
        ORDER BY category
    """).fetchall()


    # --------------------------------------------------
    # DYNAMIC SUBJECTS
    # --------------------------------------------------

    subjects = conn.execute("""
        SELECT DISTINCT
            category,
            subject
        FROM questions
        WHERE subject IS NOT NULL
        AND TRIM(subject) != ''
        ORDER BY subject
    """).fetchall()


    # --------------------------------------------------
    # DYNAMIC TOPICS
    # --------------------------------------------------

    topics = conn.execute("""
        SELECT DISTINCT
            category,
            subject,
            topic
        FROM questions
        WHERE topic IS NOT NULL
        AND TRIM(topic) != ''
        ORDER BY topic
    """).fetchall()


    # --------------------------------------------------
    # DYNAMIC DIFFICULTIES
    # --------------------------------------------------

    difficulties = conn.execute("""
        SELECT DISTINCT difficulty
        FROM questions
        WHERE difficulty IS NOT NULL
        AND TRIM(difficulty) != ''
        ORDER BY difficulty
    """).fetchall()


    # --------------------------------------------------
    # NO FILTER SELECTED
    # --------------------------------------------------

    if (
        not category
        and not subject
        and not topic
        and not difficulty
    ):

        conn.close()

        return render_template(
            "practice.html",
            questions=[],
            categories=categories,
            subjects=subjects,
            topics=topics,
            difficulties=difficulties,
            category=None,
            subject=None,
            topic=None,
            difficulty=None
        )


    # --------------------------------------------------
    # PRACTICE QUESTION QUERY
    # --------------------------------------------------

    query = """
        SELECT *
        FROM questions
        WHERE 1 = 1
    """

    params = []


    if category:

        query += """
            AND category = ?
        """

        params.append(
            category
        )


    if subject:

        query += """
            AND subject = ?
        """

        params.append(
            subject
        )


    if topic:

        query += """
            AND topic = ?
        """

        params.append(
            topic
        )


    if difficulty:

        query += """
            AND difficulty = ?
        """

        params.append(
            difficulty
        )


    # Random questions
    query += """
        ORDER BY RANDOM()
        LIMIT ?
    """

    params.append(
        count
    )


    questions = conn.execute(
        query,
        params
    ).fetchall()


    conn.close()


    return render_template(
        "practice.html",

        questions=questions,

        categories=categories,

        subjects=subjects,

        topics=topics,

        difficulties=difficulties,

        category=category,

        subject=subject,

        topic=topic,

        difficulty=difficulty
    )


# ==================================================
# SUBMIT PRACTICE
# ==================================================

@main.route(
    "/submit-practice",
    methods=["POST"]
)
def submit_practice():

    user_id = session.get(
        "user_id"
    )


    question_ids = request.form.getlist(
        "question_ids"
    )


    if not question_ids:

        return "No questions were submitted."


    conn = get_db_connection()


    questions = []


    # Get only submitted questions
    for question_id in question_ids:

        question = conn.execute("""
            SELECT *
            FROM questions
            WHERE id = ?
        """, (
            question_id,
        )).fetchone()


        if question:

            questions.append(
                question
            )


    score = 0


    # Check answers
    for q in questions:

        user_answer = request.form.get(
            f"question_{q['id']}"
        )


        if user_answer == q["correct_answer"]:

            score += 1


    total = len(
        questions
    )


    wrong = total - score


    if total > 0:

        percentage = round(
            (score / total) * 100,
            2
        )

    else:

        percentage = 0


    # First question determines session subject/category
    if questions:

        category = questions[0]["category"]

        subject = questions[0]["subject"]

    else:

        category = None

        subject = "Unknown"


    # Get topics
    topics = sorted({
        q["topic"]
        for q in questions
        if q["topic"]
    })


    topic_text = ", ".join(
        topics
    )


    # --------------------------------------------------
    # SAVE PERFORMANCE
    # --------------------------------------------------

    conn.execute("""
        INSERT INTO attempts
        (
            user_id,
            category,
            subject,
            topic,
            total_questions,
            correct_answers,
            wrong_answers,
            score,
            percentage
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        category,
        subject,
        topic_text,
        total,
        score,
        wrong,
        score,
        percentage
    ))


    conn.commit()
    conn.close()


    return render_template(
        "result.html",
        score=score,
        total=total,
        wrong=wrong,
        percentage=percentage,
        questions=questions
    )


# ==================================================
# PERFORMANCE
# ==================================================

@main.route("/performance")
def performance():

    user_id = session.get(
        "user_id"
    )


    if not user_id:

        return redirect("/login")


    conn = get_db_connection()


    # --------------------------------------------------
    # PRACTICE HISTORY
    # --------------------------------------------------

    attempts = conn.execute("""
        SELECT *
        FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
    """, (
        user_id,
    )).fetchall()


    # --------------------------------------------------
    # OVERALL SUMMARY
    # --------------------------------------------------

    summary = conn.execute("""
        SELECT

            COUNT(*) AS total_attempts,

            COALESCE(
                SUM(total_questions),
                0
            ) AS total_questions,

            COALESCE(
                SUM(correct_answers),
                0
            ) AS total_correct,

            COALESCE(
                SUM(wrong_answers),
                0
            ) AS total_wrong,

            COALESCE(
                AVG(percentage),
                0
            ) AS average_percentage

        FROM attempts

        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()


    # --------------------------------------------------
    # TOPIC PERFORMANCE
    # --------------------------------------------------

    topic_performance = conn.execute("""
        SELECT

            subject,

            topic,

            SUM(total_questions)
                AS total_questions,

            SUM(correct_answers)
                AS correct_answers,

            ROUND(
                (
                    SUM(correct_answers)
                    * 100.0
                )
                /
                NULLIF(
                    SUM(total_questions),
                    0
                ),
                2
            ) AS percentage

        FROM attempts

        WHERE user_id = ?

        GROUP BY subject, topic

        ORDER BY percentage ASC
    """, (
        user_id,
    )).fetchall()


    conn.close()


    # --------------------------------------------------
    # WEAK TOPICS
    # --------------------------------------------------

    weak_topics = [

        row

        for row in topic_performance

        if row["percentage"] < 50

    ]


    # --------------------------------------------------
    # NEEDS IMPROVEMENT
    # --------------------------------------------------

    improvement_topics = [

        row

        for row in topic_performance

        if (
            row["percentage"] >= 50
            and row["percentage"] < 75
        )

    ]


    # --------------------------------------------------
    # STRONG TOPICS
    # --------------------------------------------------

    strong_topics = [

        row

        for row in topic_performance

        if row["percentage"] >= 75

    ]


    # --------------------------------------------------
    # PERSONALIZED RECOMMENDATIONS
    # --------------------------------------------------

    recommendations = []


    for topic in topic_performance:

        percentage = topic[
            "percentage"
        ]


        if percentage < 50:

            recommendations.append({

                "subject":
                    topic["subject"],

                "topic":
                    topic["topic"],

                "percentage":
                    percentage,

                "message":
                    (
                        "Needs more practice. "
                        "Focus on this topic first."
                    )
            })


        elif percentage < 75:

            recommendations.append({

                "subject":
                    topic["subject"],

                "topic":
                    topic["topic"],

                "percentage":
                    percentage,

                "message":
                    (
                        "Good start. "
                        "Practice more to improve your score."
                    )
            })


        else:

            recommendations.append({

                "subject":
                    topic["subject"],

                "topic":
                    topic["topic"],

                "percentage":
                    percentage,

                "message":
                    (
                        "Strong topic. "
                        "Keep practicing to maintain your performance."
                    )
            })


    # --------------------------------------------------
    # PLACEMENT READINESS
    # --------------------------------------------------

    readiness_score = round(
        summary["average_percentage"],
        2
    )


    if readiness_score < 40:

        readiness_message = (
            "Needs significant improvement. "
            "Focus on your weak topics."
        )


    elif readiness_score < 60:

        readiness_message = (
            "You are making progress. "
            "Continue regular practice."
        )


    elif readiness_score < 75:

        readiness_message = (
            "Good preparation. "
            "Focus on weak areas to improve further."
        )


    elif readiness_score < 90:

        readiness_message = (
            "Very good preparation. "
            "Keep practicing consistently."
        )


    else:

        readiness_message = (
            "Excellent preparation. "
            "You are showing strong placement readiness."
        )


    return render_template(

        "performance.html",

        attempts=attempts,

        summary=summary,

        topic_performance=
            topic_performance,

        weak_topics=
            weak_topics,

        improvement_topics=
            improvement_topics,

        strong_topics=
            strong_topics,

        recommendations=
            recommendations,

        readiness_score=
            readiness_score,

        readiness_message=
            readiness_message
    )