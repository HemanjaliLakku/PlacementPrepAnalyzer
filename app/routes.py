from flask import Blueprint, render_template, request, redirect, session
from database import get_db_connection
from ai_generator import generate_questions, save_questions
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

            existing_user = conn.execute("""
                SELECT id
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

            if existing_user:
                conn.close()
                return "Email already registered."

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

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    conn = get_db_connection()

    stats = conn.execute("""
        SELECT
            COUNT(*) AS tests_taken,
            COALESCE(SUM(total_questions), 0)
                AS questions_practiced,
            COALESCE(SUM(correct_answers), 0)
                AS correct_answers,
            COALESCE(SUM(wrong_answers), 0)
                AS wrong_answers,
            COALESCE(AVG(percentage), 0)
                AS average_accuracy
        FROM attempts
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    weak_topics = conn.execute("""
        SELECT
            subject,
            topic,
            SUM(total_questions)
                AS total_questions,
            SUM(correct_answers)
                AS correct_answers,
            ROUND(
                SUM(correct_answers) * 100.0 /
                NULLIF(SUM(total_questions), 0),
                2
            ) AS percentage
        FROM attempts
        WHERE user_id = ?
        GROUP BY subject, topic
        HAVING (
            SUM(correct_answers) * 100.0 /
            NULLIF(SUM(total_questions), 0)
        ) < 50
        ORDER BY percentage ASC
        LIMIT 5
    """, (user_id,)).fetchall()

    recent_attempts = conn.execute("""
        SELECT *
        FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    average_accuracy = round(
        stats["average_accuracy"] or 0,
        2
    )

    readiness_score = average_accuracy

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        tests_taken=stats["tests_taken"],
        questions_practiced=stats["questions_practiced"],
        correct_answers=stats["correct_answers"],
        wrong_answers=stats["wrong_answers"],
        average_accuracy=average_accuracy,
        readiness_score=readiness_score,
        weak_topics=weak_topics,
        recent_attempts=recent_attempts
    )


# ==================================================
# COMPANY PREPARATION DATA
# ==================================================

COMPANY_PREPARATION = {

    "tcs": {
        "name": "TCS",
        "areas": [
            {
                "title": "Quantitative Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude and numerical problem solving.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice logical and analytical reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals and technical questions.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "infosys": {
        "name": "Infosys",
        "areas": [
            {
                "title": "Quantitative Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice numerical and quantitative problem solving.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice logical and analytical reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming concepts and fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "accenture": {
        "name": "Accenture",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative placement questions.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice analytical reasoning and problem solving.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Improve programming fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "wipro": {
        "name": "Wipro",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice reasoning questions.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming and technical fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "cognizant": {
        "name": "Cognizant",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative problem solving.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice logical reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "capgemini": {
        "name": "Capgemini",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice logical and analytical skills.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming concepts.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "hcltech": {
        "name": "HCLTech",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice logical reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "tech-mahindra": {
        "name": "Tech Mahindra",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "ltimindtree": {
        "name": "LTIMindtree",
        "areas": [
            {
                "title": "Aptitude",
                "category": "Aptitude",
                "subject": "Quantitative Aptitude",
                "description": "Practice quantitative aptitude.",
                "link": "/practice?category=Aptitude&subject=Quantitative%20Aptitude"
            },
            {
                "title": "Reasoning",
                "category": "Reasoning",
                "subject": "Logical Reasoning",
                "description": "Practice reasoning.",
                "link": "/practice?category=Reasoning&subject=Logical%20Reasoning"
            },
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            }
        ]
    },

    "amazon": {
        "name": "Amazon",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice data structures and algorithms.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Database",
                "category": "Database",
                "subject": "",
                "description": "Practice SQL and database concepts.",
                "link": "/practice?category=Database"
            }
        ]
    },

    "microsoft": {
        "name": "Microsoft",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice algorithms and data structures.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Core CS",
                "category": "Core CS",
                "subject": "",
                "description": "Practice core computer science concepts.",
                "link": "/practice?category=Core%20CS"
            }
        ]
    },

    "google": {
        "name": "Google",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice data structures and algorithms.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Core CS",
                "category": "Core CS",
                "subject": "",
                "description": "Practice computer science fundamentals.",
                "link": "/practice?category=Core%20CS"
            }
        ]
    },

    "adobe": {
        "name": "Adobe",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming concepts.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice algorithms and data structures.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Database",
                "category": "Database",
                "subject": "",
                "description": "Practice database concepts.",
                "link": "/practice?category=Database"
            }
        ]
    },

    "zoho": {
        "name": "Zoho",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Practice programming fundamentals.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice DSA and problem solving.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Database",
                "category": "Database",
                "subject": "",
                "description": "Practice SQL and database fundamentals.",
                "link": "/practice?category=Database"
            }
        ]
    },

    "product-gcc": {
        "name": "Product / GCC Companies",
        "areas": [
            {
                "title": "Programming",
                "category": "Programming",
                "subject": "",
                "description": "Build strong programming fundamentals.",
                "link": "/practice?category=Programming"
            },
            {
                "title": "Data Structures",
                "category": "Data Structures",
                "subject": "",
                "description": "Practice algorithms and data structures.",
                "link": "/practice?category=Data%20Structures"
            },
            {
                "title": "Core CS",
                "category": "Core CS",
                "subject": "",
                "description": "Strengthen core computer science concepts.",
                "link": "/practice?category=Core%20CS"
            }
        ]
    }
}


# ==================================================
# COMPANIES
# ==================================================

@main.route("/companies")
def companies():

    if not session.get("user_id"):
        return redirect("/login")

    return render_template("company.html")


@main.route("/company/<company_name>")
def company_preparation(company_name):

    if not session.get("user_id"):
        return redirect("/login")

    company_key = company_name.lower()

    company_data = COMPANY_PREPARATION.get(
        company_key
    )

    if not company_data:
        return redirect("/companies")

    return render_template(
        "company_detail.html",
        company_name=company_data["name"],
        preparation_areas=company_data["areas"]
    )


# ==================================================
# MOCK TESTS HOME
# ==================================================

@main.route("/mock-tests")
def mock_tests():

    if not session.get("user_id"):
        return redirect("/login")

    return render_template(
        "mock_tests.html"
    )


# ==================================================
# START MOCK TEST
# ==================================================

@main.route("/mock-test/<test_type>")
def start_mock_test(test_type):

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db_connection()

    if test_type == "aptitude":

        questions = conn.execute("""
            SELECT *
            FROM questions
            WHERE category = 'Aptitude'
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()

        title = "Aptitude Mock Test"

    elif test_type == "reasoning":

        questions = conn.execute("""
            SELECT *
            FROM questions
            WHERE category = 'Reasoning'
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()

        title = "Reasoning Mock Test"

    elif test_type == "technical":

        questions = conn.execute("""
            SELECT *
            FROM questions
            WHERE category IN (
                'Programming',
                'Data Structures',
                'Database',
                'Core CS'
            )
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()

        title = "Technical Mock Test"

    elif test_type == "full":

        questions = conn.execute("""
            SELECT *
            FROM questions
            ORDER BY RANDOM()
            LIMIT 20
        """).fetchall()

        title = "Full Placement Mock Test"

    else:

        conn.close()
        return redirect("/mock-tests")

    conn.close()

    if not questions:

        return (
            "<h2>No questions available.</h2>"
            '<br><a href="/mock-tests">'
            "Back to Mock Tests"
            "</a>"
        )

    return render_template(
        "mock_test.html",
        questions=questions,
        title=title,
        test_type=test_type
    )


# ==================================================
# SUBMIT MOCK TEST
# ==================================================

@main.route(
    "/submit-mock-test",
    methods=["POST"]
)
def submit_mock_test():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    test_type = request.form.get(
        "test_type",
        "full"
    )

    question_ids = request.form.getlist(
        "question_ids"
    )

    if not question_ids:

        return redirect("/mock-tests")

    conn = get_db_connection()

    questions = []

    for question_id in question_ids:

        question = conn.execute("""
            SELECT *
            FROM questions
            WHERE id = ?
        """, (
            question_id,
        )).fetchone()

        if question:
            questions.append(question)

    score = 0

    for question in questions:

        user_answer = request.form.get(
            f"question_{question['id']}"
        )

        if user_answer == question[
            "correct_answer"
        ]:

            score += 1

    total = len(questions)

    wrong = total - score

    if total > 0:

        percentage = round(
            (score / total) * 100,
            2
        )

    else:

        percentage = 0

    titles = {
        "aptitude": "Aptitude Mock Test",
        "reasoning": "Reasoning Mock Test",
        "technical": "Technical Mock Test",
        "full": "Full Placement Mock Test"
    }

    title = titles.get(
        test_type,
        "Mock Test"
    )

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
        "Mock Test",
        title,
        test_type.title(),
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
# ADMIN - ADD / VIEW QUESTIONS
# ==================================================

@main.route("/admin", methods=["GET", "POST"])
def admin():

    conn = get_db_connection()

    if request.method == "POST":

        category = request.form[
            "category"
        ].strip()

        subject = request.form[
            "subject"
        ].strip()

        topic = request.form[
            "topic"
        ].strip()

        difficulty = request.form[
            "difficulty"
        ].strip()

        question = request.form[
            "question"
        ].strip()

        option_a = request.form[
            "option_a"
        ].strip()

        option_b = request.form[
            "option_b"
        ].strip()

        option_c = request.form[
            "option_c"
        ].strip()

        option_d = request.form[
            "option_d"
        ].strip()

        correct_answer = request.form[
            "correct_answer"
        ].strip().upper()

        explanation = request.form[
            "explanation"
        ].strip()

        try:

            existing = conn.execute("""
                SELECT id
                FROM questions
                WHERE LOWER(TRIM(question))
                    = LOWER(TRIM(?))
            """, (
                question,
            )).fetchone()

            if existing:

                conn.close()

                return "This question already exists."

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

            return (
                f"Question could not be added: {e}"
            )

        conn.close()

        return redirect("/admin")

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
# AI QUESTION GENERATOR
# ==================================================

@main.route(
    "/generate-ai-questions",
    methods=["POST"]
)
def generate_ai_questions():

    category = request.form[
        "category"
    ].strip()

    subject = request.form[
        "subject"
    ].strip()

    topic = request.form[
        "topic"
    ].strip()

    difficulty = request.form[
        "difficulty"
    ].strip()

    count = request.form.get(
        "count",
        5,
        type=int
    )

    if count < 1:
        count = 5

    if count > 100:
        count = 100

    try:

        generated_questions = generate_questions(
            subject,
            topic,
            difficulty,
            count
        )

        result = save_questions(
            generated_questions,
            category,
            subject,
            topic,
            difficulty
        )

        return (
            "<h2>AI Generation Completed</h2>"
            f"<p>{result['added']} questions added.</p>"
            f"<p>{result['skipped']} duplicates skipped.</p>"
            f"<p>{result['invalid']} invalid questions skipped.</p>"
            "<br>"
            '<a href="/admin">Back to Admin</a>'
        )

    except Exception as e:

        return (
            "<h2>AI Question Generation Failed</h2>"
            f"<p>{e}</p>"
            "<br>"
            '<a href="/admin">Back to Admin</a>'
        )


# ==================================================
# BULK CSV IMPORT
# ==================================================

@main.route(
    "/import-questions",
    methods=["POST"]
)
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

        content = (
            file.stream
            .read()
            .decode("utf-8-sig")
            .splitlines()
        )

        reader = csv.DictReader(
            content
        )

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
                WHERE LOWER(TRIM(question))
                    = LOWER(TRIM(?))
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

    if count < 1:
        count = 5

    if count > 100:
        count = 100

    conn = get_db_connection()

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM questions
        WHERE category IS NOT NULL
        AND TRIM(category) != ''
        ORDER BY category
    """).fetchall()

    subjects = conn.execute("""
        SELECT DISTINCT
            category,
            subject
        FROM questions
        WHERE subject IS NOT NULL
        AND TRIM(subject) != ''
        ORDER BY subject
    """).fetchall()

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

    difficulties = conn.execute("""
        SELECT DISTINCT difficulty
        FROM questions
        WHERE difficulty IS NOT NULL
        AND TRIM(difficulty) != ''
        ORDER BY difficulty
    """).fetchall()

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

        params.append(category)

    if subject:

        query += """
            AND subject = ?
        """

        params.append(subject)

    if topic:

        query += """
            AND topic = ?
        """

        params.append(topic)

    if difficulty:

        query += """
            AND difficulty = ?
        """

        params.append(difficulty)

    query += """
        ORDER BY RANDOM()
        LIMIT ?
    """

    params.append(count)

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

    if not user_id:
        return redirect("/login")

    question_ids = request.form.getlist(
        "question_ids"
    )

    if not question_ids:
        return "No questions were submitted."

    conn = get_db_connection()

    questions = []

    for question_id in question_ids:

        question = conn.execute("""
            SELECT *
            FROM questions
            WHERE id = ?
        """, (
            question_id,
        )).fetchone()

        if question:
            questions.append(question)

    score = 0

    for q in questions:

        user_answer = request.form.get(
            f"question_{q['id']}"
        )

        if user_answer == q[
            "correct_answer"
        ]:

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

    if questions:

        category = questions[0][
            "category"
        ]

        subject = questions[0][
            "subject"
        ]

    else:

        category = None
        subject = "Unknown"

    topics = sorted({
        q["topic"]
        for q in questions
        if q["topic"]
    })

    topic_text = ", ".join(
        topics
    )

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

    attempts = conn.execute("""
        SELECT *
        FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
    """, (
        user_id,
    )).fetchall()

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

    topic_performance = conn.execute("""
        SELECT

            subject,

            topic,

            SUM(total_questions)
                AS total_questions,

            SUM(correct_answers)
                AS correct_answers,

            ROUND(
                SUM(correct_answers) * 100.0 /
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

    weak_topics = [
        row
        for row in topic_performance
        if row["percentage"] < 50
    ]

    improvement_topics = [
        row
        for row in topic_performance
        if (
            row["percentage"] >= 50
            and row["percentage"] < 75
        )
    ]

    strong_topics = [
        row
        for row in topic_performance
        if row["percentage"] >= 75
    ]

    recommendations = []

    for topic_data in topic_performance:

        percentage = topic_data[
            "percentage"
        ]

        if percentage < 50:

            recommendations.append({

                "subject":
                    topic_data["subject"],

                "topic":
                    topic_data["topic"],

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
                    topic_data["subject"],

                "topic":
                    topic_data["topic"],

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
                    topic_data["subject"],

                "topic":
                    topic_data["topic"],

                "percentage":
                    percentage,

                "message":
                    (
                        "Strong topic. "
                        "Keep practicing to maintain "
                        "your performance."
                    )
            })

    readiness_score = round(
        summary["average_percentage"] or 0,
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
        topic_performance=topic_performance,
        weak_topics=weak_topics,
        improvement_topics=improvement_topics,
        strong_topics=strong_topics,
        recommendations=recommendations,
        readiness_score=readiness_score,
        readiness_message=readiness_message
    )