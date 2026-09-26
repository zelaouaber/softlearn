# =========================================================
# SOFT LEARN — INITIALISATION COMPLETE POSTGRESQL
# Un seul script = tables + users + formations + contenu
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

print("[INFO] Connexion a la base...")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cur = conn.cursor()
print("[OK] Connecte.")

# =========================================================
# 1. TABLES
# =========================================================

print("\n[INFO] Creation des tables...")

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
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS formations (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    description TEXT,
    categorie TEXT DEFAULT 'data',
    plateforme_defaut TEXT,
    trainer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS niveaux (
    id SERIAL PRIMARY KEY,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    prix REAL NOT NULL DEFAULT 0,
    UNIQUE(formation_id, numero)
);
""")

cur.execute("""
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
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS paiements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    montant REAL NOT NULL,
    statut TEXT DEFAULT 'pending',
    reference TEXT,
    date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chapitres (
    id SERIAL PRIMARY KEY,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(niveau_id, numero)
);
""")

cur.execute("""
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
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS progressions_lecons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lecon_id INTEGER NOT NULL REFERENCES lecons(id) ON DELETE CASCADE,
    termine INTEGER DEFAULT 0,
    date_termine TIMESTAMP,
    UNIQUE(user_id, lecon_id)
);
""")

cur.execute("""
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
""")

cur.execute("""
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
""")

cur.execute("""
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
""")

cur.execute("""
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
""")

cur.execute("""
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
""")

cur.execute("""
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
print("[OK] 13 tables pretes.")

# =========================================================
# 2. ADMIN + FORMATEUR DEMO
# =========================================================

print("\n[INFO] Creation admin + formateur...")

cur.execute("SELECT id FROM users WHERE email = %s", ("admin@softlearn.com",))
if not cur.fetchone():
    cur.execute("""
        INSERT INTO users(nom, prenom, email, password, role, statut_validation)
        VALUES (%s, %s, %s, %s, 'admin', 'approved')
    """, ("Admin", "Soft Learn", "admin@softlearn.com",
          generate_password_hash("admin123")))
    print("[OK] Admin cree : admin@softlearn.com / admin123")
else:
    print("[INFO] Admin existe deja.")

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
    print("[OK] Formateur cree : trainer@softlearn.com / trainer123")
else:
    trainer_id = trainer[0]
    print("[INFO] Formateur existe deja.")

conn.commit()

# =========================================================
# 3. FORMATIONS + NIVEAUX
# =========================================================

print("\n[INFO] Creation formations + niveaux...")

