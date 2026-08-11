from pathlib import Path

from database import get_db
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
)

EXPORT_DIR = Path("exports/invoices")
LOGO_DIR = Path("uploads/logos")


def get_company_settings():

    db = get_db()

    settings = db.execute(
        "SELECT * FROM settings WHERE id=1"
    ).fetchone()

    db.close()

    return settings


def create_invoice_pdf(invoice, customer):

    company = get_company_settings()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    filename = EXPORT_DIR / f"{invoice['invoice_number']}.pdf"

    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(str(filename))

    story = []

    # Logo
    if company["logo"]:

        logo_path = LOGO_DIR / company["logo"]

        if logo_path.exists():

            story.append(
                Image(
                    str(logo_path),
                    width=50 * mm,
                    height=20 * mm,
                )
            )

            story.append(Spacer(1, 5 * mm))

    # Firmendaten
    story.append(
        Paragraph(
            f"<b>{company['company_name']}</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            f"""
            {company['owner'] or ''}<br/>
            {company['street'] or ''}<br/>
            {company['zip'] or ''} {company['city'] or ''}<br/>
            {company['email'] or ''}<br/>
            {company['phone'] or ''}<br/>
            USt-ID: {company['vat_id'] or ''}<br/>
            IBAN: {company['iban'] or ''}<br/>
            BIC: {company['bic'] or ''}
            """,
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 10 * mm))

    story.append(
        Paragraph(
            f"<b>Rechnung:</b> {invoice['invoice_number']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Kunde:</b> {customer['company']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Rechnungsdatum:</b> {invoice['invoice_date']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Fällig:</b> {invoice['due_date']}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            f"Nettobetrag: {invoice['subtotal']:.2f} €",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"MwSt.: {invoice['vat']:.2f} €",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Gesamt: {invoice['total']:.2f} €</b>",
            styles["Heading2"],
        )
    )

    doc.build(story)

    return filename
