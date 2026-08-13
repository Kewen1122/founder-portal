from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash

from database import get_db
from routes.auth import founder_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/users")
@founder_required
def users():

    db = get_db()

    users = db.execute(
        "SELECT * FROM users ORDER BY username"
    ).fetchall()

    db.close()

    return render_template("users.html", users=users)


@users_bp.route("/users/new", methods=["GET", "POST"])
@founder_required
def new_user():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form.get("role", "founder").strip() or "founder"

        if len(password) < 8:
            flash("Das Passwort muss mindestens 8 Zeichen haben.", "danger")
            return redirect("/users/new")

        db = get_db()

        try:
            db.execute(
                "INSERT INTO users(username, password, role) VALUES(?,?,?)",
                (username, generate_password_hash(password), role)
            )
            db.commit()
            flash("Benutzer wurde angelegt.", "success")
        except Exception:
            db.rollback()
            flash("Benutzername existiert bereits.", "danger")
        finally:
            db.close()

        return redirect("/users")

    return render_template("user_form.html")


@users_bp.route("/users/<int:id>/password", methods=["POST"])
@founder_required
def set_user_password(id):

    password = request.form.get("password", "")

    if len(password) < 8:
        flash("Das Passwort muss mindestens 8 Zeichen haben.", "danger")
        return redirect("/users")

    db = get_db()
    db.execute(
        "UPDATE users SET password=? WHERE id=?",
        (generate_password_hash(password), id)
    )
    db.commit()
    db.close()

    flash("Passwort wurde neu gesetzt.", "success")
    return redirect("/users")


@users_bp.route("/users/<int:id>/delete", methods=["POST"])
@founder_required
def delete_user(id):

    if id == session.get("user_id"):
        flash("Du kannst dich nicht selbst löschen.", "danger")
        return redirect("/users")

    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (id,))
    db.commit()
    db.close()

    flash("Benutzer gelöscht.", "success")
    return redirect("/users")
