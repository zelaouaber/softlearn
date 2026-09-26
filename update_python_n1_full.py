# =========================================================
# SOFT LEARN — MISE A JOUR COMPLETE PYTHON N1 (PostgreSQL)
# - 16 exercices de lecon (2 par lecon)
# - 1 evaluation finale QCM (20 questions)
# - 5 exercices de code pour l'evaluation finale
# =========================================================

import os
import json
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("[ERREUR] DATABASE_URL non definie.")
    exit(1)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# =========================================================
# 1. RECUPERER LE NIVEAU PYTHON N1
# =========================================================

cur.execute("""
    SELECT n.id FROM niveaux n
    JOIN formations f ON f.id = n.formation_id
    WHERE f.nom = 'Python' AND n.numero = 1
""")
row = cur.fetchone()
if not row:
    print("[ERREUR] Python N1 introuvable.")
    exit(1)
niveau_id = row[0]
print(f"[OK] Python N1 trouve (id={niveau_id})")

# =========================================================
# 2. RECUPERER LES IDs DES LECONS
# =========================================================

def get_lecon_id(titre):
    cur.execute("""
        SELECT l.id FROM lecons l
        JOIN chapitres c ON c.id = l.chapitre_id
        WHERE c.niveau_id = %s AND l.titre = %s
    """, (niveau_id, titre))
    r = cur.fetchone()
    return r[0] if r else None

lecons = {
    "1.1": get_lecon_id("Qu'est-ce que Python ?"),
    "1.2": get_lecon_id("Installer Python"),
    "2.1": get_lecon_id("Afficher avec print()"),
    "2.2": get_lecon_id("Saisir avec input()"),
    "2.3": get_lecon_id("Les variables"),
    "2.4": get_lecon_id("Les conditions"),
    "2.5": get_lecon_id("Les boucles"),
    "2.6": get_lecon_id("Les fonctions"),
}
print("[INFO] IDs lecons :", lecons)

# =========================================================
# 3. SUPPRESSION ANCIENS EXERCICES DU NIVEAU
# =========================================================

cur.execute("""
    DELETE FROM soumissions
    WHERE exercice_id IN (SELECT id FROM exercices WHERE niveau_id = %s)
""", (niveau_id,))

cur.execute("DELETE FROM exercices WHERE niveau_id = %s", (niveau_id,))

print("[OK] Anciens exercices supprimes.")

# =========================================================
# 4. EXERCICES DE LECON (2 par lecon = 16 au total)
# =========================================================

print("\n[INFO] Creation des 16 exercices de lecon...")

