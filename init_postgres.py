# =========================================================
# INITIALISATION POSTGRESQL (a lancer UNE SEULE FOIS sur Render)
# =========================================================

import os
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    print("[ERREUR] DATABASE_URL non definie.")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# =========================================================
# SCHEMA
# =========================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    telephone TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'trainer', 'admin')),
    statut_validation TEXT DEFAULT 'approved',
    diplome TEXT,
    cv TEXT,
    diplome_file TEXT,
    experience TEXT,
    motif_refus TEXT,
    date_validation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS formations (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    description TEXT,
    categorie TEXT DEFAULT 'data',
    plateforme_defaut TEXT,
    trainer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS niveaux (
    id SERIAL PRIMARY KEY,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    prix REAL NOT NULL DEFAULT 0,
    UNIQUE(formation_id, numero)
);

CREATE TABLE IF NOT EXISTS inscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    progression INTEGER DEFAULT 0,
    statut TEXT DEFAULT 'inactive',
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_completion TIMESTAMP,
    UNIQUE(user_id, niveau_id)
);

CREATE TABLE IF NOT EXISTS paiements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    montant REAL NOT NULL,
    statut TEXT DEFAULT 'pending',
    reference TEXT,
    date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chapitres (
    id SERIAL PRIMARY KEY,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(niveau_id, numero)
);

CREATE TABLE IF NOT EXISTS lecons (
    id SERIAL PRIMARY KEY,
    chapitre_id INTEGER NOT NULL REFERENCES chapitres(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    contenu TEXT,
    duree INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapitre_id, numero)
);

CREATE TABLE IF NOT EXISTS progressions_lecons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lecon_id INTEGER NOT NULL REFERENCES lecons(id) ON DELETE CASCADE,
    termine INTEGER DEFAULT 0,
    date_termine TIMESTAMP,
    UNIQUE(user_id, lecon_id)
);

CREATE TABLE IF NOT EXISTS exercices (
    id SERIAL PRIMARY KEY,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'texte',
    langage TEXT,
    contenu TEXT,
    reponse_attendue TEXT,
    qcm_data TEXT,
    plateforme_url TEXT,
    corrige_auto INTEGER DEFAULT 0,
    lecon_id INTEGER,
    est_evaluation_finale INTEGER DEFAULT 0,
    partie TEXT DEFAULT 'principal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS soumissions (
    id SERIAL PRIMARY KEY,
    exercice_id INTEGER NOT NULL REFERENCES exercices(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contenu TEXT,
    note REAL,
    commentaire TEXT,
    note_ia REAL,
    commentaire_ia TEXT,
    date_correction_ia TIMESTAMP,
    details TEXT,
    statut TEXT DEFAULT 'submitted',
    date_soumission TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pretests (
    id SERIAL PRIMARY KEY,
    niveau_id INTEGER NOT NULL UNIQUE REFERENCES niveaux(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    description TEXT,
    seuil_reussite INTEGER DEFAULT 70,
    duree_minutes INTEGER DEFAULT 30,
    qcm_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS soumissions_pretest (
    id SERIAL PRIMARY KEY,
    pretest_id INTEGER NOT NULL REFERENCES pretests(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    reponses TEXT,
    score INTEGER,
    reussi INTEGER DEFAULT 0,
    date_passage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS certificats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    numero_certificat TEXT UNIQUE NOT NULL,
    score_obtenu REAL NOT NULL,
    score_total REAL NOT NULL,
    pourcentage REAL NOT NULL,
    date_obtention TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, niveau_id)
);

CREATE TABLE IF NOT EXISTS progressions_etudiant (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    niveau_actuel_id INTEGER,
    niveaux_completes TEXT DEFAULT '[]',
    pourcentage_global INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, formation_id)
);
""")

conn.commit()

# =========================================================
# ADMIN PAR DEFAUT
# =========================================================

cur.execute("SELECT id FROM users WHERE email = %s",
            ("admin@softlearn.com",))
if not cur.fetchone():
    cur.execute("""
        INSERT INTO users(nom, prenom, email, password, role, statut_validation)
        VALUES (%s, %s, %s, %s, 'admin', 'approved')
    """, ("Admin", "Soft Learn", "admin@softlearn.com",
          generate_password_hash("admin123")))
    print("[OK] Admin cree : admin@softlearn.com / admin123")

# =========================================================
# FORMATEUR DEMO
# =========================================================

cur.execute("SELECT id FROM users WHERE email = %s",
            ("trainer@softlearn.com",))
trainer = cur.fetchone()
if not trainer:
    cur.execute("""
        INSERT INTO users(nom, prenom, email, password, role,
                          statut_validation, diplome, experience)
        VALUES (%s, %s, %s, %s, 'trainer', 'approved', %s, %s)
    """, ("Formateur", "Demo", "trainer@softlearn.com",
          generate_password_hash("trainer123"),
          "Master en Informatique",
          "5 ans d'experience en formation."))
    print("[OK] Formateur cree : trainer@softlearn.com / trainer123")

conn.commit()
cur.close()
conn.close()

print("[OK] Base PostgreSQL initialisee avec succes.")