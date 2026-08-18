import json

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    send_file,
)

from database import get_db
from routes.auth import login_required
from utils import log_action
from services.license_service import (
    create_license,
    list_licenses,
    get_license,
    revoke_license,
    get_license_file_path,
    LicenseServiceError,
)
from services.invoice_service import create_invoice

licenses_bp = Blueprint("licenses", __name__)


@licenses_bp.route("/licenses")
@login_required
def licenses():

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
        ORDER BY name, edition
    """).fetchall()

    db.close()

    return render_template(
        "licenses.html",
        customers=customers,
        products=products,
        licenses=list_licenses(),
    )


@licenses_bp.route("/licenses/new", methods=["POST"])
@login_required
def new_license():

    db = get_db()

    try:

        customer_id = int(request.form["customer_id"])
        product_id = int(request.form["product_id"])

        product = db.execute(
            """
            SELECT *
            FROM software_products
            WHERE id=?
            """,
            (product_id,)
        ).fetchone()

        if product is None:
            flash("Produkt nicht gefunden.", "danger")
            return redirect("/licenses")

        create_license(
            customer_id=customer_id,
            product_id=product_id,
            duration_key=request.form["duration"],
            max_users=int(request.form["max_users"]),
            features=request.form.getlist("features"),
            license_type=request.form["license_type"],
        )

        create_invoice(
            customer_id=customer_id,
            description=f"{product['name']} {product['edition']} Lizenz",
            price=float(product["price"]),
        )

        log_action("Lizenz erstellt", f"{product['name']} {product['edition']} fuer Kunde #{customer_id}")
        flash(
            "Lizenz und Rechnung wurden erfolgreich erstellt.",
            "success",
        )

    except LicenseServiceError as e:

        flash(str(e), "danger")

    finally:

        db.close()

    return redirect("/licenses")


@licenses_bp.route("/licenses/<int:id>")
@login_required
def license_detail(id):

    license = get_license(id)

    if not license:

        flash("Lizenz nicht gefunden.", "danger")
        return redirect("/licenses")

    try:
        features = json.loads(license["features_json"] or "[]")
    except ValueError:
        features = []

    return render_template(
        "license_detail.html",
        license=license,
        features=features,
    )


@licenses_bp.route("/licenses/download/<int:id>")
@login_required
def download_license(id):

    license = get_license(id)

    if not license:

        flash("Lizenz nicht gefunden.", "danger")
        return redirect("/licenses")

    path = get_license_file_path(
        license["license_id"]
    )

    return send_file(
        path,
        as_attachment=True,
        download_name=f"{license['company']}_{license['license_id']}.lic",
    )


@licenses_bp.route("/licenses/revoke/<int:id>", methods=["POST"])
@login_required
def revoke(id):

    license = get_license(id)
    revoke_license(id)

    log_action("Lizenz widerrufen", license["company"] if license else str(id))
    flash(
        "Lizenz wurde widerrufen.",
        "warning",
    )

    return redirect("/licenses")
