from flask import Blueprint, render_template

from database import get_db
from routes.auth import founder_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/audit-log")
@founder_required
def audit_log():

    db = get_db()

    logs = db.execute("""
        SELECT * FROM activity_log
        ORDER BY id DESC
        LIMIT 250
    """).fetchall()

    db.close()

    return render_template("audit_log.html", logs=logs)
