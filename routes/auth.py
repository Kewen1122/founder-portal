from functools import wraps
from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db
from extensions import limiter
from utils import log_action
from totp import generate_secret, verify_code, qr_code_data_uri

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
@limiter.limit("10 per minute", methods=["POST"])
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

            if user["totp_secret"]:
                session["pending_2fa_user_id"] = user["id"]
                return redirect("/login/2fa")

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            log_action("Login")
            return redirect("/dashboard")

        flash("Benutzername oder Passwort falsch.", "danger")

    return render_template("login.html")


@auth_bp.route("/login/2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login_2fa():
    pending_id = session.get("pending_2fa_user_id")
    if not pending_id:
        return redirect("/login")

    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (pending_id,)).fetchone()
        db.close()

        if user and verify_code(user["totp_secret"], request.form.get("code", "")):
            session.pop("pending_2fa_user_id", None)
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            log_action("Login (2FA bestätigt)")
            return redirect("/dashboard")

        flash("Code ist falsch oder abgelaufen.", "danger")

    return render_template("login_2fa.html")


@auth_bp.route("/logout")
def logout():
    if "user_id" in session:
        log_action("Logout")
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

        log_action("Eigenes Passwort geändert")
        flash("Passwort wurde geändert.", "success")
        return redirect("/dashboard")

    db = get_db()
    user = db.execute("SELECT totp_secret FROM users WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return render_template("change_password.html", totp_enabled=bool(user["totp_secret"]))


@auth_bp.route("/2fa/setup", methods=["GET", "POST"])
@login_required
def setup_2fa():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

    if user["totp_secret"]:
        db.close()
        flash("Zwei-Faktor-Authentifizierung ist bereits aktiv.", "danger")
        return redirect("/change-password")

    if request.method == "POST":
        secret = session.get("pending_totp_secret")
        if secret and verify_code(secret, request.form.get("code", "")):
            db.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, user["id"]))
            db.commit()
            db.close()
            session.pop("pending_totp_secret", None)
            log_action("2FA aktiviert")
            flash("Zwei-Faktor-Authentifizierung wurde aktiviert.", "success")
            return redirect("/change-password")

        db.close()
        flash("Code stimmt nicht mit dem angezeigten Schlüssel überein. Bitte erneut versuchen.", "danger")
        return redirect("/2fa/setup")

    secret = session.get("pending_totp_secret")
    if not secret:
        secret = generate_secret()
        session["pending_totp_secret"] = secret
    db.close()
    qr = qr_code_data_uri(secret, user["username"])
    return render_template("two_factor_setup.html", secret=secret, qr=qr)


@auth_bp.route("/2fa/disable", methods=["POST"])
@login_required
def disable_2fa():
    password = request.form.get("password", "")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

    if not user or not check_password_hash(user["password"], password):
        db.close()
        flash("Passwort ist falsch.", "danger")
        return redirect("/change-password")

    db.execute("UPDATE users SET totp_secret=NULL WHERE id=?", (user["id"],))
    db.commit()
    db.close()
    log_action("2FA deaktiviert")
    flash("Zwei-Faktor-Authentifizierung wurde deaktiviert.", "success")
    return redirect("/change-password")