exercices_lecons = [
    # ---- Lecon 1.1 : Qu'est-ce que Python ? ----
    {"lecon": "1.1", "titre": "Ex 1.1.a : Definition de Python",
     "description": "Redigez un court texte expliquant ce qu'est Python.",
     "type": "texte",
     "contenu": "Expliquez dans vos propres mots :\n1. Ce qu'est Python\n2. Au moins 3 caracteristiques\n3. 3 domaines d'utilisation",
     "reponse_attendue": "Python est un langage interprete, multi-paradigme, open source."},
    {"lecon": "1.1", "titre": "Ex 1.1.b : QCM Introduction",
     "description": "Testez vos connaissances sur les bases.",
     "type": "qcm",
     "qcm": [
         {"question": "Qui a cree Python ?", "options": ["Bill Gates", "Guido van Rossum", "Zuckerberg", "Linus"], "bonne": 1},
         {"question": "En quelle annee ?", "options": ["1985", "1991", "2000", "2010"], "bonne": 1},
         {"question": "'Python est interprete' signifie ?", "options": ["Compile avant execution", "Execute ligne par ligne", "Traduit en arabe", "En anglais"], "bonne": 1},
         {"question": "Version a utiliser ?", "options": ["Python 1", "Python 2", "Python 3", "Peu importe"], "bonne": 2},
     ]},

    # ---- Lecon 1.2 : Installer Python ----
    {"lecon": "1.2", "titre": "Ex 1.2.a : Etapes d'installation",
     "description": "Decrivez les etapes d'installation sur Windows.",
     "type": "texte",
     "contenu": "Listez dans l'ordre les 4 etapes, en precisant l'etape CRITIQUE.",
     "reponse_attendue": "1. Telecharger .exe\n2. Lancer installateur\n3. Cocher 'Add Python to PATH'\n4. Install Now"},
    {"lecon": "1.2", "titre": "Ex 1.2.b : QCM Installation",
     "description": "Testez vos connaissances sur l'installation.",
     "type": "qcm",
     "qcm": [
         {"question": "Site officiel ?", "options": ["python.com", "python.org", "python.net", "python.io"], "bonne": 1},
         {"question": "Case a cocher OBLIGATOIREMENT ?", "options": ["For all users", "Add Python to PATH", "Install pip", "Shortcuts"], "bonne": 1},
         {"question": "Commande pour verifier ?", "options": ["python --check", "python --version", "python --info", "python --status"], "bonne": 1},
         {"question": "Extension fichier Python ?", "options": [".python", ".pt", ".py", ".pyt"], "bonne": 2},
         {"question": "Editeur recommande ?", "options": ["Notepad", "VS Code", "Sublime", "Nano"], "bonne": 1},
     ]},

    # ---- Lecon 2.1 : Afficher avec print() ----
    {"lecon": "2.1", "titre": "Ex 2.1.a : Premier affichage",
     "description": "Ecrivez un programme qui affiche 3 lignes.",
     "type": "code", "langage": "python",
     "contenu": "Affichez :\n1. Votre nom complet\n2. Votre age\n3. La phrase : 'J'apprends Python chez Soft Learn !'",
     "reponse_attendue": 'print("Ahmed Benali")\nprint(22)\nprint("J\'apprends Python chez Soft Learn !")',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.1", "titre": "Ex 2.1.b : Menu formate",
     "description": "Creez un menu avec des separateurs.",
     "type": "code", "langage": "python",
     "contenu": "Affichez un menu encadre par 40 '=' avec 3 options numerotees.",
     "reponse_attendue": 'print("=" * 40)\nprint("   MENU PRINCIPAL")\nprint("=" * 40)\nprint("1. Nouvelle partie")\nprint("2. Charger une partie")\nprint("3. Quitter")\nprint("=" * 40)',
     "plateforme_url": "https://colab.research.google.com/"},

    # ---- Lecon 2.2 : Saisir avec input() ----
    {"lecon": "2.2", "titre": "Ex 2.2.a : Presentation interactive",
     "description": "Demandez des informations a l'utilisateur.",
     "type": "code", "langage": "python",
     "contenu": "Demandez prenom, age, ville et affichez une phrase.",
     "reponse_attendue": 'prenom = input("Prenom : ")\nage = int(input("Age : "))\nville = input("Ville : ")\nprint(f"Bonjour {prenom}, {age} ans, a {ville}.")',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.2", "titre": "Ex 2.2.b : Calculatrice simple",
     "description": "Creez une mini calculatrice.",
     "type": "code", "langage": "python",
     "contenu": "Demandez 2 nombres float, affichez somme, difference, produit, quotient.",
     "reponse_attendue": 'a = float(input("a : "))\nb = float(input("b : "))\nprint(a+b, a-b, a*b, a/b)',
     "plateforme_url": "https://colab.research.google.com/"},

    # ---- Lecon 2.3 : Variables ----
    {"lecon": "2.3", "titre": "Ex 2.3.a : Fiche etudiant",
     "description": "Creez des variables pour un etudiant.",
     "type": "code", "langage": "python",
     "contenu": "Creez nom (str), age (int), moyenne (float), est_inscrit (bool) et affichez-les.",
     "reponse_attendue": 'nom = "Ahmed"\nage = 22\nmoyenne = 15.75\nest_inscrit = True\nprint(nom, age, moyenne, est_inscrit)',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.3", "titre": "Ex 2.3.b : Conversion devises",
     "description": "Convertissez DA vers EUR.",
     "type": "code", "langage": "python",
     "contenu": "Demandez un montant en DA et un taux, affichez en EUR.",
     "reponse_attendue": 'da = float(input("DA : "))\ntaux = 0.0068\neur = da * taux\nprint(f"{da} DA = {eur:.2f} EUR")',
     "plateforme_url": "https://colab.research.google.com/"},

    # ---- Lecon 2.4 : Conditions ----
    {"lecon": "2.4", "titre": "Ex 2.4.a : Pair ou impair",
     "description": "Verifiez la parite.",
     "type": "code", "langage": "python",
     "contenu": "Demandez un nombre entier, affichez Pair ou Impair.",
     "reponse_attendue": 'n = int(input("Nombre : "))\nif n % 2 == 0:\n    print("Pair")\nelse:\n    print("Impair")',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.4", "titre": "Ex 2.4.b : Mention du bac",
     "description": "Attribuez une mention selon la note.",
     "type": "code", "langage": "python",
     "contenu": "Note 0-20 :\n>=16 TB\n>=14 B\n>=12 AB\n>=10 P\n<10 Insuffisant",
     "reponse_attendue": 'note = float(input("Note : "))\nif note >= 16:\n    print("TB")\nelif note >= 14:\n    print("B")\nelif note >= 12:\n    print("AB")\nelif note >= 10:\n    print("P")\nelse:\n    print("Insuffisant")',
     "plateforme_url": "https://colab.research.google.com/"},

    # ---- Lecon 2.5 : Boucles ----
    {"lecon": "2.5", "titre": "Ex 2.5.a : Table multiplication",
     "description": "Affichez la table d'un nombre.",
     "type": "code", "langage": "python",
     "contenu": "Demandez un nombre, affichez sa table de 1 a 10.",
     "reponse_attendue": 'n = int(input("Table : "))\nfor i in range(1, 11):\n    print(f"{n} x {i} = {n*i}")',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.5", "titre": "Ex 2.5.b : Somme 1 a N",
     "description": "Calculez la somme de 1 a N.",
     "type": "code", "langage": "python",
     "contenu": "Demandez N, calculez la somme avec une boucle for.",
     "reponse_attendue": 'n = int(input("N : "))\ns = 0\nfor i in range(1, n+1):\n    s += i\nprint(s)',
     "plateforme_url": "https://colab.research.google.com/"},

    # ---- Lecon 2.6 : Fonctions ----
    {"lecon": "2.6", "titre": "Ex 2.6.a : Aire rectangle",
     "description": "Creez une fonction aire.",
     "type": "code", "langage": "python",
     "contenu": "Definissez calculer_aire(longueur, largeur), appelez avec (5, 3).",
     "reponse_attendue": 'def calculer_aire(l, L):\n    return l * L\nprint(calculer_aire(5, 3))',
     "plateforme_url": "https://colab.research.google.com/"},
    {"lecon": "2.6", "titre": "Ex 2.6.b : Fonction salutation",
     "description": "Creez une fonction qui salue.",
     "type": "code", "langage": "python",
     "contenu": "Definissez saluer(nom, message='Bonjour'). Testez avec 2 appels.",
     "reponse_attendue": 'def saluer(nom, message="Bonjour"):\n    print(f"{message}, {nom} !")\nsaluer("Ahmed")\nsaluer("Sara", "Salut")',
     "plateforme_url": "https://colab.research.google.com/"},
]

