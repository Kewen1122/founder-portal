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

    db.close()

    return render_template(
        "customer_detail.html",
        customer=customer
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
                phone
            )
            VALUES(?,?,?,?)
        """, (
            request.form["company"],
            request.form["contact"],
            request.form["email"],
            request.form["phone"]
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
                phone=?
            WHERE id=?
        """, (
            request.form["company"],
            request.form["contact"],
            request.form["email"],
            request.form["phone"],
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


@customers_bp.route("/customers/delete/<int:id>")
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
