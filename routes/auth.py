from functools import wraps
from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db

auth_bp = Blueprint("auth", __name__)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return fn(*args, **kwargs)
    return wrapper


def founder_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        if session.get("role") != "founder":
            flash("Nur Founder dürfen diese Seite öffnen.", "danger")
            return redirect("/dashboard")
        return fn(*args, **kwargs)
    return wrapper


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        db.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect("/dashboard")

        flash("Benutzername oder Passwort falsch.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        current = request.form.get("current_password", "")
        pw1 = request.form.get("password", "")
        pw2 = request.form.get("password2", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if not user or not check_password_hash(user["password"], current):
            db.close()
            flash("Aktuelles Passwort ist falsch.", "danger")
            return redirect("/change-password")

        if len(pw1) < 8:
            db.close()
            flash("Das neue Passwort muss mindestens 8 Zeichen haben.", "danger")
            return redirect("/change-password")

        if pw1 != pw2:
            db.close()
            flash("Die neuen Passwörter stimmen nicht überein.", "danger")
            return redirect("/change-password")

        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (generate_password_hash(pw1), session["user_id"])
        )
        db.commit()
        db.close()

        flash("Passwort wurde geändert.", "success")
        return redirect("/dashboard")

    return render_template("change_password.html")
