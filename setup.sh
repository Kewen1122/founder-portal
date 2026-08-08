#!/bin/bash

echo "=========================================="
echo "  LagerOS Founder Portal Setup"
echo "=========================================="

echo ""
echo "📁 Erstelle Projektstruktur..."

mkdir -p templates
mkdir -p static/css
mkdir -p static/js
mkdir -p static/img
mkdir -p models
mkdir -p routes
mkdir -p services
mkdir -p utils
mkdir -p instance
mkdir -p migrations
mkdir -p uploads

echo "📄 Erstelle Dateien..."

touch app.py
touch config.py
touch database.py
touch extensions.py
touch README.md
touch requirements.txt
touch .env
touch .gitignore

touch models/__init__.py
touch models/user.py
touch models/customer.py
touch models/license.py
touch models/audit.py

touch routes/auth.py
touch routes/dashboard.py
touch routes/customers.py
touch routes/licenses.py
touch routes/settings.py

touch services/license_service.py
touch services/customer_service.py

touch utils/helpers.py

touch templates/base.html
touch templates/dashboard.html
touch templates/login.html
touch templates/customers.html
touch templates/licenses.html

touch static/css/style.css

echo "📝 Schreibe .gitignore..."

cat > .gitignore << EOF
venv/
.env
instance/
__pycache__/
*.pyc
*.db
.vscode/
.idea/
.DS_Store
EOF

echo "📦 Installiere Python-Pakete..."

pip install Flask Flask-Login Flask-WTF Flask-Limiter Flask-Talisman \
python-dotenv Flask-SQLAlchemy SQLAlchemy Flask-Migrate \
cryptography reportlab gunicorn

echo "📋 Speichere requirements.txt..."

pip freeze > requirements.txt

echo ""
echo "=========================================="
echo "✅ Founder Portal erfolgreich vorbereitet!"
echo "=========================================="
