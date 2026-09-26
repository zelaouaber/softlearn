# =========================================================
# SOFT LEARN — TABLE CERTIFICATS
# =========================================================

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

conn.executescript("""
CREATE TABLE IF NOT EXISTS certificats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    niveau_id INTEGER NOT NULL,
    formation_id INTEGER NOT NULL,
    numero_certificat TEXT UNIQUE NOT NULL,
    score_obtenu REAL NOT NULL,
    score_total REAL NOT NULL,
    pourcentage REAL NOT NULL,
    date_obtention TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, niveau_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE,
    FOREIGN KEY(formation_id) REFERENCES formations(id) ON DELETE CASCADE
);
""")

conn.commit()
conn.close()

print("[OK] Table 'certificats' creee.")