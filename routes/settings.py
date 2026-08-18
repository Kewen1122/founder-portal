from flask import Blueprint, render_template, request, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
import os

from database import get_db
from routes.auth import login_required
from utils import log_action


settings_bp = Blueprint("settings", __name__)

UPLOAD_FOLDER = "uploads/logos"


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    db = get_db()

    if request.method == "POST":

        logo_filename = None

        if "logo" in request.files:

            file = request.files["logo"]

            if file.filename:

                logo_filename = secure_filename(file.filename)

                os.makedirs(
                    UPLOAD_FOLDER,
                    exist_ok=True
                )

                file.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        logo_filename
                    )
                )


        db.execute("""
        UPDATE settings
        SET
            company_name=?,
            owner=?,
            street=?,
            zip=?,
            city=?,
            email=?,
            phone=?,
            website=?,
            vat_id=?,
            iban=?,
            bic=?,
            logo=COALESCE(?,logo)
        WHERE id=1
        """, (

            request.form["company_name"],
            request.form["owner"],
            request.form["street"],
            request.form["zip"],
            request.form["city"],
            request.form["email"],
            request.form["phone"],
            request.form["website"],
            request.form["vat_id"],
            request.form["iban"],
            request.form["bic"],
            logo_filename

        ))

        db.commit()

        log_action("Firmeneinstellungen geändert")
        flash(
            "Einstellungen gespeichert.",
            "success"
        )


    settings = db.execute(
        "SELECT * FROM settings WHERE id=1"
    ).fetchone()


    db.close()


    return render_template(
        "settings.html",
        settings=settings
    )


@settings_bp.route("/settings/logo/<path:filename>")
@login_required
def settings_logo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
