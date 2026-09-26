# =========================================================
# SOFT LEARN — EXERCICES ET EVALUATION FINALE PYTHON N1
# =========================================================

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

# =========================================================
# 1. RECUPERER LE NIVEAU ET LES LECONS
# =========================================================

py_n1 = conn.execute("""
    SELECT n.id FROM niveaux n
    JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = 'Python' AND n.numero = 1
""").fetchone()

if not py_n1:
    print("[ERREUR] Python Niveau 1 introuvable.")
    conn.close()
    exit(1)

niveau_id = py_n1[0]
print(f"[OK] Niveau Python N1 trouve (ID = {niveau_id})")

# Recuperer les IDs des lecons par titre
def get_lecon_id(titre):
    row = conn.execute("""
        SELECT l.id FROM lecons l
        JOIN chapitres c ON c.id = l.chapitre_id
        WHERE c.niveau_id = ? AND l.titre = ?
    """, (niveau_id, titre)).fetchone()
    return row[0] if row else None

lecon_1_1 = get_lecon_id("Qu'est-ce que Python ?")
lecon_1_2 = get_lecon_id("Installer Python")
lecon_2_1 = get_lecon_id("Afficher avec print()")
lecon_2_2 = get_lecon_id("Saisir avec input()")
lecon_2_3 = get_lecon_id("Les variables")
lecon_2_4 = get_lecon_id("Les conditions")
lecon_2_5 = get_lecon_id("Les boucles")
lecon_2_6 = get_lecon_id("Les fonctions")

print("[INFO] IDs des lecons recuperes.")

# Supprimer les anciens exercices de ce niveau
conn.execute("DELETE FROM exercices WHERE niveau_id = ?", (niveau_id,))
conn.commit()
print("[OK] Anciens exercices supprimes.")

# =========================================================
# 2. CREATION DES 12 EXERCICES (2 par lecon)
# =========================================================

print("[INFO] Creation des exercices...")

# =========================================================
# LECON 1.1 : QU'EST-CE QUE PYTHON ?
# =========================================================

# Exercice 1.1.a - TEXTE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        contenu, reponse_attendue
    )
    VALUES (?, ?, ?, ?, 'texte', ?, ?)
""", (
    niveau_id, lecon_1_1,
    "Exercice 1.1.a : Definition de Python",
    "Redigez un court texte (5-10 lignes) expliquant ce qu'est Python.",
    "Expliquez dans vos propres mots :\n"
    "1. Ce qu'est Python\n"
    "2. Au moins 3 de ses caracteristiques\n"
    "3. Trois domaines dans lesquels il est utilise",
    "Python est un langage de programmation interprete, multi-paradigme "
    "et open source, cree par Guido van Rossum en 1991. Sa syntaxe simple "
    "et lisible en fait un excellent langage pour debuter. Il est "
    "interprete (execute ligne par ligne), type dynamiquement (pas besoin "
    "de declarer le type) et portable (fonctionne sur tous les systemes). "
    "Python est utilise dans de nombreux domaines : le developpement web "
    "(Django, Flask), la data science (Pandas, NumPy), l'intelligence "
    "artificielle (TensorFlow, PyTorch), le calcul scientifique et "
    "l'automatisation de taches."
))

print("  [OK] Exercice 1.1.a cree.")

# Exercice 1.1.b - QCM
qcm_1_1 = [
    {
        "question": "Qui a cree le langage Python ?",
        "options": ["Bill Gates", "Guido van Rossum", "Mark Zuckerberg", "Linus Torvalds"],
        "bonne": 1
    },
    {
        "question": "En quelle annee Python a-t-il ete cree ?",
        "options": ["1985", "1991", "2000", "2010"],
        "bonne": 1
    },
    {
        "question": "Que signifie 'Python est interprete' ?",
        "options": [
            "Le code est compile en binaire avant execution",
            "Le code est execute ligne par ligne sans compilation",
            "Le code est traduit en arabe",
            "Le code doit etre ecrit en anglais"
        ],
        "bonne": 1
    },
    {
        "question": "Quelle version de Python faut-il utiliser aujourd'hui ?",
        "options": ["Python 1", "Python 2", "Python 3", "Peu importe"],
        "bonne": 2
    }
]

conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        qcm_data, corrige_auto
    )
    VALUES (?, ?, ?, ?, 'qcm', ?, 1)
""", (
    niveau_id, lecon_1_1,
    "Exercice 1.1.b : QCM Introduction",
    "Testez vos connaissances sur les bases de Python.",
    json.dumps(qcm_1_1)
))

