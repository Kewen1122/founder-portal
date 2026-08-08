from flask import Blueprint, render_template, request, redirect, flash
from database import get_db

products_bp = Blueprint("products", __name__)


@products_bp.route("/products")
def products():

    db = get_db()

    products = db.execute("""
        SELECT *
        FROM software_products
        ORDER BY name, edition
    """).fetchall()

    db.close()

    return render_template(
        "products.html",
        products=products
    )


@products_bp.route("/products/new", methods=["GET", "POST"])
def new_product():

    if request.method == "POST":

        db = get_db()

        db.execute("""
            INSERT INTO software_products(
                name,
                edition,
                current_version,
                price,
                description
            )
            VALUES(?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["edition"],
            request.form["current_version"],
            request.form["price"] or 0,
            request.form["description"]
        ))

        db.commit()
        db.close()

        flash("Produkt wurde angelegt.")

        return redirect("/products")

    return render_template(
        "product_form.html",
        product=None
    )


@products_bp.route("/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    db = get_db()

    if request.method == "POST":

        db.execute("""
            UPDATE software_products
            SET
                name=?,
                edition=?,
                current_version=?,
                price=?,
                description=?,
                status=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["edition"],
            request.form["current_version"],
            request.form["price"] or 0,
            request.form["description"],
            request.form["status"],
            id
        ))

        db.commit()
        db.close()

        flash("Produkt gespeichert.")

        return redirect("/products")

    product = db.execute(
        "SELECT * FROM software_products WHERE id=?",
        (id,)
    ).fetchone()

    db.close()

    return render_template(
        "product_form.html",
        product=product
    )


@products_bp.route("/products/delete/<int:id>")
def delete_product(id):

    db = get_db()

    db.execute(
        "DELETE FROM software_products WHERE id=?",
        (id,)
    )

    db.commit()
    db.close()

    flash("Produkt gelöscht.")

    return redirect("/products")
