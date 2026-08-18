from datetime import datetime

from flask import request, session

from database import get_db


def log_action(action, details=""):
    try:
        db = get_db()
        db.execute(
            "INSERT INTO activity_log(user_id,username,action,details,ip,created_at) VALUES(?,?,?,?,?,?)",
            (
                session.get("user_id"),
                session.get("username"),
                action,
                details,
                request.remote_addr,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        db.commit()
        db.close()
    except Exception:
        pass