print("  [OK] Exercice 1.1.b cree.")

# =========================================================
# LECON 1.2 : INSTALLER PYTHON
# =========================================================

# Exercice 1.2.a - TEXTE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        contenu, reponse_attendue
    )
    VALUES (?, ?, ?, ?, 'texte', ?, ?)
""", (
    niveau_id, lecon_1_2,
    "Exercice 1.2.a : Etapes d'installation",
    "Decrivez les etapes pour installer Python sur Windows.",
    "Listez dans l'ordre les 4 etapes principales de l'installation "
    "de Python sur Windows, en precisant l'etape CRITIQUE a ne pas oublier.",
    "1. Telecharger le fichier .exe depuis python.org\n"
    "2. Lancer l'installateur\n"
    "3. CRITIQUE : cocher 'Add Python to PATH'\n"
    "4. Cliquer sur 'Install Now' et attendre la fin"
))

print("  [OK] Exercice 1.2.a cree.")

# Exercice 1.2.b - QCM
qcm_1_2 = [
    {
        "question": "Sur quel site officiel telecharge-t-on Python ?",
        "options": ["python.com", "python.org", "python.net", "python.io"],
        "bonne": 1
    },
    {
        "question": "Sur Windows, quelle case faut-il IMPERATIVEMENT cocher ?",
        "options": [
            "Install for all users",
            "Add Python to PATH",
            "Install pip",
            "Create shortcuts"
        ],
        "bonne": 1
    },
    {
        "question": "Quelle commande verifie que Python est installe ?",
        "options": [
            "python --check",
            "python --version",
            "python --info",
            "python --status"
        ],
        "bonne": 1
    },
    {
        "question": "Quelle est l'extension d'un fichier Python ?",
        "options": [".python", ".pt", ".py", ".pyt"],
        "bonne": 2
    },
    {
        "question": "Quel editeur de code est recommande pour debuter ?",
        "options": ["Notepad", "VS Code", "Sublime", "Nano"],
        "bonne": 1
    }
]

conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        qcm_data, corrige_auto
    )
    VALUES (?, ?, ?, ?, 'qcm', ?, 1)
""", (
    niveau_id, lecon_1_2,
    "Exercice 1.2.b : QCM Installation",
    "Testez vos connaissances sur l'installation de Python.",
    json.dumps(qcm_1_2)
))

print("  [OK] Exercice 1.2.b cree.")

# =========================================================
# LECON 2.1 : AFFICHER AVEC PRINT()
# =========================================================

# Exercice 2.1.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_1,
    "Exercice 2.1.a : Premier affichage",
    "Ecrivez un programme qui affiche 3 lignes.",
    "Affichez exactement 3 lignes :\n"
    "1. Votre nom complet\n"
    "2. Votre age\n"
    "3. La phrase : 'J'apprends Python chez Soft Learn !'",
    "print(\"Ahmed Benali\")\n"
    "print(22)\n"
    "print(\"J'apprends Python chez Soft Learn !\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.1.a cree.")

# Exercice 2.1.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_1,
    "Exercice 2.1.b : Menu formate",
    "Creez un menu avec des separateurs.",
    "Affichez un menu encadre par des lignes de '=' (40 caracteres) "
    "avec 3 options numerotees :\n"
    "1. Nouvelle partie\n"
    "2. Charger une partie\n"
    "3. Quitter",
    "print(\"=\" * 40)\n"
    "print(\"       MENU PRINCIPAL\")\n"
    "print(\"=\" * 40)\n"
    "print(\"1. Nouvelle partie\")\n"
    "print(\"2. Charger une partie\")\n"
    "print(\"3. Quitter\")\n"
    "print(\"=\" * 40)",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.1.b cree.")

# =========================================================
# LECON 2.2 : SAISIR AVEC INPUT()
# =========================================================

