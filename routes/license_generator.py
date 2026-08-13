from flask import Blueprint, render_template
from database import get_db
from routes.auth import login_required

generator_bp = Blueprint("generator", __name__)


@generator_bp.route("/licenses/new")
@login_required
def new_license():

    db = get_db()

    customers = db.execute("""
        SELECT *
        FROM customers
        ORDER BY company
    """).fetchall()

    products = db.execute("""
        SELECT *
        FROM software_products
        WHERE status='active'
        ORDER BY name
    """).fetchall()

    db.close()

    return render_template(
        "license_generator.html",
        customers=customers,
        products=products
    )
