# =========================================================
# SOFT LEARN — CRÉATION DE LA BASE DE DONNÉES
# =========================================================

import sqlite3
import json
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

conn.executescript("""
DROP TABLE IF EXISTS progressions_etudiant;
DROP TABLE IF EXISTS progressions_lecons;
DROP TABLE IF EXISTS soumissions_pretest;
DROP TABLE IF EXISTS pretests;
DROP TABLE IF EXISTS lecons;
DROP TABLE IF EXISTS chapitres;
DROP TABLE IF EXISTS soumissions;
DROP TABLE IF EXISTS exercices;
DROP TABLE IF EXISTS paiements;
DROP TABLE IF EXISTS inscriptions;
DROP TABLE IF EXISTS niveaux;
DROP TABLE IF EXISTS formations;
DROP TABLE IF EXISTS users;

-- =========================================
-- UTILISATEURS
-- =========================================

CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    telephone TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','trainer','admin')),

    statut_validation TEXT DEFAULT 'approved'
        CHECK(statut_validation IN ('pending','approved','rejected')),
    diplome TEXT,
    cv TEXT,
    diplome_file TEXT,
    experience TEXT,
    motif_refus TEXT,
    date_validation TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- FORMATIONS
-- =========================================

CREATE TABLE formations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    description TEXT,
    categorie TEXT DEFAULT 'data',
    plateforme_defaut TEXT,
    trainer_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(trainer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- =========================================
-- NIVEAUX
-- =========================================

CREATE TABLE niveaux(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formation_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    prix REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(formation_id) REFERENCES formations(id) ON DELETE CASCADE,
    UNIQUE(formation_id, numero)
);

-- =========================================
-- INSCRIPTIONS
-- =========================================

CREATE TABLE inscriptions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    niveau_id INTEGER NOT NULL,
    formation_id INTEGER NOT NULL,
    progression INTEGER DEFAULT 0,
    statut TEXT DEFAULT 'inactive',
    date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
    date_completion TEXT,
    UNIQUE(user_id, niveau_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE,
    FOREIGN KEY(formation_id) REFERENCES formations(id) ON DELETE CASCADE
);

-- =========================================
-- PAIEMENTS
-- =========================================

CREATE TABLE paiements(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    niveau_id INTEGER NOT NULL,
    montant REAL NOT NULL,
    statut TEXT DEFAULT 'pending',
    reference TEXT,
    date_paiement TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE
);

-- =========================================
-- CHAPITRES
-- =========================================

CREATE TABLE chapitres(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niveau_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE,
    UNIQUE(niveau_id, numero)
);

-- =========================================
-- LEÇONS
-- =========================================

CREATE TABLE lecons(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapitre_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    titre TEXT NOT NULL,
    contenu TEXT,
    duree INTEGER DEFAULT 5,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(chapitre_id) REFERENCES chapitres(id) ON DELETE CASCADE,
    UNIQUE(chapitre_id, numero)
);

-- =========================================
-- PROGRESSION LEÇONS
-- =========================================

CREATE TABLE progressions_lecons(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lecon_id INTEGER NOT NULL,
    termine INTEGER DEFAULT 0,
    date_termine TEXT,
    UNIQUE(user_id, lecon_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(lecon_id) REFERENCES lecons(id) ON DELETE CASCADE
);

-- =========================================
-- EXERCICES
-- =========================================

CREATE TABLE exercices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niveau_id INTEGER NOT NULL,
    titre TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'texte'
        CHECK(type IN ('texte','code','qcm','fichier')),
    langage TEXT,
    contenu TEXT,
    reponse_attendue TEXT,
    qcm_data TEXT,
    plateforme_url TEXT,
    corrige_auto INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE
);

-- =========================================
-- SOUMISSIONS
-- =========================================

CREATE TABLE soumissions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercice_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    contenu TEXT,
    note REAL,
    commentaire TEXT,
    note_ia REAL,
    commentaire_ia TEXT,
    date_correction_ia TEXT,
    statut TEXT DEFAULT 'submitted',
    date_soumission TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(exercice_id) REFERENCES exercices(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================
-- PRÉ-TESTS
-- =========================================

CREATE TABLE pretests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niveau_id INTEGER NOT NULL UNIQUE,
    titre TEXT NOT NULL,
    description TEXT,
    seuil_reussite INTEGER DEFAULT 70,
    duree_minutes INTEGER DEFAULT 30,
    qcm_data TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE
);

-- =========================================
-- SOUMISSIONS PRÉ-TESTS
-- =========================================

CREATE TABLE soumissions_pretest(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pretest_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    niveau_id INTEGER NOT NULL,
    reponses TEXT,
    score INTEGER,
    reussi INTEGER DEFAULT 0,
    date_passage TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(pretest_id) REFERENCES pretests(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(niveau_id) REFERENCES niveaux(id) ON DELETE CASCADE
);

-- =========================================
-- PROGRESSION GLOBALE
-- =========================================

CREATE TABLE progressions_etudiant(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    formation_id INTEGER NOT NULL,
    niveau_actuel_id INTEGER,
    niveaux_completes TEXT DEFAULT '[]',
    pourcentage_global INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, formation_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(formation_id) REFERENCES formations(id) ON DELETE CASCADE
);
""")