for exo in exercices_lecons:
    lecon_id = lecons.get(exo["lecon"])
    cur.execute("""
        INSERT INTO exercices(
            niveau_id, lecon_id, titre, description, type,
            langage, contenu, reponse_attendue, qcm_data,
            plateforme_url, corrige_auto, est_evaluation_finale, partie
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'principal')
    """, (
        niveau_id,
        lecon_id,
        exo["titre"],
        exo.get("description"),
        exo["type"],
        exo.get("langage"),
        exo.get("contenu"),
        exo.get("reponse_attendue"),
        json.dumps(exo["qcm"]) if exo.get("qcm") else None,
        exo.get("plateforme_url"),
        1 if exo["type"] == "qcm" else 0,
    ))
    print(f"  [OK] {exo['titre']}")

# =========================================================
# 5. EVALUATION FINALE — PARTIE 1 : QCM (20 questions)
# =========================================================

print("\n[INFO] Creation de l'evaluation finale - Partie 1 QCM...")

qcm_final = [
    {"question": "Qui a cree le langage Python ?", "options": ["Bill Gates", "Guido van Rossum", "Linus Torvalds", "Mark Zuckerberg"], "bonne": 1},
    {"question": "En quelle annee Python a-t-il ete cree ?", "options": ["1985", "1991", "2000", "2010"], "bonne": 1},
    {"question": "Quelle version de Python faut-il utiliser ?", "options": ["Python 1", "Python 2", "Python 3", "Peu importe"], "bonne": 2},
    {"question": "Que fait la fonction print() ?", "options": ["Elle lit une saisie utilisateur", "Elle affiche du texte ou des valeurs", "Elle calcule une somme", "Elle supprime une variable"], "bonne": 1},
    {"question": "Que retourne TOUJOURS la fonction input() ?", "options": ["Un entier", "Un decimal", "Une chaine (str)", "Un booleen"], "bonne": 2},
    {"question": "Quelle fonction convertit une chaine en entier ?", "options": ["str()", "int()", "float()", "num()"], "bonne": 1},
    {"question": "Comment declare-t-on une variable en Python ?", "options": ["var x = 5", "int x = 5", "x = 5", "let x = 5"], "bonne": 2},
    {"question": "Quel est le type de la valeur 3.14 en Python ?", "options": ["int", "float", "str", "bool"], "bonne": 1},
    {"question": "Quelle est la convention de nommage en Python ?", "options": ["camelCase", "PascalCase", "snake_case", "kebab-case"], "bonne": 2},
    {"question": "Que fait l'operateur '==' en Python ?", "options": ["Il assigne une valeur", "Il compare deux valeurs", "Il additionne", "Il multiplie"], "bonne": 1},
    {"question": "Quel mot-cle utilise-t-on pour definir une fonction ?", "options": ["function", "def", "func", "define"], "bonne": 1},
    {"question": "Que fait le mot-cle 'return' dans une fonction ?", "options": ["Il affiche un message", "Il arrete le programme", "Il renvoie une valeur", "Il efface la memoire"], "bonne": 2},
    {"question": "Quelle est la syntaxe correcte de la structure if ?", "options": ["if x > 5 { }", "if x > 5:", "if (x > 5)", "IF x > 5 THEN"], "bonne": 1},
    {"question": "Combien d'espaces faut-il utiliser pour l'indentation en Python ?", "options": ["1", "2", "4", "8"], "bonne": 2},
    {"question": "Quelle boucle utilise-t-on pour parcourir une liste ?", "options": ["while", "for", "loop", "repeat"], "bonne": 1},
    {"question": "Que fait range(5) ?", "options": ["Genere 1, 2, 3, 4, 5", "Genere 0, 1, 2, 3, 4", "Genere 0, 1, 2, 3, 4, 5", "Genere 5, 4, 3, 2, 1"], "bonne": 1},
    {"question": "Que fait le mot-cle 'break' dans une boucle ?", "options": ["Il saute une iteration", "Il sort de la boucle", "Il redemarre la boucle", "Il met en pause"], "bonne": 1},
    {"question": "Que fait le mot-cle 'continue' dans une boucle ?", "options": ["Il saute l'iteration en cours", "Il sort de la boucle", "Il redemarre la boucle", "Il met en pause"], "bonne": 0},
    {"question": "Quelle est la bonne syntaxe pour une f-string ?", "options": ["print('Bonjour' + {nom})", "print('Bonjour %s' % nom)", "print(f'Bonjour {nom}')", "print('Bonjour', {nom})"], "bonne": 2},
    {"question": "Que fait l'operateur '*' applique a une chaine ?", "options": ["Il multiplie la chaine par un nombre", "Il repete la chaine N fois", "Il copie la chaine", "Il inverse la chaine"], "bonne": 1},
]

