from flask import Blueprint, render_template, send_file, flash, redirect

from database import get_db
from services.pdf_service import create_invoice_pdf

invoices_bp = Blueprint("invoices", __name__)


@invoices_bp.route("/invoices")
def invoices():

    db = get_db()

    invoices = db.execute("""
        SELECT
            invoices.*,
            customers.company
        FROM invoices
        JOIN customers
            ON customers.id = invoices.customer_id
        ORDER BY invoices.created_at DESC
    """).fetchall()

    db.close()

    return render_template(
        "invoices.html",
        invoices=invoices
    )


@invoices_bp.route("/invoices/<int:id>")
def invoice_detail(id):

    db = get_db()

    invoice = db.execute("""
        SELECT
            invoices.*,
            customers.company,
            customers.contact,
            customers.email,
            customers.phone
        FROM invoices
        JOIN customers
            ON customers.id = invoices.customer_id
        WHERE invoices.id=?
    """, (id,)).fetchone()

    items = db.execute("""
        SELECT *
        FROM invoice_items
        WHERE invoice_id=?
    """, (id,)).fetchall()

    db.close()

    if invoice is None:
        flash("Rechnung nicht gefunden.", "danger")
        return redirect("/invoices")

    return render_template(
        "invoice_detail.html",
        invoice=invoice,
        items=items
    )


@invoices_bp.route("/invoices/pdf/<int:id>")
def invoice_pdf(id):

    db = get_db()

    invoice = db.execute("""
        SELECT
            invoices.*,
            customers.*
        FROM invoices
        JOIN customers
            ON customers.id=invoices.customer_id
        WHERE invoices.id=?
    """, (id,)).fetchone()

    db.close()

    if invoice is None:
        flash("Rechnung nicht gefunden.", "danger")
        return redirect("/invoices")

    pdf = create_invoice_pdf(
        invoice=invoice,
        customer=invoice
    )

    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"{invoice['invoice_number']}.pdf"
    )
