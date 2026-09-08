from flask import Flask
from app.routes import main

app = Flask(__name__)

# Secret key required for Flask sessions
app.secret_key = "placement-prep-secret-key"

app.register_blueprint(main)


if __name__ == "__main__":
    app.run(debug=True)