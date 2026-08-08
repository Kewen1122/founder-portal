from werkzeug.security import generate_password_hash
import sqlite3

DB_NAME = "founder.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    db = get_db()
    c = db.cursor()

    # Benutzer
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Kunden
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        contact TEXT,
        email TEXT,
        phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Software-Produkte
    c.execute("""
    CREATE TABLE IF NOT EXISTS software_products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        edition TEXT NOT NULL,
        current_version TEXT,
        price REAL DEFAULT 0,
        description TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Lizenzen
    c.execute("""
    CREATE TABLE IF NOT EXISTS licenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        license_id TEXT UNIQUE,
        license_type TEXT NOT NULL,
        issued_at TEXT,
        valid_until TEXT,
        max_users INTEGER,
        features_json TEXT,
        payload_json TEXT,
        license_key TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(product_id) REFERENCES software_products(id)
    )
    """)

    # Rechnungen
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER NOT NULL,
        invoice_date TEXT,
        due_date TEXT,
        subtotal REAL DEFAULT 0,
        vat REAL DEFAULT 0,
        total REAL DEFAULT 0,
        status TEXT DEFAULT 'open',
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)

    # Rechnungspositionen
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        description TEXT,
        quantity INTEGER,
        unit_price REAL,
        total REAL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """)


   # Firmeneinstellungen
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        owner TEXT,
        street TEXT,
        zip TEXT,
        city TEXT,
        email TEXT,
        phone TEXT,
        website TEXT,
        vat_id TEXT,
        iban TEXT,
        bic TEXT,
        logo TEXT

    )
    """)


    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:

        c.execute("""
        INSERT INTO settings(
        id,
        company_name
    )
    VALUES(1,?)
    """, (
        "Meine Softwarefirma",
    ))

    # Standardbenutzer
    c.execute("SELECT COUNT(*) FROM users")

    if c.fetchone()[0] == 0:

        c.execute("""
        INSERT INTO users(
            username,
            password,
            role
        )
        VALUES(?,?,?)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "founder"
        ))

    db.commit()
    db.close()
