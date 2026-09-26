# =========================================================
# SOFT LEARN — PEUPLEMENT DE LA BASE POSTGRESQL
# Insere les 8 formations, 24 niveaux, cours, exos, pre-tests
# =========================================================

import os
import json
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
# UTILISATEURS
# =========================================================

# Admin
cur.execute("SELECT id FROM users WHERE email = %s", ("admin@softlearn.com",))
admin = cur.fetchone()
if not admin:
    cur.execute("""
        INSERT INTO users(nom, prenom, email, password, role, statut_validation)
        VALUES (%s, %s, %s, %s, 'admin', 'approved')
        RETURNING id
    """, ("Admin", "Soft Learn", "admin@softlearn.com",
          generate_password_hash("admin123")))
    admin_id = cur.fetchone()[0]
else:
    admin_id = admin[0]

# Formateur
cur.execute("SELECT id FROM users WHERE email = %s", ("trainer@softlearn.com",))
trainer = cur.fetchone()
if not trainer:
    cur.execute("""
        INSERT INTO users(nom, prenom, email, password, role,
                          statut_validation, diplome, experience)
        VALUES (%s, %s, %s, %s, 'trainer', 'approved', %s, %s)
        RETURNING id
    """, ("Formateur", "Demo", "trainer@softlearn.com",
          generate_password_hash("trainer123"),
          "Master en Informatique",
          "5 ans d'experience en formation."))
    trainer_id = cur.fetchone()[0]
else:
    trainer_id = trainer[0]

print(f"[OK] Admin ID = {admin_id}")
print(f"[OK] Trainer ID = {trainer_id}")

# =========================================================
# FORMATIONS + NIVEAUX
# =========================================================

