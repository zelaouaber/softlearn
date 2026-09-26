import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"
conn = sqlite3.connect(DB_PATH)

try:
    conn.execute("ALTER TABLE soumissions ADD COLUMN details TEXT")
    print("[OK] Colonne 'details' ajoutee a soumissions.")
except sqlite3.OperationalError:
    print("[INFO] Colonne 'details' existe deja.")

conn.commit()
conn.close()