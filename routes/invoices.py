from datetime import date

from flask import Blueprint, render_template, request, send_file, flash, redirect

from database import get_db
from routes.auth import login_required
from utils import log_action
from services.pdf_service import create_invoice_pdf

invoices_bp = Blueprint("invoices", __name__)


@invoices_bp.route("/invoices")
@login_required
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
        invoices=invoices,
        now=date.today().isoformat(),
    )


@invoices_bp.route("/invoices/<int:id>")
@login_required
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


@invoices_bp.route("/invoices/<int:id>/mark-paid", methods=["POST"])
@login_required
def mark_paid(id):

    db = get_db()

    invoice = db.execute(
        "SELECT id, invoice_number FROM invoices WHERE id=?", (id,)
    ).fetchone()

    if invoice is None:
        db.close()
        flash("Rechnung nicht gefunden.", "danger")
        return redirect("/invoices")

    db.execute("UPDATE invoices SET status='paid' WHERE id=?", (id,))
    db.commit()
    db.close()

    log_action("Rechnung als bezahlt markiert", invoice["invoice_number"])
    flash("Rechnung wurde als bezahlt markiert.", "success")

    return redirect(request.form.get("next") or "/invoices")


@invoices_bp.route("/invoices/pdf/<int:id>")
@login_required
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
