from flask import Blueprint, render_template, request, redirect, flash
from database import get_db
from routes.auth import login_required

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers")
@login_required
def customers():

    db = get_db()

    customers = db.execute(
        "SELECT * FROM customers ORDER BY company"
    ).fetchall()

    db.close()

    return render_template("customers.html", customers=customers)


@customers_bp.route("/customers/<int:id>")
@login_required
def customer_detail(id):

    db = get_db()

    customer = db.execute(
        "SELECT * FROM customers WHERE id=?",
        (id,)
    ).fetchone()

    licenses = db.execute("""
        SELECT
            licenses.*,
            software_products.name AS product_name,
            software_products.edition AS product_edition,
            software_products.price AS product_price
        FROM licenses
        JOIN software_products ON software_products.id = licenses.product_id
        WHERE licenses.customer_id=?
        ORDER BY licenses.created_at DESC
    """, (id,)).fetchall()

    invoices = db.execute("""
        SELECT * FROM invoices
        WHERE customer_id=?
        ORDER BY created_at DESC
    """, (id,)).fetchall()

    total_revenue = db.execute("""
        SELECT COALESCE(SUM(total), 0) FROM invoices
        WHERE customer_id=?
    """, (id,)).fetchone()[0]

    db.close()

    return render_template(
        "customer_detail.html",
        customer=customer,
        licenses=licenses,
        invoices=invoices,
        total_revenue=total_revenue
    )


@customers_bp.route("/customers/new", methods=["GET", "POST"])
@login_required
def new_customer():

    if request.method == "POST":

        db = get_db()

        db.execute("""
            INSERT INTO customers(
                company,
                contact,
                email,
                phone,
                instance_url
            )
            VALUES(?,?,?,?,?)
        """, (
            request.form["company"],
            request.form["contact"],
            request.form["email"],
            request.form["phone"],
            request.form.get("instance_url", "")
        ))

        db.commit()
        db.close()

        flash("Kunde wurde angelegt.")

        return redirect("/customers")

    return render_template(
        "customer_form.html",
        customer=None
    )


@customers_bp.route("/customers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_customer(id):

    db = get_db()

    if request.method == "POST":

        db.execute("""
            UPDATE customers
            SET
                company=?,
                contact=?,
                email=?,
                phone=?,
                instance_url=?
            WHERE id=?
        """, (
            request.form["company"],
            request.form["contact"],
            request.form["email"],
            request.form["phone"],
            request.form.get("instance_url", ""),
            id
        ))

        db.commit()
        db.close()

        flash("Kunde gespeichert.")

        return redirect("/customers")

    customer = db.execute(
        "SELECT * FROM customers WHERE id=?",
        (id,)
    ).fetchone()

    db.close()

    return render_template(
        "customer_form.html",
        customer=customer
    )


@customers_bp.route("/customers/delete/<int:id>", methods=["POST"])
@login_required
def delete_customer(id):

    db = get_db()

    db.execute(
        "DELETE FROM customers WHERE id=?",
        (id,)
    )

    db.commit()
    db.close()

    flash("Kunde gelöscht.")

    return redirect("/customers")