formations_data = [
    {"nom": "Python", "description": "Apprentissage progressif de Python : des fondamentaux jusqu'aux projets IA.", "categorie": "programmation", "plateforme_defaut": "https://colab.research.google.com/",
     "niveaux": [
        {"numero": 1, "titre": "Python – Fondamentaux", "description": "Syntaxe, variables, conditions, boucles, fonctions.", "prix": 5000},
        {"numero": 2, "titre": "Python – Data Analysis", "description": "NumPy, Pandas, Matplotlib, nettoyage et analyse.", "prix": 8000},
        {"numero": 3, "titre": "Python – Avance & IA", "description": "POO, Machine Learning, Scikit-learn, projets.", "prix": 10000},
     ]},
    {"nom": "SPSS", "description": "Analyse statistique avec SPSS.", "categorie": "data", "plateforme_defaut": None,
     "niveaux": [
        {"numero": 1, "titre": "SPSS – Initiation", "description": "Interface, donnees, statistiques descriptives.", "prix": 5000},
        {"numero": 2, "titre": "SPSS – Analyse statistique", "description": "Tests t, Khi2, ANOVA, regression.", "prix": 8000},
        {"numero": 3, "titre": "SPSS – Analyse avancee", "description": "Multivariee, projet complet.", "prix": 10000},
     ]},
    {"nom": "Bureautique", "description": "Word, Excel et PowerPoint jusqu'a l'automatisation VBA.", "categorie": "bureautique", "plateforme_defaut": None,
     "niveaux": [
        {"numero": 1, "titre": "Bureautique – Fondamentaux", "description": "Bases Word, Excel, PowerPoint.", "prix": 5000},
        {"numero": 2, "titre": "Bureautique – Intermediaire", "description": "Excel avance, TCD, formules.", "prix": 8000},
        {"numero": 3, "titre": "Bureautique – Automatisation", "description": "Macros VBA, dashboards.", "prix": 10000},
     ]},
    {"nom": "Intelligence Artificielle", "description": "IA, Machine Learning et Deep Learning.", "categorie": "data", "plateforme_defaut": "https://colab.research.google.com/",
     "niveaux": [
        {"numero": 1, "titre": "IA – Fondamentaux", "description": "Concepts IA, ML, premiers modeles.", "prix": 5000},
        {"numero": 2, "titre": "IA – Machine Learning", "description": "Regression, classification, Random Forest.", "prix": 8000},
        {"numero": 3, "titre": "IA – Deep Learning", "description": "CNN, Transfer Learning, projets.", "prix": 10000},
     ]},
    {"nom": "Developpement Web", "description": "HTML, CSS, JavaScript et Flask.", "categorie": "web", "plateforme_defaut": "https://codepen.io/pen/",
     "niveaux": [
        {"numero": 1, "titre": "Web – HTML & CSS", "description": "Structure, CSS, Flexbox, Grid.", "prix": 5000},
        {"numero": 2, "titre": "Web – JavaScript", "description": "DOM, evenements, validation.", "prix": 8000},
        {"numero": 3, "titre": "Web – Full Stack Flask", "description": "Flask, BDD, API, CRUD.", "prix": 10000},
     ]},
    {"nom": "C++", "description": "Programmation C++ des fondamentaux aux algorithmes.", "categorie": "programmation", "plateforme_defaut": "https://replit.com/languages/cpp",
     "niveaux": [
        {"numero": 1, "titre": "C++ – Fondamentaux", "description": "Syntaxe, variables, boucles.", "prix": 5000},
        {"numero": 2, "titre": "C++ – POO", "description": "Classes, heritage, polymorphisme.", "prix": 8000},
        {"numero": 3, "titre": "C++ – Algorithmes", "description": "Structures de donnees, pointeurs, STL.", "prix": 10000},
     ]},
    {"nom": "Java", "description": "Programmation Java des fondamentaux aux applications.", "categorie": "programmation", "plateforme_defaut": "https://replit.com/languages/java",
     "niveaux": [
        {"numero": 1, "titre": "Java – Fondamentaux", "description": "Syntaxe, variables, POO intro.", "prix": 5000},
        {"numero": 2, "titre": "Java – POO & Collections", "description": "Classes, heritage, collections.", "prix": 8000},
        {"numero": 3, "titre": "Java – Avance", "description": "JDBC, BDD, Spring.", "prix": 10000},
     ]},
    {"nom": "Data Analysis", "description": "Analyse de donnees d'Excel aux dashboards avances.", "categorie": "data", "plateforme_defaut": "https://www.kaggle.com/code",
     "niveaux": [
        {"numero": 1, "titre": "Data Analysis – Fondamentaux", "description": "Excel, stats descriptives.", "prix": 5000},
        {"numero": 2, "titre": "Data Analysis – Python", "description": "NumPy, Pandas, Matplotlib.", "prix": 8000},
        {"numero": 3, "titre": "Data Analysis – Avance", "description": "Analyse exploratoire, dashboards.", "prix": 10000},
     ]},
]

for f in formations_data:
    cur.execute("SELECT id FROM formations WHERE nom = %s", (f["nom"],))
    existing = cur.fetchone()
    if existing:
        fid = existing[0]
    else:
        cur.execute("""
            INSERT INTO formations(nom, description, categorie, plateforme_defaut, trainer_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (f["nom"], f["description"], f["categorie"],
              f["plateforme_defaut"], trainer_id))
        fid = cur.fetchone()[0]

    for n in f["niveaux"]:
        cur.execute("""
            SELECT id FROM niveaux WHERE formation_id = %s AND numero = %s
        """, (fid, n["numero"]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO niveaux(formation_id, numero, titre, description, prix)
                VALUES (%s, %s, %s, %s, %s)
            """, (fid, n["numero"], n["titre"], n["description"], n["prix"]))