# Exercice 2.2.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_2,
    "Exercice 2.2.a : Presentation interactive",
    "Demandez des informations a l'utilisateur.",
    "Demandez :\n"
    "- Le prenom (input)\n"
    "- L'age (input + int)\n"
    "- La ville (input)\n\n"
    "Puis affichez : 'Bonjour [prenom], vous avez [age] ans et habitez a [ville].'",
    "prenom = input(\"Votre prenom : \")\n"
    "age = int(input(\"Votre age : \"))\n"
    "ville = input(\"Votre ville : \")\n\n"
    "print(f\"Bonjour {prenom}, vous avez {age} ans et habitez a {ville}.\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.2.a cree.")

# Exercice 2.2.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_2,
    "Exercice 2.2.b : Calculatrice simple",
    "Creez une mini calculatrice.",
    "Demandez 2 nombres (float), puis affichez :\n"
    "- Leur somme\n"
    "- Leur difference\n"
    "- Leur produit\n"
    "- Leur quotient",
    "a = float(input(\"Premier nombre : \"))\n"
    "b = float(input(\"Deuxieme nombre : \"))\n\n"
    "print(f\"Somme      : {a + b}\")\n"
    "print(f\"Difference : {a - b}\")\n"
    "print(f\"Produit    : {a * b}\")\n"
    "print(f\"Quotient   : {a / b:.2f}\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.2.b cree.")

# =========================================================
# LECON 2.3 : LES VARIABLES
# =========================================================

# Exercice 2.3.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_3,
    "Exercice 2.3.a : Fiche etudiant",
    "Creez des variables pour un etudiant.",
    "Creez 4 variables :\n"
    "- nom (str)\n"
    "- age (int)\n"
    "- moyenne (float)\n"
    "- est_inscrit (bool)\n\n"
    "Affichez-les avec f-string.",
    "nom = \"Ahmed Benali\"\n"
    "age = 22\n"
    "moyenne = 15.75\n"
    "est_inscrit = True\n\n"
    "print(f\"Nom : {nom}\")\n"
    "print(f\"Age : {age}\")\n"
    "print(f\"Moyenne : {moyenne}\")\n"
    "print(f\"Inscrit : {est_inscrit}\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.3.a cree.")

# Exercice 2.3.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_3,
    "Exercice 2.3.b : Conversion de devises",
    "Convertissez un montant en dinars vers euros.",
    "Demandez un montant en DA et un taux de change (par defaut 0.0068). "
    "Calculez et affichez le montant en euros.",
    "montant_da = float(input(\"Montant en DA : \"))\n"
    "taux = float(input(\"Taux de change (1 DA = ? EUR) : \") or 0.0068)\n\n"
    "montant_eur = montant_da * taux\n"
    "print(f\"{montant_da} DA = {montant_eur:.2f} EUR\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.3.b cree.")

# =========================================================
# LECON 2.4 : LES CONDITIONS
# =========================================================

# Exercice 2.4.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_4,
    "Exercice 2.4.a : Pair ou impair",
    "Verifiez si un nombre est pair ou impair.",
    "Demandez un nombre entier a l'utilisateur, puis affichez "
    "'Pair' ou 'Impair' selon le resultat.",
    "nombre = int(input(\"Entrez un nombre : \"))\n\n"
    "if nombre % 2 == 0:\n"
    "    print(\"Pair\")\n"
    "else:\n"
    "    print(\"Impair\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.4.a cree.")

# Exercice 2.4.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_4,
    "Exercice 2.4.b : Mention du bac",
    "Attribuez une mention selon la moyenne.",
    "Demandez une note (0-20) et affichez la mention :\n"
    "- >= 16 : 'Tres bien'\n"
    "- >= 14 : 'Bien'\n"
    "- >= 12 : 'Assez bien'\n"
    "- >= 10 : 'Passable'\n"
    "- < 10 : 'Insuffisant'",
    "note = float(input(\"Votre note : \"))\n\n"
    "if note >= 16:\n"
    "    print(\"Tres bien\")\n"
    "elif note >= 14:\n"
    "    print(\"Bien\")\n"
    "elif note >= 12:\n"
    "    print(\"Assez bien\")\n"
    "elif note >= 10:\n"
    "    print(\"Passable\")\n"
    "else:\n"
    "    print(\"Insuffisant\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.4.b cree.")