# =========================================================
# UTILISATEURS DE DÉMONSTRATION
# =========================================================

admin_id = conn.execute("""
    INSERT INTO users(nom, prenom, email, password, role, statut_validation)
    VALUES (?, ?, ?, ?, 'admin', 'approved')
""", ("Admin", "Soft Learn", "admin@softlearn.com",
      generate_password_hash("admin123"))).lastrowid

trainer_id = conn.execute("""
    INSERT INTO users(nom, prenom, email, password, role,
                      statut_validation, diplome, experience)
    VALUES (?, ?, ?, ?, 'trainer', 'approved', ?, ?)
""", ("Formateur", "Demo", "trainer@softlearn.com",
      generate_password_hash("trainer123"),
      "Master en Informatique",
      "5 ans d'expérience en développement Python et formation professionnelle.")).lastrowid

student_id = conn.execute("""
    INSERT INTO users(nom, prenom, email, password, role, statut_validation)
    VALUES (?, ?, ?, ?, 'student', 'approved')
""", ("Etudiant", "Demo", "student@softlearn.com",
      generate_password_hash("student123"))).lastrowid


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
             "description": "Interface, données, statistiques descriptives.", "prix": 5000},
            {"numero": 2, "titre": "SPSS – Analyse statistique",
             "description": "Tests t, Khi², ANOVA, régression.", "prix": 8000},
            {"numero": 3, "titre": "SPSS – Analyse avancée",
             "description": "Multivariée, projet complet.", "prix": 10000},
        ]
    },
    {
        "nom": "Bureautique",
        "description": "Word, Excel et PowerPoint jusqu'à l'automatisation VBA.",
        "categorie": "bureautique",
        "plateforme_defaut": None,
        "niveaux": [
            {"numero": 1, "titre": "Bureautique – Fondamentaux",
             "description": "Bases Word, Excel, PowerPoint.", "prix": 5000},
            {"numero": 2, "titre": "Bureautique – Intermédiaire",
             "description": "Excel avancé, TCD, formules.", "prix": 8000},
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
             "description": "Concepts IA, ML, premiers modèles.", "prix": 5000},
            {"numero": 2, "titre": "IA – Machine Learning",
             "description": "Régression, classification, Random Forest.", "prix": 8000},
            {"numero": 3, "titre": "IA – Deep Learning",
             "description": "CNN, Transfer Learning, projets.", "prix": 10000},
        ]
    },
    {
        "nom": "Développement Web",
        "description": "HTML, CSS, JavaScript et Flask.",
        "categorie": "web",
        "plateforme_defaut": "https://codepen.io/pen/",
        "niveaux": [
            {"numero": 1, "titre": "Web – HTML & CSS",
             "description": "Structure, CSS, Flexbox, Grid.", "prix": 5000},
            {"numero": 2, "titre": "Web – JavaScript",
             "description": "DOM, événements, validation.", "prix": 8000},
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
             "description": "Classes, héritage, polymorphisme.", "prix": 8000},
            {"numero": 3, "titre": "C++ – Algorithmes",
             "description": "Structures de données, pointeurs, STL.", "prix": 10000},
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
             "description": "Classes, héritage, collections.", "prix": 8000},
            {"numero": 3, "titre": "Java – Avancé",
             "description": "JDBC, BDD, Spring.", "prix": 10000},
        ]
    },
    {
        "nom": "Data Analysis",
        "description": "Analyse de données d'Excel aux dashboards avancés.",
        "categorie": "data",
        "plateforme_defaut": "https://www.kaggle.com/code",
        "niveaux": [
            {"numero": 1, "titre": "Data Analysis – Fondamentaux",
             "description": "Excel, stats descriptives.", "prix": 5000},
            {"numero": 2, "titre": "Data Analysis – Python",
             "description": "NumPy, Pandas, Matplotlib.", "prix": 8000},
            {"numero": 3, "titre": "Data Analysis – Avancé",
             "description": "Analyse exploratoire, dashboards.", "prix": 10000},
        ]
    },
]

