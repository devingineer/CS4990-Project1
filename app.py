import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

from flask import Flask, render_template, request, redirect, url_for, session

# ── Config ────────────────────────────────────────────────────────────────────
APP_SECRET   = os.environ.get("SECRET_KEY", "dev-secret-change-me")
FIG_DIR      = Path("figures")
DB_PATH      = Path("responses.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

# ── Questions ─────────────────────────────────────────────────────────────────
QUESTIONS = {
    "Devin-Figure1.png": {
        "prompt": "Does Kit Kat have approximately more or less than 35% sugar?",
        "choices": ["More", "Less", "About 35%"],
        "correct": "Less",
    },
    "Devin-Figure2.png": {
        "prompt": "Approximate the difference in sugar percentage between Milky Way and Twix.",
        "choices": ["~3%", "~8%", "~15%", "~20%"],
        "correct": "~8%",
    },
    "Devin-Figure3.png": {
        "prompt": "Is there a larger gap in sugar percentage between Peanut Butter Cup and Milky Way, or between Peanut Butter Cup and Twix?",
        "choices": ["Peanut Butter Cup and Milky Way", "Peanut Butter Cup and Twix", "The gap is about the same"],
        "correct": "Peanut Butter Cup and Milky Way",
    },
}

DEFAULT_QUESTION = {
    "prompt": "Based on the figure, which option best answers the question?",
    "choices": ["A", "B", "C", "D"],
    "correct": None,
}

# ── Database helpers ──────────────────────────────────────────────────────────
def _placeholder():
    """Return the correct parameter placeholder for the active DB driver."""
    return "%s" if DATABASE_URL else "?"


def get_conn():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        if DATABASE_URL:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id SERIAL PRIMARY KEY,
                    ts TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    figure TEXT NOT NULL,
                    question TEXT NOT NULL,
                    choice TEXT NOT NULL,
                    correct_choice TEXT,
                    is_correct INTEGER
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    figure TEXT NOT NULL,
                    question TEXT NOT NULL,
                    choice TEXT NOT NULL,
                    correct_choice TEXT,
                    is_correct INTEGER
                )
            """)
        conn.commit()


def insert_response(user_id, figure, question, choice, correct_choice, is_correct):
    ph = _placeholder()
    sql = f"""
        INSERT INTO responses (ts, user_id, figure, question, choice, correct_choice, is_correct)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    """
    with get_conn() as conn:
        conn.cursor().execute(sql, (
            datetime.now(timezone.utc).isoformat(),
            user_id, figure, question, choice, correct_choice, is_correct,
        ))
        conn.commit()



def fetch_responses():
    sql = """
        SELECT ts, user_id, figure, choice, correct_choice, is_correct
        FROM responses
        ORDER BY ts DESC
    """
    with get_conn() as conn:
        if DATABASE_URL:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()


# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = APP_SECRET


def list_figures():
    if not FIG_DIR.exists():
        return []
    return sorted(p.name for p in FIG_DIR.iterdir() if p.suffix.lower() == ".png")


@app.route("/figures/<path:filename>")
def figures(filename):
    from flask import send_from_directory
    return send_from_directory(FIG_DIR, filename)


@app.route("/")
def home():
    return render_template("home.html", n=len(list_figures()))


@app.route("/start", methods=["POST"])
def start():
    session["user_id"] = os.urandom(8).hex()
    session["idx"] = 0
    return redirect(url_for("survey"))


@app.route("/survey", methods=["GET", "POST"])
def survey():
    figs = list_figures()
    idx  = session.get("idx", 0)

    if idx >= len(figs):
        return redirect(url_for("complete"))

    fig_name = figs[idx]
    q = QUESTIONS.get(fig_name, DEFAULT_QUESTION)

    if request.method == "POST":
        choice  = request.form.get("choice", "")
        correct = q.get("correct")
        is_correct = None if correct is None else int(choice == correct)

        insert_response(
            user_id=session.get("user_id", "unknown"),
            figure=fig_name,
            question=q["prompt"],
            choice=choice,
            correct_choice=correct,
            is_correct=is_correct,
        )
        session["idx"] = idx + 1
        return redirect(url_for("survey"))

    pct = int(idx / len(figs) * 100)
    return render_template("survey.html", fig=fig_name, q=q,
                           idx=idx, n=len(figs), pct=pct)


@app.route("/complete")
def complete():
    return render_template("complete.html")


@app.route("/stats")
def stats():
    figures = list_figures()

    # Pivot raw responses into one row per participant, one column per figure
    raw = fetch_responses()
    user_answers = {}   # {user_id: {figure: choice}}
    user_first_ts = {}  # {user_id: earliest ts} for row ordering
    for r in raw:
        uid = r["user_id"]
        if uid not in user_answers:
            user_answers[uid] = {}
            user_first_ts[uid] = r["ts"]
        user_answers[uid][r["figure"]] = r["choice"]

    pivot = [
        {
            "user_id": uid[:8],
            "ts": user_first_ts[uid][:19].replace("T", " "),
            "answers": [user_answers[uid].get(fig, "—") for fig in figures],
        }
        for uid in sorted(user_answers, key=lambda u: user_first_ts[u])
    ]

    return render_template("stats.html", figures=figures, pivot=pivot)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8080)