# =========================================================
# LECON 2.5 : LES BOUCLES
# =========================================================

# Exercice 2.5.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_5,
    "Exercice 2.5.a : Table de multiplication",
    "Affichez la table de multiplication d'un nombre.",
    "Demandez un nombre, puis affichez sa table de multiplication "
    "de 1 a 10 avec le format : 'n x i = resultat'.",
    "nombre = int(input(\"Quelle table ? \"))\n\n"
    "for i in range(1, 11):\n"
    "    print(f\"{nombre} x {i} = {nombre * i}\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.5.a cree.")

# Exercice 2.5.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_5,
    "Exercice 2.5.b : Somme des nombres",
    "Calculez la somme des nombres de 1 a N.",
    "Demandez un nombre N, puis calculez et affichez "
    "la somme des nombres de 1 a N avec une boucle.",
    "n = int(input(\"Entrez N : \"))\n"
    "somme = 0\n\n"
    "for i in range(1, n + 1):\n"
    "    somme += i\n\n"
    "print(f\"La somme de 1 a {n} est {somme}\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.5.b cree.")

# =========================================================
# LECON 2.6 : LES FONCTIONS
# =========================================================

# Exercice 2.6.a - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_6,
    "Exercice 2.6.a : Aire du rectangle",
    "Creez une fonction qui calcule l'aire d'un rectangle.",
    "Definissez une fonction calculer_aire(longueur, largeur) qui "
    "retourne l'aire. Appelez-la avec (5, 3) et affichez le resultat.",
    "def calculer_aire(longueur, largeur):\n"
    "    return longueur * largeur\n\n"
    "aire = calculer_aire(5, 3)\n"
    "print(f\"Aire : {aire}\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.6.a cree.")

# Exercice 2.6.b - CODE
conn.execute("""
    INSERT INTO exercices(
        niveau_id, lecon_id, titre, description, type,
        langage, contenu, reponse_attendue, plateforme_url
    )
    VALUES (?, ?, ?, ?, 'code', 'python', ?, ?, ?)
""", (
    niveau_id, lecon_2_6,
    "Exercice 2.6.b : Fonction de salutation",
    "Creez une fonction qui salue avec un message personnalise.",
    "Definissez une fonction saluer(nom, message='Bonjour') qui "
    "affiche : 'message, nom !'. Testez avec 2 appels : "
    "saluer('Ahmed') et saluer('Sara', 'Salut').",
    "def saluer(nom, message=\"Bonjour\"):\n"
    "    print(f\"{message}, {nom} !\")\n\n"
    "saluer(\"Ahmed\")\n"
    "saluer(\"Sara\", \"Salut\")",
    "https://colab.research.google.com/"
))

print("  [OK] Exercice 2.6.b cree.")

# =========================================================
# 3. EVALUATION FINALE (QCM 20 questions)
# =========================================================

print("[INFO] Creation de l'evaluation finale...")

