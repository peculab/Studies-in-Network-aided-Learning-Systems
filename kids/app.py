from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "data.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            activity_mode TEXT NOT NULL,   -- heard / joined
            activity_name TEXT NOT NULL,
            context TEXT NOT NULL,         -- home / school / outdoor / other
            response_type TEXT NOT NULL,
            intensity INTEGER NOT NULL,    -- 1-5
            emotion TEXT NOT NULL,         -- positive / neutral / negative
            duration_sec INTEGER,
            notes TEXT
        )
        """)
        conn.commit()

def query(sql, params=()):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    return rows

def execute(sql, params=()):
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()

@app.route("/")
def index():
    rows = query("SELECT * FROM logs ORDER BY datetime(created_at) DESC LIMIT 20")
    return render_template("index.html", rows=rows)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        created_at = datetime.now().isoformat(timespec="seconds")
        activity_mode = request.form["activity_mode"]
        activity_name = request.form["activity_name"].strip()
        context = request.form["context"]
        response_type = request.form["response_type"]
        intensity = int(request.form["intensity"])
        emotion = request.form["emotion"]
        duration_sec = request.form.get("duration_sec", "").strip()
        duration_sec = int(duration_sec) if duration_sec else None
        notes = request.form.get("notes", "").strip()

        execute("""
        INSERT INTO logs (created_at, activity_mode, activity_name, context, response_type,
                          intensity, emotion, duration_sec, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (created_at, activity_mode, activity_name, context, response_type,
              intensity, emotion, duration_sec, notes))

        return redirect(url_for("index"))

    return render_template("add.html")

@app.route("/dashboard")
def dashboard():
    # 近 30 天趨勢（每日筆數）
    since = (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds")
    daily = query("""
        SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS cnt
        FROM logs
        WHERE datetime(created_at) >= datetime(?)
        GROUP BY day
        ORDER BY day
    """, (since,))

    # 反應類別分佈
    resp = query("""
        SELECT response_type, COUNT(*) AS cnt
        FROM logs
        GROUP BY response_type
        ORDER BY cnt DESC
    """)

    # 觸發活動 Top
    act = query("""
        SELECT activity_name, COUNT(*) AS cnt
        FROM logs
        GROUP BY activity_name
        ORDER BY cnt DESC
        LIMIT 10
    """)

    # 情緒比例
    emo = query("""
        SELECT emotion, COUNT(*) AS cnt
        FROM logs
        GROUP BY emotion
    """)

    return render_template(
        "dashboard.html",
        daily=daily,
        resp=resp,
        act=act,
        emo=emo
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)