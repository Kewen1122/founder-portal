from datetime import date, timedelta

from database import get_db


def next_invoice_number():
    db = get_db()

    year = date.today().year

    row = db.execute(
        """
        SELECT invoice_number
        FROM invoices
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        number = 1
    else:
        try:
            number = int(row["invoice_number"].split("-")[1]) + 1
        except Exception:
            number = 1

    db.close()

    return f"{year}-{number:06d}"


def create_invoice(customer_id, description, price):

    db = get_db()

    invoice_number = next_invoice_number()

    today = date.today()
    due = today + timedelta(days=14)

    vat = round(price * 0.19, 2)
    total = round(price + vat, 2)

    db.execute("""
        INSERT INTO invoices(
            invoice_number,
            customer_id,
            invoice_date,
            due_date,
            subtotal,
            vat,
            total,
            status
        )
        VALUES(?,?,?,?,?,?,?,?)
    """,(
        invoice_number,
        customer_id,
        today.isoformat(),
        due.isoformat(),
        price,
        vat,
        total,
        "open"
    ))

    invoice_id = db.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    db.execute("""
        INSERT INTO invoice_items(
            invoice_id,
            description,
            quantity,
            unit_price,
            total
        )
        VALUES(?,?,?,?,?)
    """,(
        invoice_id,
        description,
        1,
        price,
        price
    ))

    db.commit()
    db.close()

    return invoice_id
