from flask import Blueprint, render_template, request

from database import get_db
from routes.auth import founder_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/audit-log")
@founder_required
def audit_log():

    db = get_db()

    username = request.args.get("username", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    where = []
    params = []
    if username:
        where.append("username=?")
        params.append(username)
    if date_from:
        where.append("date(created_at)>=?")
        params.append(date_from)
    if date_to:
        where.append("date(created_at)<=?")
        params.append(date_to)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    logs = db.execute(f"""
        SELECT * FROM activity_log
        {where_sql}
        ORDER BY id DESC
        LIMIT 250
    """, params).fetchall()

    usernames = db.execute("""
        SELECT DISTINCT username FROM activity_log
        WHERE username IS NOT NULL
        ORDER BY username
    """).fetchall()

    db.close()

    return render_template(
        "audit_log.html",
        logs=logs,
        usernames=[u["username"] for u in usernames],
        username=username,
        date_from=date_from,
        date_to=date_to,
    )