formations_data = [
    {
        "nom": "Python",
        "description": "Apprentissage progressif de Python : des fondamentaux jusqu'aux projets IA.",
        "categorie": "programmation",
        "plateforme_defaut": "https://colab.research.google.com/",
        "niveaux": [
            {"numero": 1, "titre": "Python – Fondamentaux",
             "description": "Syntaxe, variables, conditions, boucles, fonctions.", "prix": 5000},
            {"numero": 2, "titre": "Python – Data Analysis",
             "description": "NumPy, Pandas, Matplotlib, nettoyage et analyse.", "prix": 8000},
            {"numero": 3, "titre": "Python – Avancé & IA",
             "description": "POO, Machine Learning, Scikit-learn, projets.", "prix": 10000},
        ]
    },
    {
        "nom": "SPSS",
        "description": "Analyse statistique avec SPSS.",
        "categorie": "data",
        "plateforme_defaut": None,
        "niveaux": [
            {"numero": 1, "titre": "SPSS – Initiation",
             "description": "Interface, donnees, statistiques descriptives.", "prix": 5000},
            {"numero": 2, "titre": "SPSS – Analyse statistique",
             "description": "Tests t, Khi2, ANOVA, regression.", "prix": 8000},
            {"numero": 3, "titre": "SPSS – Analyse avancee",
             "description": "Multivariee, projet complet.", "prix": 10000},
        ]
    },
    {
        "nom": "Bureautique",
        "description": "Word, Excel et PowerPoint jusqu'a l'automatisation VBA.",
        "categorie": "bureautique",
        "plateforme_defaut": None,
        "niveaux": [
            {"numero": 1, "titre": "Bureautique – Fondamentaux",
             "description": "Bases Word, Excel, PowerPoint.", "prix": 5000},
            {"numero": 2, "titre": "Bureautique – Intermediaire",
             "description": "Excel avance, TCD, formules.", "prix": 8000},
            {"numero": 3, "titre": "Bureautique – Automatisation",
             "description": "Macros VBA, dashboards.", "prix": 10000},
        ]
    },
    {
        "nom": "Intelligence Artificielle",
        "description": "IA, Machine Learning et Deep Learning.",
        "categorie": "data",
        "plateforme_defaut": "https://colab.research.google.com/",
        "niveaux": [
            {"numero": 1, "titre": "IA – Fondamentaux",
             "description": "Concepts IA, ML, premiers modeles.", "prix": 5000},
            {"numero": 2, "titre": "IA – Machine Learning",
             "description": "Regression, classification, Random Forest.", "prix": 8000},
            {"numero": 3, "titre": "IA – Deep Learning",
             "description": "CNN, Transfer Learning, projets.", "prix": 10000},
        ]
    },
    {
        "nom": "Developpement Web",
        "description": "HTML, CSS, JavaScript et Flask.",
        "categorie": "web",
        "plateforme_defaut": "https://codepen.io/pen/",
        "niveaux": [
            {"numero": 1, "titre": "Web – HTML & CSS",
             "description": "Structure, CSS, Flexbox, Grid.", "prix": 5000},
            {"numero": 2, "titre": "Web – JavaScript",
             "description": "DOM, evenements, validation.", "prix": 8000},
            {"numero": 3, "titre": "Web – Full Stack Flask",
             "description": "Flask, BDD, API, CRUD.", "prix": 10000},
        ]
    },
    {
        "nom": "C++",
        "description": "Programmation C++ des fondamentaux aux algorithmes.",
        "categorie": "programmation",
        "plateforme_defaut": "https://replit.com/languages/cpp",
        "niveaux": [
            {"numero": 1, "titre": "C++ – Fondamentaux",
             "description": "Syntaxe, variables, boucles.", "prix": 5000},
            {"numero": 2, "titre": "C++ – POO",
             "description": "Classes, heritage, polymorphisme.", "prix": 8000},
            {"numero": 3, "titre": "C++ – Algorithmes",
             "description": "Structures de donnees, pointeurs, STL.", "prix": 10000},
        ]
    },
    {
        "nom": "Java",
        "description": "Programmation Java des fondamentaux aux applications.",
        "categorie": "programmation",
        "plateforme_defaut": "https://replit.com/languages/java",
        "niveaux": [
            {"numero": 1, "titre": "Java – Fondamentaux",
             "description": "Syntaxe, variables, POO intro.", "prix": 5000},
            {"numero": 2, "titre": "Java – POO & Collections",
             "description": "Classes, heritage, collections.", "prix": 8000},
            {"numero": 3, "titre": "Java – Avance",
             "description": "JDBC, BDD, Spring.", "prix": 10000},
        ]
    },
    {
        "nom": "Data Analysis",
        "description": "Analyse de donnees d'Excel aux dashboards avances.",
        "categorie": "data",
        "plateforme_defaut": "https://www.kaggle.com/code",
        "niveaux": [
            {"numero": 1, "titre": "Data Analysis – Fondamentaux",
             "description": "Excel, stats descriptives.", "prix": 5000},
            {"numero": 2, "titre": "Data Analysis – Python",
             "description": "NumPy, Pandas, Matplotlib.", "prix": 8000},
            {"numero": 3, "titre": "Data Analysis – Avance",
             "description": "Analyse exploratoire, dashboards.", "prix": 10000},
        ]
    },
]

formations_ids = {}  # nom -> id
niveaux_ids = {}     # (formation_nom, numero) -> niveau_id

for f in formations_data:
    # Verifie si la formation existe deja
    cur.execute("SELECT id FROM formations WHERE nom = %s", (f["nom"],))
    existing = cur.fetchone()

    if existing:
        fid = existing[0]
    else:
        cur.execute("""
            INSERT INTO formations(nom, description, categorie, plateforme_defaut, trainer_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (f["nom"], f["description"], f["categorie"],
              f["plateforme_defaut"], trainer_id))
        fid = cur.fetchone()[0]

    formations_ids[f["nom"]] = fid
    print(f"[OK] Formation '{f['nom']}' ID = {fid}")

    for n in f["niveaux"]:
        cur.execute("""
            SELECT id FROM niveaux
            WHERE formation_id = %s AND numero = %s
        """, (fid, n["numero"]))
        existing_niv = cur.fetchone()

        if existing_niv:
            nid = existing_niv[0]
        else:
            cur.execute("""
                INSERT INTO niveaux(formation_id, numero, titre, description, prix)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (fid, n["numero"], n["titre"], n["description"], n["prix"]))
            nid = cur.fetchone()[0]

        niveaux_ids[(f["nom"], n["numero"])] = nid

    print(f"     -> {len(f['niveaux'])} niveaux crees")

conn.commit()

print()
print(f"[OK] {len(formations_ids)} formations inserees")
print(f"[OK] {len(niveaux_ids)} niveaux inseres")
print()
print("=" * 60)
print("PEUPLEMENT TERMINE")
print("=" * 60)

cur.close()
conn.close()