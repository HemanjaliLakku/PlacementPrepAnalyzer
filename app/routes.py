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