for f in formations_data:
    fid = conn.execute("""
        INSERT INTO formations(nom, description, categorie, plateforme_defaut, trainer_id)
        VALUES (?, ?, ?, ?, ?)
    """, (f["nom"], f["description"], f["categorie"],
          f["plateforme_defaut"], trainer_id)).lastrowid

    for n in f["niveaux"]:
        conn.execute("""
            INSERT INTO niveaux(formation_id, numero, titre, description, prix)
            VALUES (?, ?, ?, ?, ?)
        """, (fid, n["numero"], n["titre"], n["description"], n["prix"]))

# =========================================================
# CONTENU PÉDAGOGIQUE DE DÉMONSTRATION
# =========================================================

# ---------- Python Niveau 1 ----------
py_n1 = conn.execute("""
    SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = 'Python' AND n.numero = 1
""").fetchone()

if py_n1:
    niveau_id = py_n1[0]

    # Chapitre 1 : Introduction
    chap1 = conn.execute("""
        INSERT INTO chapitres(niveau_id, numero, titre, description)
        VALUES (?, 1, ?, ?)
    """, (niveau_id, "Introduction à Python",
          "Découvrez Python et installez votre environnement")).lastrowid

    # Leçon 1.1
    lecon1_contenu = (
        "Python est un langage de programmation **interprété**, "
        "**multi-paradigme** et **open source**.\n\n"
        "## Pourquoi Python ?\n\n"
        "- 📖 Syntaxe simple et lisible\n"
        "- 🚀 Polyvalent : web, data, IA\n"
        "- 🌍 Grande communauté\n\n"
        "## Premier exemple\n\n"
        "```python\n"
        "print(\"Bonjour Soft Learn !\")\n"
        "```\n\n"
        "Ce code affiche simplement le message dans la console."
    )

    conn.execute("""
        INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
        VALUES (?, 1, ?, ?, 10)
    """, (chap1, "Qu'est-ce que Python ?", lecon1_contenu))

    # Leçon 1.2
    lecon2_contenu = (
        "## Étapes d'installation\n\n"
        "### 1. Télécharger Python\n\n"
        "Rendez-vous sur python.org et téléchargez la dernière version.\n\n"
        "### 2. Installation sous Windows\n\n"
        "1. Lancez le fichier .exe téléchargé\n"
        "2. ⚠️ Cochez \"Add Python to PATH\"\n"
        "3. Cliquez sur \"Install Now\"\n\n"
        "### 3. Vérification\n\n"
        "```bash\n"
        "python --version\n"
        "```"
    )

    conn.execute("""
        INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
        VALUES (?, 2, ?, ?, 15)
    """, (chap1, "Installer Python", lecon2_contenu))

    # Chapitre 2 : Variables
    chap2 = conn.execute("""
        INSERT INTO chapitres(niveau_id, numero, titre, description)
        VALUES (?, 2, ?, ?)
    """, (niveau_id, "Variables et types",
          "Apprenez à stocker et manipuler des données")).lastrowid

    lecon3_contenu = (
        "## Qu'est-ce qu'une variable ?\n\n"
        "Une variable est un **espace mémoire** nommé qui stocke une valeur.\n\n"
        "### Création d'une variable\n\n"
        "```python\n"
        "nom = \"Ahmed\"\n"
        "age = 25\n"
        "taille = 1.75\n"
        "```\n\n"
        "### Types de données\n\n"
        "| Type | Exemple |\n"
        "|------|---------|\n"
        "| str | \"Bonjour\" |\n"
        "| int | 42 |\n"
        "| float | 3.14 |\n"
        "| bool | True / False |\n"
        "| list | [1, 2, 3] |"
    )

    conn.execute("""
        INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
        VALUES (?, 1, ?, ?, 12)
    """, (chap2, "Les variables", lecon3_contenu))

    # Exercice code
    conn.execute("""
        INSERT INTO exercices(niveau_id, titre, description, type,
                              langage, contenu, plateforme_url)
        VALUES (?, ?, ?, 'code', 'python', ?, ?)
    """, (niveau_id,
          "Afficher un message",
          "Écrivez un programme qui affiche « Bonjour Soft Learn ».",
          "Utilisez la fonction print() pour afficher le message.",
          "https://colab.research.google.com/"))

    # QCM
    qcm_python = [
        {"question": "Quel est le type de la valeur 3.14 en Python ?",
         "options": ["int", "float", "str", "bool"], "bonne": 1},
        {"question": "Comment déclare-t-on une variable en Python ?",
         "options": ["var x = 5", "int x = 5", "x = 5", "let x = 5"], "bonne": 2},
        {"question": "Que fait la fonction print() ?",
         "options": ["Elle lit une saisie", "Elle affiche du texte",
                     "Elle calcule une somme", "Elle supprime une variable"],
         "bonne": 1},
    ]
    conn.execute("""
        INSERT INTO exercices(niveau_id, titre, description, type,
                              qcm_data, corrige_auto)
        VALUES (?, ?, ?, 'qcm', ?, 1)
    """, (niveau_id, "QCM : Les bases de Python",
          "Testez vos connaissances sur les bases.", json.dumps(qcm_python)))