cur.execute("""
    INSERT INTO exercices(
        niveau_id, titre, description, type,
        qcm_data, corrige_auto, est_evaluation_finale, partie
    ) VALUES (%s, %s, %s, 'qcm', %s, 1, 1, 'qcm')
""", (
    niveau_id,
    "Evaluation finale - Partie 1 : QCM",
    "20 questions a choix multiples. Chaque bonne reponse vaut 1 point. Total : 20 points.",
    json.dumps(qcm_final)
))
print("[OK] Partie 1 QCM creee (20 pts)")

# =========================================================
# 6. EVALUATION FINALE — PARTIE 2 : CODE (5 exercices)
# =========================================================

print("\n[INFO] Creation de l'evaluation finale - Partie 2 Code...")

exercices_code_final = [
    {
        "titre": "Evaluation - Exo 1 : Menu formate",
        "description": "Creez un menu encadre avec print().",
        "contenu": "Affichez un menu encadre par 40 '=' avec :\n- 'CERTIFICATION SOFT LEARN' au centre\n- 3 options numerotees\n- Un separateur final",
        "reponse_attendue": 'print("=" * 40)\nprint("   CERTIFICATION SOFT LEARN")\nprint("=" * 40)\nprint("1. Commencer")\nprint("2. Aide")\nprint("3. Quitter")\nprint("=" * 40)',
    },
    {
        "titre": "Evaluation - Exo 2 : Calculatrice interactive",
        "description": "Creez une calculatrice qui demande 2 nombres.",
        "contenu": "Demandez 2 nombres (float), affichez :\n- somme\n- difference\n- produit\n- quotient (2 decimales)",
        "reponse_attendue": 'a = float(input("a : "))\nb = float(input("b : "))\nprint(f"Somme : {a+b}")\nprint(f"Diff : {a-b}")\nprint(f"Prod : {a*b}")\nprint(f"Quot : {a/b:.2f}")',
    },
    {
        "titre": "Evaluation - Exo 3 : Pair ou impair",
        "description": "Verifiez si un nombre est pair ou impair.",
        "contenu": "Demandez un nombre entier, affichez 'Pair' ou 'Impair'.",
        "reponse_attendue": 'n = int(input("Nombre : "))\nif n % 2 == 0:\n    print("Pair")\nelse:\n    print("Impair")',
    },
    {
        "titre": "Evaluation - Exo 4 : Somme des N premiers nombres",
        "description": "Calculez la somme de 1 a N avec une boucle.",
        "contenu": "Demandez N, calculez et affichez la somme avec une boucle for.",
        "reponse_attendue": 'n = int(input("N : "))\ns = 0\nfor i in range(1, n+1):\n    s += i\nprint(s)',
    },
    {
        "titre": "Evaluation - Exo 5 : Fonction calcul IMC",
        "description": "Creez une fonction qui calcule l'IMC.",
        "contenu": "Definissez calculer_imc(poids, taille) retournant poids / taille**2. Appelez avec (70, 1.75).",
        "reponse_attendue": 'def calculer_imc(poids, taille):\n    return poids / (taille ** 2)\nprint(f"{calculer_imc(70, 1.75):.2f}")',
    },
]