conn.commit()
print("[OK] 8 formations + 24 niveaux inseres.")

# =========================================================
# 4. CONTENU PEDAGOGIQUE PYTHON N1
# =========================================================

print("\n[INFO] Creation du contenu pedagogique (Python N1)...")

cur.execute("""
    SELECT n.id FROM niveaux n
    JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = %s AND n.numero = 1
""", ("Python",))
row = cur.fetchone()
nid = row[0] if row else None

if nid:
    cur.execute("""
        INSERT INTO chapitres(niveau_id, numero, titre, description)
        VALUES (%s, 1, %s, %s)
        ON CONFLICT (niveau_id, numero) DO UPDATE SET
            titre = EXCLUDED.titre, description = EXCLUDED.description
        RETURNING id
    """, (nid, "Introduction a Python",
          "Decouvrez Python et installez votre environnement"))
    chap1 = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO chapitres(niveau_id, numero, titre, description)
        VALUES (%s, 2, %s, %s)
        ON CONFLICT (niveau_id, numero) DO UPDATE SET
            titre = EXCLUDED.titre, description = EXCLUDED.description
        RETURNING id
    """, (nid, "Bases du langage",
          "print, input, variables, conditions, boucles et fonctions"))
    chap2 = cur.fetchone()[0]

    lecons_data = [
        (chap1, 1, "Qu'est-ce que Python ?", 25,
         "## Qu'est-ce que Python ?\n\n"
         "Python est un **langage interprete**, **multi-paradigme**, "
         "**type dynamiquement** et **open source**, cree par "
         "**Guido van Rossum** en 1991.\n\n"
         "### Domaines d'application\n\n"
         "- Developpement Web (Django, Flask)\n"
         "- Data Science (Pandas, NumPy)\n"
         "- Intelligence Artificielle (TensorFlow, PyTorch)\n\n"
         "### Premier programme\n\n"
         "```python\nprint(\"Bonjour Soft Learn !\")\n```"),
        (chap1, 2, "Installer Python", 20,
         "## Installation\n\n"
         "### Windows\n\n"
         "1. Telecharger sur **python.org**\n"
         "2. CRITIQUE : cocher **Add Python to PATH**\n"
         "3. Cliquer sur Install Now\n"
         "4. Verifier : `python --version`\n\n"
         "> **Regle absolue** : Utilisez toujours Python 3."),
        (chap2, 1, "Afficher avec print()", 30,
         "## print()\n\n"
         "```python\nprint(\"Bonjour\")\nprint(42)\n```\n\n"
         "### Parametres\n\n"
         "- `sep` : change le separateur\n"
         "- `end` : change la fin de ligne\n\n"
         "```python\nprint(\"a\", \"b\", sep=\"-\")\n"
         "print(\"Ligne 1\", end=\" \")\n```"),
        (chap2, 2, "Saisir avec input()", 30,
         "## input()\n\n"
         "```python\nnom = input(\"Votre nom : \")\nprint(f\"Bonjour {nom} !\")\n```\n\n"
         "> **Important** : input() retourne TOUJOURS une chaine (str).\n\n"
         "### Conversion\n\n"
         "```python\nage = int(input(\"Votre age : \"))\n```"),
        (chap2, 3, "Les variables", 30,
         "## Variables\n\n"
         "```python\nnom = \"Ahmed\"\nage = 25\ntaille = 1.75\nactif = True\n```\n\n"
         "### Types\n\n"
         "| Type | Exemple |\n|------|---------|\n"
         "| str | \"Bonjour\" |\n| int | 42 |\n| float | 3.14 |\n| bool | True/False |"),
        (chap2, 4, "Les conditions", 35,
         "## Conditions\n\n"
         "```python\nage = 20\nif age >= 18:\n    print(\"Majeur\")\nelse:\n    print(\"Mineur\")\n```\n\n"
         "### Operateurs\n\n"
         "`==`, `!=`, `>`, `<`, `>=`, `<=`, `and`, `or`, `not`"),
        (chap2, 5, "Les boucles", 35,
         "## Boucles\n\n"
         "```python\nfor i in range(5):\n    print(i)\n```\n\n"
         "```python\ncompteur = 1\nwhile compteur <= 5:\n    print(compteur)\n    compteur += 1\n```\n\n"
         "### break et continue\n\n"
         "- `break` : sort de la boucle\n"
         "- `continue` : saute l'iteration"),
        (chap2, 6, "Les fonctions", 40,
         "## Fonctions\n\n"
         "```python\ndef addition(a, b):\n    return a + b\n\n"
         "resultat = addition(5, 3)\nprint(resultat)\n```\n\n"
         "### Valeurs par defaut\n\n"
         "```python\ndef saluer(nom, message=\"Bonjour\"):\n    print(f\"{message}, {nom} !\")\n```"),
    ]

    for ch, num, titre, duree, contenu in lecons_data:
        cur.execute("""
            INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (chapitre_id, numero) DO UPDATE SET
                titre = EXCLUDED.titre,
                contenu = EXCLUDED.contenu,
                duree = EXCLUDED.duree
        """, (ch, num, titre, contenu, duree))

    print("[OK] 2 chapitres + 8 lecons")

    # Exercices
    cur.execute("SELECT COUNT(*) FROM exercices WHERE niveau_id = %s", (nid,))
    if cur.fetchone()[0] == 0:
        exos = [
            {"titre": "Ex 1.1.a : Definition", "type": "texte",
             "description": "Definir Python",
             "contenu": "Expliquez dans vos propres mots ce qu'est Python.",
             "reponse_attendue": "Python est un langage interprete multi-paradigme."},
            {"titre": "Ex 1.1.b : QCM intro", "type": "qcm",
             "description": "QCM sur les bases de Python",
             "qcm": [
                 {"question": "Qui a cree Python ?",
                  "options": ["Bill Gates", "Guido van Rossum", "Linus Torvalds", "Zuck"],
                  "bonne": 1},
                 {"question": "En quelle annee ?",
                  "options": ["1985", "1991", "2000", "2010"], "bonne": 1},
                 {"question": "Version a utiliser ?",
                  "options": ["1", "2", "3", "Peu importe"], "bonne": 2},
             ]},
            {"titre": "Ex 2.1.a : Premier affichage", "type": "code",
             "description": "Afficher 3 lignes",
             "langage": "python",
             "contenu": "Affichez votre nom, votre age et une phrase.",
             "reponse_attendue": 'print("Ahmed")\nprint(22)\nprint("Python !")',
             "plateforme_url": "https://colab.research.google.com/"},
            {"titre": "Ex 2.4.a : Pair ou impair", "type": "code",
             "description": "Verifier la parite",
             "langage": "python",
             "contenu": "Demandez un nombre et affichez Pair/Impair.",
             "reponse_attendue": "n = int(input())\nif n % 2 == 0:\n    print('Pair')\nelse:\n    print('Impair')",
             "plateforme_url": "https://colab.research.google.com/"},
            {"titre": "Ex 2.5.a : Table multiplication", "type": "code",
             "description": "Table de multiplication",
             "langage": "python",
             "contenu": "Demandez un nombre et affichez sa table de 1 a 10.",
             "reponse_attendue": "n = int(input())\nfor i in range(1, 11):\n    print(f'{n} x {i} = {n*i}')",
             "plateforme_url": "https://colab.research.google.com/"},
            {"titre": "Ex 2.6.a : Aire rectangle", "type": "code",
             "description": "Fonction aire",
             "langage": "python",
             "contenu": "Creez une fonction calculer_aire(l, L).",
             "reponse_attendue": "def calculer_aire(l, L):\n    return l * L\nprint(calculer_aire(5, 3))",
             "plateforme_url": "https://colab.research.google.com/"},
        ]

        for exo in exos:
            cur.execute("""
                INSERT INTO exercices(
                    niveau_id, titre, description, type, langage,
                    contenu, reponse_attendue, qcm_data, plateforme_url,
                    corrige_auto, est_evaluation_finale, partie
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'principal')
            """, (nid, exo["titre"], exo.get("description"),
                  exo["type"], exo.get("langage"),
                  exo.get("contenu"), exo.get("reponse_attendue"),
                  json.dumps(exo["qcm"]) if exo.get("qcm") else None,
                  exo.get("plateforme_url"),
                  1 if exo["type"] == "qcm" else 0))

        # Evaluation finale
        qcm_final = [
            {"question": "Qui a cree Python ?", "options": ["Bill Gates", "Guido van Rossum", "Linus", "Zuck"], "bonne": 1},
            {"question": "Annee de creation ?", "options": ["1985", "1991", "2000", "2010"], "bonne": 1},
            {"question": "Version a utiliser ?", "options": ["1", "2", "3", "Peu importe"], "bonne": 2},
            {"question": "print() fait quoi ?", "options": ["Lit", "Affiche", "Calcule", "Supprime"], "bonne": 1},
            {"question": "input() retourne ?", "options": ["int", "float", "str", "bool"], "bonne": 2},
            {"question": "Convertir en entier ?", "options": ["str()", "int()", "float()", "num()"], "bonne": 1},
            {"question": "Declarer variable ?", "options": ["var x=5", "int x=5", "x=5", "let x=5"], "bonne": 2},
            {"question": "Type de 3.14 ?", "options": ["int", "float", "str", "bool"], "bonne": 1},
            {"question": "Convention Python ?", "options": ["camelCase", "PascalCase", "snake_case", "kebab"], "bonne": 2},
            {"question": "Operateur = ?", "options": ["Compare", "Assigne", "Multiplie", "Divise"], "bonne": 1},
            {"question": "Mot-cle fonction ?", "options": ["function", "def", "func", "define"], "bonne": 1},
            {"question": "return fait quoi ?", "options": ["Affiche", "Arrete", "Renvoie", "Efface"], "bonne": 2},
            {"question": "if x > 5 syntaxe ?", "options": ["if x>5 {}", "if x>5:", "if (x>5)", "IF x>5"], "bonne": 1},
            {"question": "Indentation espaces ?", "options": ["1", "2", "4", "8"], "bonne": 2},
            {"question": "Boucle liste ?", "options": ["while", "for", "loop", "repeat"], "bonne": 1},
            {"question": "range(5) genere ?", "options": ["1..5", "0..4", "0..5", "5..1"], "bonne": 1},
            {"question": "break fait ?", "options": ["Saute", "Sort", "Redemarre", "Pause"], "bonne": 1},
            {"question": "continue fait ?", "options": ["Saute iteration", "Sort", "Redemarre", "Pause"], "bonne": 0},
            {"question": "f-string ?", "options": ["print('{x}')", "print('%s'%x)", "print(f'{x}')", "print(x)"], "bonne": 2},
            {"question": "'*' sur chaine ?", "options": ["Multiplie", "Repete", "Copie", "Inverse"], "bonne": 1},
        ]

        cur.execute("""
            INSERT INTO exercices(
                niveau_id, titre, description, type, qcm_data,
                corrige_auto, est_evaluation_finale, partie
            ) VALUES (%s, %s, %s, 'qcm', %s, 1, 1, 'qcm')
        """, (nid, "Evaluation finale - Certification Python N1",
              "20 questions. Seuil : 70%", json.dumps(qcm_final)))

        print("[OK] 6 exercices + 1 evaluation finale")

# =========================================================
# 5. PRE-TESTS POUR TOUS LES NIVEAUX >= 2
# =========================================================

print("\n[INFO] Creation des pre-tests...")

templates_pretest = {
    "Python": [
        {"question": "print() fait quoi ?", "options": ["Lit", "Affiche", "Calcule", "Supprime"], "bonne": 1},
        {"question": "Type de 3.14 ?", "options": ["int", "float", "str", "bool"], "bonne": 1},
        {"question": "Definir une fonction ?", "options": ["function f()", "def f():", "void f()", "func f()"], "bonne": 1},
    ],
    "SPSS": [
        {"question": "SPSS signifie ?", "options": ["Statistical Package for the Social Sciences", "Program System", "Software Pro", "Simple Program"], "bonne": 0},
        {"question": "SPSS sert a ?", "options": ["Design", "Analyse de donnees", "Web", "Jeux"], "bonne": 1},
        {"question": "Extension SPSS ?", "options": [".xlsx", ".sav", ".csv", ".txt"], "bonne": 1},
    ],
    "Bureautique": [
        {"question": "Tableur ?", "options": ["Word", "Excel", "PowerPoint", "Access"], "bonne": 1},
        {"question": "Extension Word ?", "options": [".xlsx", ".docx", ".pptx", ".txt"], "bonne": 1},
        {"question": "Ctrl+C fait ?", "options": ["Coller", "Copier", "Couper", "Sauver"], "bonne": 1},
    ],
    "Intelligence Artificielle": [
        {"question": "IA signifie ?", "options": ["Intelligence Artificielle", "Internet Avance", "Interface Auto", "Info Appliquee"], "bonne": 0},
        {"question": "Langage IA ?", "options": ["Java", "C++", "Python", "PHP"], "bonne": 2},
        {"question": "ML fait ?", "options": ["Programme manuellement", "Apprend des donnees", "Cree sites", "Gere BDD"], "bonne": 1},
    ],
    "Developpement Web": [
        {"question": "HTML signifie ?", "options": ["HyperText Markup Language", "High Tech Modern Lang", "Home Tool Markup", "Hyperlink Text Mode"], "bonne": 0},
        {"question": "CSS sert a ?", "options": ["Structurer", "Styliser", "Programmer", "BDD"], "bonne": 1},
        {"question": "Balise lien ?", "options": ["<link>", "<a>", "<href>", "<url>"], "bonne": 1},
    ],
    "C++": [
        {"question": "Createur C++ ?", "options": ["Bjarne Stroustrup", "Dennis Ritchie", "James Gosling", "Guido"], "bonne": 0},
        {"question": "Sortie std ?", "options": ["print()", "cout", "System.out", "console.log"], "bonne": 1},
        {"question": "Type entier ?", "options": ["float", "int", "string", "bool"], "bonne": 1},
    ],
    "Java": [
        {"question": "Createur Java ?", "options": ["Microsoft", "Sun Microsystems", "Apple", "Google"], "bonne": 1},
        {"question": "Point d'entree ?", "options": ["start()", "run()", "main()", "init()"], "bonne": 2},
        {"question": "Variable Java ?", "options": ["var x=5;", "int x=5;", "x=5;", "let x=5;"], "bonne": 1},
    ],
    "Data Analysis": [
        {"question": "Analyse donnees ?", "options": ["Cree sites", "Extrait info", "Programme jeux", "Gere reseaux"], "bonne": 1},
        {"question": "DataFrames Python ?", "options": ["NumPy", "Pandas", "Matplotlib", "SciPy"], "bonne": 1},
        {"question": "Matplotlib sert a ?", "options": ["Analyse texte", "Visualiser donnees", "Calcul", "BDD"], "bonne": 1},
    ],
}

cur.execute("""
    SELECT n.id, n.numero, f.nom
    FROM niveaux n
    JOIN formations f ON f.id = n.formation_id
    WHERE n.numero >= 2
""")

count_pretests = 0
for nid2, num, fname in cur.fetchall():
    cur.execute("SELECT id FROM pretests WHERE niveau_id = %s", (nid2,))
    if not cur.fetchone():
        questions = templates_pretest.get(fname, templates_pretest["Python"])
        titre = f"Pre-test {fname} — Niveau {num}"
        description = f"Verifiez vos prerequis pour le niveau {num}."
        cur.execute("""
            INSERT INTO pretests(niveau_id, titre, description,
                                  seuil_reussite, qcm_data)
            VALUES (%s, %s, %s, 70, %s)
        """, (nid2, titre, description, json.dumps(questions)))
        count_pretests += 1

conn.commit()
print(f"[OK] {count_pretests} pre-tests crees.")

# =========================================================
# FIN
# =========================================================

cur.close()
conn.close()

print("\n" + "=" * 60)
print("[OK] INITIALISATION COMPLETE TERMINEE AVEC SUCCES")
print("=" * 60)
print("Admin    : admin@softlearn.com    / admin123")
print("Trainer  : trainer@softlearn.com  / trainer123")
print("=" * 60)