# ---------- Python Niveau 2 : Pré-test ----------
py_n2 = conn.execute("""
    SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = 'Python' AND n.numero = 2
""").fetchone()

if py_n2:
    pretest_data = [
        {"question": "Que fait la fonction print() ?",
         "options": ["Lit une saisie", "Affiche du texte",
                     "Calcule une somme", "Supprime une variable"],
         "bonne": 1},
        {"question": "Quel est le résultat de 3 + 2 * 2 ?",
         "options": ["10", "7", "12", "5"], "bonne": 1},
        {"question": "Comment définit-on une fonction en Python ?",
         "options": ["function maFonction()", "def maFonction():",
                     "void maFonction()", "func maFonction()"], "bonne": 1},
        {"question": "Quel type de données représente [1, 2, 3] ?",
         "options": ["tuple", "dict", "list", "set"], "bonne": 2},
        {"question": "Que fait l'opérateur == en Python ?",
         "options": ["Affecte une valeur", "Compare deux valeurs",
                     "Additionne", "Supprime"], "bonne": 1},
    ]
    conn.execute("""
        INSERT INTO pretests(niveau_id, titre, description,
                             seuil_reussite, qcm_data)
        VALUES (?, ?, ?, ?, ?)
    """, (py_n2[0], "Pré-test Python Niveau 2",
          "Ce test vérifie que vous maîtrisez les bases de Python (Niveau 1) "
          "avant de passer au niveau 2.",
          70, json.dumps(pretest_data)))

# ---------- Python Niveau 3 : Pré-test ----------
py_n3 = conn.execute("""
    SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = 'Python' AND n.numero = 3
""").fetchone()