for exo in exercices_code_final:
    cur.execute("""
        INSERT INTO exercices(
            niveau_id, titre, description, type, langage,
            contenu, reponse_attendue,
            corrige_auto, est_evaluation_finale, partie
        ) VALUES (%s, %s, %s, 'code', 'python', %s, %s, 0, 1, 'code')
    """, (niveau_id, exo["titre"], exo["description"],
          exo["contenu"], exo["reponse_attendue"]))
    print(f"  [OK] {exo['titre']}")

# =========================================================
# 7. COMMIT + VERIFICATION
# =========================================================

conn.commit()

cur.execute("SELECT COUNT(*) FROM exercices WHERE niveau_id = %s", (niveau_id,))
total = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM exercices
    WHERE niveau_id = %s AND est_evaluation_finale = 1
""", (niveau_id,))
final_count = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM exercices
    WHERE niveau_id = %s AND est_evaluation_finale = 0
""", (niveau_id,))
lecon_count = cur.fetchone()[0]

cur.close()
conn.close()

print("\n" + "=" * 60)
print("[OK] MISE A JOUR PYTHON N1 TERMINEE")
print("=" * 60)
print(f"Exercices de lecon          : {lecon_count}")
print(f"Evaluation finale           : {final_count}  (1 QCM + 5 code)")
print(f"Total                       : {total}")
print("=" * 60)
print("Evaluation finale = QCM (20 pts) + Code (5 x 4 pts) = 40 pts")
print("Seuil de reussite : 90% (36/40)")
print("=" * 60)