# =========================================================
# SOFT LEARN — MISE A JOUR EVALUATION FINALE MIXTE
# =========================================================

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

# ---------- AJOUT COLONNE 'partie' ----------
try:
    conn.execute("ALTER TABLE exercices ADD COLUMN partie TEXT DEFAULT 'principal'")
    print("[OK] Colonne 'partie' ajoutee.")
except sqlite3.OperationalError:
    print("[INFO] Colonne 'partie' existe deja.")

# ---------- RECUPERATION DU NIVEAU ----------
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

# ---------- SUPPRESSION DE L'ANCIENNE EVALUATION ----------
conn.execute("""
    DELETE FROM exercices
    WHERE niveau_id = ? AND est_evaluation_finale = 1
""", (niveau_id,))
conn.commit()
print("[OK] Ancienne evaluation finale supprimee.")

# =========================================================
# PARTIE 1 : QCM (20 questions)
# =========================================================

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
        "question": "Quelle est la convention de nommage en Python ?",
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
        qcm_data, corrige_auto, est_evaluation_finale, partie
    )
    VALUES (?, ?, ?, 'qcm', ?, 1, 1, 'qcm')
""", (
    niveau_id,
    "Evaluation finale - Partie 1 : QCM",
    "20 questions a choix multiples. Chaque bonne reponse vaut 1 point. "
    "Total de cette partie : 20 points.",
    json.dumps(qcm_final)
))

print("[OK] Partie 1 (QCM) creee.")

# =========================================================
# PARTIE 2 : EXERCICES DE CODE (5 exercices)
# =========================================================

exercices_code_final = [
    {
        "titre": "Evaluation - Exo 1 : Menu formate",
        "description": "Creez un menu encadre avec print().",
        "contenu": "Affichez un menu encadre par 40 '=' avec :\n"
                   "- 'CERTIFICATION SOFT LEARN' au centre\n"
                   "- 3 options numerotees (1, 2, 3)\n"
                   "- Un separateur final",
        "reponse_attendue": (
            "print(\"=\" * 40)\n"
            "print(\"   CERTIFICATION SOFT LEARN\")\n"
            "print(\"=\" * 40)\n"
            "print(\"1. Commencer\")\n"
            "print(\"2. Aide\")\n"
            "print(\"3. Quitter\")\n"
            "print(\"=\" * 40)"
        ),
        "points": 4
    },
    {
        "titre": "Evaluation - Exo 2 : Calculatrice interactive",
        "description": "Creez une calculatrice qui demande 2 nombres.",
        "contenu": "Demandez 2 nombres (float), puis affichez :\n"
                   "- Leur somme\n"
                   "- Leur difference\n"
                   "- Leur produit\n"
                   "- Leur quotient (2 decimales)",
        "reponse_attendue": (
            "a = float(input(\"Premier nombre : \"))\n"
            "b = float(input(\"Deuxieme nombre : \"))\n\n"
            "print(f\"Somme      : {a + b}\")\n"
            "print(f\"Difference : {a - b}\")\n"
            "print(f\"Produit    : {a * b}\")\n"
            "print(f\"Quotient   : {a / b:.2f}\")"
        ),
        "points": 4
    },
    {
        "titre": "Evaluation - Exo 3 : Pair ou impair",
        "description": "Verifiez si un nombre est pair ou impair.",
        "contenu": "Demandez un nombre entier a l'utilisateur, "
                   "puis affichez 'Pair' ou 'Impair'.",
        "reponse_attendue": (
            "nombre = int(input(\"Entrez un nombre : \"))\n\n"
            "if nombre % 2 == 0:\n"
            "    print(\"Pair\")\n"
            "else:\n"
            "    print(\"Impair\")"
        ),
        "points": 4
    },
    {
        "titre": "Evaluation - Exo 4 : Somme des N premiers nombres",
        "description": "Calculez la somme de 1 a N avec une boucle.",
        "contenu": "Demandez un nombre N, puis calculez et affichez "
                   "la somme des nombres de 1 a N avec une boucle for.",
        "reponse_attendue": (
            "n = int(input(\"Entrez N : \"))\n"
            "somme = 0\n\n"
            "for i in range(1, n + 1):\n"
            "    somme += i\n\n"
            "print(f\"La somme de 1 a {n} est {somme}\")"
        ),
        "points": 4
    },
    {
        "titre": "Evaluation - Exo 5 : Fonction de calcul d'IMC",
        "description": "Creez une fonction qui calcule l'IMC.",
        "contenu": "Definissez une fonction calculer_imc(poids, taille) "
                   "qui retourne l'IMC (poids / taille ** 2). "
                   "Appelez-la avec (70, 1.75) et affichez le resultat "
                   "arrondi a 2 decimales.",
        "reponse_attendue": (
            "def calculer_imc(poids, taille):\n"
            "    return poids / (taille ** 2)\n\n"
            "imc = calculer_imc(70, 1.75)\n"
            "print(f\"IMC : {imc:.2f}\")"
        ),
        "points": 4
    }
]

for exo in exercices_code_final:
    conn.execute("""
        INSERT INTO exercices(
            niveau_id, titre, description, type,
            langage, contenu, reponse_attendue,
            corrige_auto, est_evaluation_finale, partie
        )
        VALUES (?, ?, ?, 'code', 'python', ?, ?, 0, 1, 'code')
    """, (
        niveau_id,
        exo["titre"],
        exo["description"],
        exo["contenu"],
        exo["reponse_attendue"]
    ))
    print(f"  [OK] {exo['titre']} cree.")

conn.commit()
conn.close()

print()
print("=" * 60)
print("[OK] EVALUATION FINALE MIXTE CREEE")
print("=" * 60)
print("Partie 1 : QCM (20 questions) - 20 points")
print("Partie 2 : Code (5 exercices) - 20 points")
print("TOTAL : 40 points - Seuil de reussite : 28/40 (70%)")
print("=" * 60)