if py_n3:
    pretest_data_n3 = [
        {"question": "Que signifie POO ?",
         "options": ["Programmation Orientée Objet",
                     "Programme Opérationnel Optimisé",
                     "Procédure Ordonnée", "Aucune de ces réponses"],
         "bonne": 0},
        {"question": "Quelle bibliothèque est utilisée pour le Machine Learning ?",
         "options": ["NumPy", "Pandas", "Scikit-learn", "Matplotlib"],
         "bonne": 2},
        {"question": "Que fait pandas.DataFrame ?",
         "options": ["Crée une liste", "Crée un tableau 2D",
                     "Crée un dictionnaire", "Aucune de ces réponses"],
         "bonne": 1},
    ]
    conn.execute("""
        INSERT INTO pretests(niveau_id, titre, description,
                             seuil_reussite, qcm_data)
        VALUES (?, ?, ?, ?, ?)
    """, (py_n3[0], "Pré-test Python Niveau 3",
          "Ce test vérifie que vous maîtrisez le niveau 2 (Data Analysis) "
          "avant de passer au niveau 3.",
          70, json.dumps(pretest_data_n3)))

# =========================================================
# PRÉ-TESTS AUTOMATIQUES POUR TOUS LES NIVEAUX ≥ 2
# =========================================================

