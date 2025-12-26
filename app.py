from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "research_db_cambodia"

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- PUBLIC ----------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/researchers")
def researchers():
    q = request.args.get("q", "")
    db = get_db()

    if q:
        researchers = db.execute("""
            SELECT * FROM researchers
            WHERE name LIKE ? OR field LIKE ? OR institution LIKE ?
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        researchers = db.execute("SELECT * FROM researchers").fetchall()

    data = []
    for r in researchers:
        profiles = db.execute(
            "SELECT platform, url FROM research_profiles WHERE researcher_id=?",
            (r["id"],)
        ).fetchall()
        # Convert sqlite3.Row to dict for easier access in Jinja
        data.append({"r": dict(r), "profiles": [dict(p) for p in profiles]})

    db.close()
    return render_template("researchers.html", data=data, q=q)

# ---------------- AUTH ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ADMIN ----------------

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()
    researchers = db.execute("SELECT * FROM researchers").fetchall()

    data = []
    for r in researchers:
        profiles = db.execute(
            "SELECT platform, url FROM research_profiles WHERE researcher_id=?",
            (r["id"],)
        ).fetchall()
        data.append({"r": r, "profiles": profiles})

    db.close()
    return render_template("admin.html", data=data)

# ---------------- ADD ----------------

@app.route("/add", methods=["GET", "POST"])
def add():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        db = get_db()

        file = request.files.get("photo")
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cur = db.execute("""
            INSERT INTO researchers
            (name, field, institution, email, bio, citation_count, publication_count, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["field"],
            request.form["institution"],
            request.form["email"],
            request.form["bio"],
            request.form["citation_count"] or 0,
            request.form["publication_count"] or 0,
            filename
        ))

        researcher_id = cur.lastrowid

        platforms = request.form.getlist("profile_platform[]")
        urls = request.form.getlist("profile_url[]")

        for p, u in zip(platforms, urls):
            if p and u:
                db.execute("""
                    INSERT INTO research_profiles (researcher_id, platform, url)
                    VALUES (?, ?, ?)
                """, (researcher_id, p.strip(), u.strip()))

        db.commit()
        db.close()
        return redirect("/admin")

    return render_template("add.html")

# ---------------- EDIT ----------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()
    researcher = db.execute("SELECT * FROM researchers WHERE id=?", (id,)).fetchone()
    profiles = db.execute(
        "SELECT platform, url FROM research_profiles WHERE researcher_id=?", (id,)
    ).fetchall()

    if request.method == "POST":
        file = request.files.get("photo")
        filename = researcher["photo"]  # keep old if no new file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute("""
            UPDATE researchers SET
            name=?, field=?, institution=?, email=?, bio=?,
            citation_count=?, publication_count=?, photo=?
            WHERE id=?
        """, (
            request.form["name"], request.form["field"], request.form["institution"],
            request.form["email"], request.form["bio"],
            request.form["citation_count"] or 0,
            request.form["publication_count"] or 0,
            filename, id
        ))

        # Update profiles
        db.execute("DELETE FROM research_profiles WHERE researcher_id=?", (id,))
        platforms = request.form.getlist("profile_platform[]")
        urls = request.form.getlist("profile_url[]")
        for p, u in zip(platforms, urls):
            if p and u:
                db.execute("""
                    INSERT INTO research_profiles (researcher_id, platform, url)
                    VALUES (?, ?, ?)
                """, (id, p.strip(), u.strip()))

        db.commit()
        db.close()
        return redirect("/admin")

    db.close()
    return render_template("edit.html", r=researcher, profiles=profiles)

# ---------------- DELETE ----------------

@app.route("/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()
    db.execute("DELETE FROM researchers WHERE id=?", (id,))
    db.execute("DELETE FROM research_profiles WHERE researcher_id=?", (id,))
    db.commit()
    db.close()
    return redirect("/admin")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
