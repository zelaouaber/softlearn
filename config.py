import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# =========================================================
# BASE DE DONNEES
# =========================================================

# Render fournit DATABASE_URL automatiquement
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# PostgreSQL sur Render utilise "postgres://" mais psycopg2 attend "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Si pas de DATABASE_URL (dev local), on utilise SQLite
USE_POSTGRES = bool(DATABASE_URL)

SQLITE_PATH = BASE_DIR / "database.db"

# =========================================================
# UPLOADS & CERTIFICATS
# =========================================================

UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

CERTIFICATES_FOLDER = BASE_DIR / "static" / "certificates"
CERTIFICATES_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}

# =========================================================
# SECURITE
# =========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "softlearn-change-this-secret-key"
)

# =========================================================
# IMAGES STATIQUES
# =========================================================

LOGO_PATH = BASE_DIR / "static" / "images" / "logo.jpg"