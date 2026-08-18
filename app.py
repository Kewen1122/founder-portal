from datetime import date, timedelta

from database import init_db
from database import get_db
from extensions import csrf, limiter
from flask import Flask, render_template, session, redirect, jsonify
from routes.auth import auth_bp, login_required
from routes.licenses import licenses_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.invoices import invoices_bp
from routes.settings import settings_bp
from routes.users import users_bp
from routes.audit import audit_bp

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
csrf.init_app(app)
limiter.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(licenses_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(products_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(users_bp)
app.register_blueprint(audit_bp)

init_db()

@app.route("/")
def index():
    return redirect("/dashboard")

@app.route("/healthz")
def healthz():
    try:
        db = get_db()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        return jsonify(status="error", detail=str(e)), 503
    return jsonify(status="ok"), 200

@app.route("/dashboard")
@login_required
def dashboard():

    db = get_db()

    customer_count = db.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    product_count = db.execute(
        "SELECT COUNT(*) FROM software_products"
    ).fetchone()[0]

    active_license_count = db.execute(
        "SELECT COUNT(*) FROM licenses WHERE status='active'"
    ).fetchone()[0]

    revoked_license_count = db.execute(
        "SELECT COUNT(*) FROM licenses WHERE status='revoked'"
    ).fetchone()[0]

    expiring_licenses = db.execute("""
        SELECT
            licenses.*,
            customers.company
        FROM licenses
        JOIN customers
        ON customers.id = licenses.customer_id
        WHERE licenses.status = 'active'
        AND licenses.valid_until IS NOT NULL
        AND licenses.valid_until <= date('now', '+30 days')
        ORDER BY licenses.valid_until ASC
    """).fetchall()

    overdue_invoices = db.execute("""
        SELECT
            invoices.*,
            customers.company
        FROM invoices
        JOIN customers
        ON customers.id = invoices.customer_id
        WHERE invoices.status = 'open'
        AND invoices.due_date < date('now')
        ORDER BY invoices.due_date ASC
    """).fetchall()

    db.close()

    return render_template(
        "dashboard.html",
        customer_count=customer_count,
        product_count=product_count,
        active_license_count=active_license_count,
        revoked_license_count=revoked_license_count,
        expiring_licenses=expiring_licenses,
        overdue_invoices=overdue_invoices,
        urgent_cutoff=(date.today() + timedelta(days=7)).isoformat(),
    )

if __name__ == "__main__":
    app.run(port=5050, debug=os.environ.get("FLASK_DEBUG") == "1")
