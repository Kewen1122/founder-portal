from database import init_db
from database import get_db
from flask import Flask, render_template, session, redirect
from routes.auth import auth_bp
from routes.licenses import licenses_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.license_generator import generator_bp
from routes.invoices import invoices_bp
from routes.settings import settings_bp

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

app.register_blueprint(auth_bp)
app.register_blueprint(licenses_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(products_bp)
app.register_blueprint(generator_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(settings_bp)

@app.route("/")
def index():
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

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

    latest_customers = db.execute("""
        SELECT *
        FROM customers
        ORDER BY created_at DESC
        LIMIT 5
    """).fetchall()

    latest_licenses = db.execute("""
        SELECT
            licenses.*,
            customers.company
        FROM licenses
        JOIN customers
        ON customers.id = licenses.customer_id
        ORDER BY licenses.created_at DESC
        LIMIT 5
    """).fetchall()

    db.close()

    return render_template(
        "dashboard.html",
        customer_count=customer_count,
        product_count=product_count,
        active_license_count=active_license_count,
        revoked_license_count=revoked_license_count,
        latest_customers=latest_customers,
        latest_licenses=latest_licenses
    )

if __name__ == "__main__":
    init_db()
    app.run(port=5050, debug=True)
