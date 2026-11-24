"""ACEest Fitness & Gym - Flask application for CI/CD demonstration."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.getenv("ACEEST_DATABASE", BASE_DIR / "instance" / "aceest.db"))
VERSION = os.getenv("APP_VERSION", "3.2.4")

PROGRAMS = {
    "Fat Loss": {"workout": "Strength training, interval cardio, and active recovery.", "diet": "Balanced meals with a moderate calorie deficit.", "calories": 2000},
    "Muscle Gain": {"workout": "Progressive overload: squat, press, hinge, and row movements.", "diet": "Protein-rich meals with a modest calorie surplus.", "calories": 2800},
    "Beginner": {"workout": "Full-body circuit: squats, rows, push-ups, and walking.", "diet": "Balanced meals with adequate protein and hydration.", "calories": 2200},
}

def get_db() -> sqlite3.Connection:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age BETWEEN 12 AND 100),
            goal TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "local-development-key-change-me")
    init_db()

    @app.get("/")
    def index():
        with get_db() as conn:
            clients = conn.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
        return render_template("index.html", clients=clients, programs=PROGRAMS, version=VERSION)

    @app.post("/clients")
    def add_client():
        name = request.form.get("name", "").strip()
        goal = request.form.get("goal", "")
        try:
            age = int(request.form.get("age", ""))
        except ValueError:
            age = 0
        if not name or len(name) > 80 or not 12 <= age <= 100 or goal not in PROGRAMS:
            flash("Enter a valid name, age (12–100), and fitness goal.", "error")
            return redirect(url_for("index"))
        with get_db() as conn:
            conn.execute("INSERT INTO clients(name, age, goal) VALUES (?, ?, ?)", (name, age, goal))
        flash(f"Client {name} added successfully.", "success")
        return redirect(url_for("index"))

    @app.post("/clients/<int:client_id>/delete")
    def delete_client(client_id: int):
        with get_db() as conn:
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        flash("Client record deleted.", "success")
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        return {"status": "healthy", "version": VERSION}, 200

    @app.get("/ready")
    def ready():
        try:
            with get_db() as conn:
                conn.execute("SELECT 1")
            return {"status": "ready"}, 200
        except sqlite3.Error:
            return {"status": "not-ready"}, 503

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