qcm_final = [
    {
        "question": "Qui a cree le langage Python ?",
        "options": ["Bill Gates", "Guido van Rossum", "Linus Torvalds", "Mark Zuckerberg"],
        "bonne": 1
    },
    {
        "question": "En quelle annee Python a-t-il ete cree ?",
        "options": ["1985", "1991", "2000", "2010"],
        "bonne": 1
    },
    {
        "question": "Quelle version de Python faut-il utiliser ?",
        "options": ["Python 1", "Python 2", "Python 3", "Peu importe"],
        "bonne": 2
    },
    {
        "question": "Que fait la fonction print() ?",
        "options": [
            "Elle lit une saisie utilisateur",
            "Elle affiche du texte ou des valeurs",
            "Elle calcule une somme",
            "Elle supprime une variable"
        ],
        "bonne": 1
    },
    {
        "question": "Que retourne TOUJOURS la fonction input() ?",
        "options": ["Un entier", "Un decimal", "Une chaine (str)", "Un booleen"],
        "bonne": 2
    },
    {
        "question": "Quelle fonction convertit une chaine en entier ?",
        "options": ["str()", "int()", "float()", "num()"],
        "bonne": 1
    },
    {
        "question": "Comment declare-t-on une variable en Python ?",
        "options": ["var x = 5", "int x = 5", "x = 5", "let x = 5"],
        "bonne": 2
    },
    {
        "question": "Quel est le type de la valeur 3.14 en Python ?",
        "options": ["int", "float", "str", "bool"],
        "bonne": 1
    },
    {
        "question": "Quel est le nom de la convention de nommage en Python ?",
        "options": ["camelCase", "PascalCase", "snake_case", "kebab-case"],
        "bonne": 2
    },
    {
        "question": "Que fait l'operateur '==' en Python ?",
        "options": [
            "Il assigne une valeur",
            "Il compare deux valeurs",
            "Il additionne",
            "Il multiplie"
        ],
        "bonne": 1
    },
    {
        "question": "Quel mot-cle utilise-t-on pour definir une fonction ?",
        "options": ["function", "def", "func", "define"],
        "bonne": 1
    },
    {
        "question": "Que fait le mot-cle 'return' dans une fonction ?",
        "options": [
            "Il affiche un message",
            "Il arrete le programme",
            "Il renvoie une valeur",
            "Il efface la memoire"
        ],
        "bonne": 2
    },
    {
        "question": "Quelle est la syntaxe correcte de la structure if ?",
        "options": [
            "if x > 5 { }",
            "if x > 5:",
            "if (x > 5)",
            "IF x > 5 THEN"
        ],
        "bonne": 1
    },
    {
        "question": "Combien d'espaces faut-il utiliser pour l'indentation en Python ?",
        "options": ["1", "2", "4", "8"],
        "bonne": 2
    },
    {
        "question": "Quelle boucle utilise-t-on pour parcourir une liste ?",
        "options": ["while", "for", "loop", "repeat"],
        "bonne": 1
    },
    {
        "question": "Que fait range(5) ?",
        "options": [
            "Genere 1, 2, 3, 4, 5",
            "Genere 0, 1, 2, 3, 4",
            "Genere 0, 1, 2, 3, 4, 5",
            "Genere 5, 4, 3, 2, 1"
        ],
        "bonne": 1
    },
    {
        "question": "Que fait le mot-cle 'break' dans une boucle ?",
        "options": [
            "Il saute une iteration",
            "Il sort de la boucle",
            "Il redemarre la boucle",
            "Il met en pause"
        ],
        "bonne": 1
    },
    {
        "question": "Que fait le mot-cle 'continue' dans une boucle ?",
        "options": [
            "Il saute l'iteration en cours",
            "Il sort de la boucle",
            "Il redemarre la boucle",
            "Il met en pause"
        ],
        "bonne": 0
    },
    {
        "question": "Quelle est la bonne syntaxe pour une f-string ?",
        "options": [
            "print('Bonjour' + {nom})",
            "print('Bonjour %s' % nom)",
            "print(f'Bonjour {nom}')",
            "print('Bonjour', {nom})"
        ],
        "bonne": 2
    },
    {
        "question": "Que fait l'operateur '*' applique a une chaine ?",
        "options": [
            "Il multiplie la chaine par un nombre",
            "Il repete la chaine N fois",
            "Il copie la chaine",
            "Il inverse la chaine"
        ],
        "bonne": 1
    }
]

conn.execute("""
    INSERT INTO exercices(
        niveau_id, titre, description, type,
        qcm_data, corrige_auto, est_evaluation_finale
    )
    VALUES (?, ?, ?, 'qcm', ?, 1, 1)
""", (
    niveau_id,
    "Evaluation finale - Certification Python N1",
    "Evaluez vos connaissances sur l'ensemble du niveau. "
    "Seuil de reussite : 70% (14/20). En cas de reussite, "
    "vous obtiendrez votre certificat Soft Learn.",
    json.dumps(qcm_final)
))

print("  [OK] Evaluation finale creee.")

# =========================================================
# 4. FINALISATION
# =========================================================

conn.commit()
conn.close()

print()
print("=" * 60)
print("[OK] EXERCICES ET EVALUATION CREES AVEC SUCCES")
print("=" * 60)
print("12 exercices (2 par lecon)")
print("1 evaluation finale de certification (20 questions)")
print("=" * 60)