def creer_pretest_generique(niveau_id, formation_nom, niveau_numero):
    """
    Crée un pré-test générique adapté à la formation.
    Ces pré-tests vérifient les connaissances du niveau précédent.
    """
    # Modèles de questions par formation
    templates = {
        "SPSS": [
            {"question": "Que signifie SPSS ?",
             "options": ["Statistical Package for the Social Sciences",
                         "Statistical Program System Software",
                         "Software for Professional Statistics",
                         "Simple Program for Statistical Studies"],
             "bonne": 0},
            {"question": "À quoi sert SPSS ?",
             "options": ["À faire du design graphique",
                         "À analyser des données statistiques",
                         "À créer des sites web",
                         "À programmer des jeux"],
             "bonne": 1},
            {"question": "Quel type de fichier SPSS utilise-t-il ?",
             "options": [".xlsx", ".sav", ".csv", ".txt"],
             "bonne": 1},
        ],
        "Bureautique": [
            {"question": "Quel logiciel est utilisé pour les tableurs ?",
             "options": ["Word", "Excel", "PowerPoint", "Access"],
             "bonne": 1},
            {"question": "Quelle extension pour un document Word ?",
             "options": [".xlsx", ".docx", ".pptx", ".txt"],
             "bonne": 1},
            {"question": "Que fait le raccourci Ctrl+C ?",
             "options": ["Coller", "Copier", "Couper", "Enregistrer"],
             "bonne": 1},
        ],
        "Intelligence Artificielle": [
            {"question": "Que signifie IA ?",
             "options": ["Intelligence Artificielle",
                         "Internet Avancé",
                         "Interface Automatique",
                         "Information Appliquée"],
             "bonne": 0},
            {"question": "Quel langage est le plus utilisé en IA ?",
             "options": ["Java", "C++", "Python", "PHP"],
             "bonne": 2},
            {"question": "Que fait le Machine Learning ?",
             "options": ["Programmer manuellement",
                         "Apprendre à partir de données",
                         "Créer des sites web",
                         "Gérer des bases de données"],
             "bonne": 1},
        ],
        "Développement Web": [
            {"question": "Que signifie HTML ?",
             "options": ["HyperText Markup Language",
                         "High Tech Modern Language",
                         "Home Tool Markup Language",
                         "Hyperlink Text Mode Language"],
             "bonne": 0},
            {"question": "À quoi sert le CSS ?",
             "options": ["Structurer le contenu",
                         "Styliser le contenu",
                         "Programmer le serveur",
                         "Gérer les bases de données"],
             "bonne": 1},
            {"question": "Quelle balise crée un lien ?",
             "options": ["<link>", "<a>", "<href>", "<url>"],
             "bonne": 1},
        ],
        "C++": [
            {"question": "Qui a créé le C++ ?",
             "options": ["Bjarne Stroustrup", "Dennis Ritchie",
                         "James Gosling", "Guido van Rossum"],
             "bonne": 0},
            {"question": "Quelle est la sortie standard en C++ ?",
             "options": ["print()", "cout", "System.out", "console.log"],
             "bonne": 1},
            {"question": "Quel type pour un nombre entier en C++ ?",
             "options": ["float", "int", "string", "bool"],
             "bonne": 1},
        ],
        "Java": [
            {"question": "Qui a créé Java ?",
             "options": ["Microsoft", "Sun Microsystems",
                         "Apple", "Google"],
             "bonne": 1},
            {"question": "Quelle méthode est le point d'entrée en Java ?",
             "options": ["start()", "run()", "main()", "init()"],
             "bonne": 2},
            {"question": "Comment déclare-t-on une variable en Java ?",
             "options": ["var x = 5;", "int x = 5;",
                         "x = 5;", "let x = 5;"],
             "bonne": 1},
        ],
        "Data Analysis": [
            {"question": "Que signifie l'analyse de données ?",
             "options": ["Créer des sites",
                         "Extraire des informations de données",
                         "Programmer des jeux",
                         "Gérer des réseaux"],
             "bonne": 1},
            {"question": "Quelle bibliothèque Python pour les DataFrames ?",
             "options": ["NumPy", "Pandas", "Matplotlib", "SciPy"],
             "bonne": 1},
            {"question": "À quoi sert Matplotlib ?",
             "options": ["Analyse de texte", "Visualisation de données",
                         "Calcul matriciel", "Base de données"],
             "bonne": 1},
        ],
        "Python": [
            {"question": "Que fait print() en Python ?",
             "options": ["Lit une saisie", "Affiche du texte",
                         "Additionne", "Supprime"],
             "bonne": 1},
            {"question": "Quel type pour 3.14 ?",
             "options": ["int", "float", "str", "bool"],
             "bonne": 1},
            {"question": "Comment définir une fonction ?",
             "options": ["function f()", "def f():",
                         "void f()", "func f()"],
             "bonne": 1},
        ],
    }

    # Utiliser le template correspondant ou un générique
    questions = templates.get(formation_nom, templates["Python"])

    # Adapter le titre selon le niveau
    if niveau_numero == 2:
        titre = f"Pré-test {formation_nom} — Niveau 2"
        description = (f"Vérifiez que vous maîtrisez les bases de {formation_nom} "
                       f"avant de passer au niveau 2.")
    else:
        titre = f"Pré-test {formation_nom} — Niveau 3"
        description = (f"Vérifiez que vous maîtrisez le niveau 2 de {formation_nom} "
                       f"avant de passer au niveau 3.")

    conn.execute("""
        INSERT OR IGNORE INTO pretests(niveau_id, titre, description,
                                        seuil_reussite, qcm_data)
        VALUES (?, ?, ?, ?, ?)
    """, (niveau_id, titre, description, 70, json.dumps(questions)))


# Parcourir tous les niveaux ≥ 2 sans pré-test
niveaux_sans_pretest = conn.execute("""
    SELECT n.id, n.numero, f.nom AS formation_nom
    FROM niveaux n
    JOIN formations f ON f.id = n.formation_id
    LEFT JOIN pretests p ON p.niveau_id = n.id
    WHERE n.numero >= 2 AND p.id IS NULL
""").fetchall()

for niveau in niveaux_sans_pretest:
    creer_pretest_generique(niveau[0], niveau[2], niveau[1])

print(f"✅ {len(niveaux_sans_pretest)} pré-tests générés automatiquement.")

# =========================================================
# FINALISATION
# =========================================================

conn.commit()
conn.close()

print("=" * 60)
print("✅ Base Soft Learn créée avec succès !")
print("=" * 60)
print("8 formations · 24 niveaux · 5000/8000/10000 DA")
print("Chapitres · Leçons · Exercices · Pré-tests · IA")
print("-" * 60)
print("Admin   : admin@softlearn.com    / admin123")
print("Trainer : trainer@softlearn.com  / trainer123")
print("Student : student@softlearn.com  / student123")
print("=" * 60)