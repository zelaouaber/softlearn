# =========================================================
# SOFT LEARN — MISE À JOUR DU CONTENU PYTHON NIVEAU 1
# =========================================================

import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

# ---------- AJOUT DES COLONNES ----------

try:
    conn.execute("ALTER TABLE exercices ADD COLUMN lecon_id INTEGER")
    print("[OK] Colonne 'lecon_id' ajoutee.")
except sqlite3.OperationalError:
    print("[INFO] Colonne 'lecon_id' existe deja.")

try:
    conn.execute("ALTER TABLE exercices ADD COLUMN est_evaluation_finale INTEGER DEFAULT 0")
    print("[OK] Colonne 'est_evaluation_finale' ajoutee.")
except sqlite3.OperationalError:
    print("[INFO] Colonne 'est_evaluation_finale' existe deja.")

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

# ---------- SUPPRESSION ANCIEN CONTENU ----------

print("[INFO] Suppression de l'ancien contenu...")
conn.execute("DELETE FROM exercices WHERE niveau_id = ?", (niveau_id,))
conn.execute("DELETE FROM chapitres WHERE niveau_id = ?", (niveau_id,))
conn.commit()
print("[OK] Ancien contenu supprime.")

# =========================================================
# CHAPITRE 1
# =========================================================

chap1 = conn.execute("""
    INSERT INTO chapitres(niveau_id, numero, titre, description)
    VALUES (?, 1, ?, ?)
""", (niveau_id, "Introduction a Python",
      "Decouvrez Python et installez votre environnement")).lastrowid

print("[INFO] Chapitre 1 cree.")

# =========================================================
# LECON 1.1 : QU'EST-CE QUE PYTHON ?
# =========================================================

lecon_1_1 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Definir** ce qu'est Python et ses caracteristiques principales
- **Comprendre** pourquoi Python est aujourd'hui le langage le plus populaire
- **Identifier** les principaux domaines d'application de Python
- **Reconnaitre** la syntaxe de base a travers un premier exemple

---

## 1. Qu'est-ce que Python ?

**Python** est un **langage de programmation** cree par **Guido van Rossum** en **1991**. Son nom vient de la troupe d'humoristes britanniques Monty Python.

Un **langage de programmation** est un ensemble de regles permettant d'ecrire des **instructions** qu'un ordinateur peut comprendre et executer.

### Definition formelle

> Python est un langage de programmation **interprete**, **multi-paradigme**, **type dynamiquement** et **open source**, concu pour privilegier la **lisibilite** et la **simplicite** du code.

### Les 5 caracteristiques principales

| Caracteristique | Definition | Consequence |
| :--- | :--- | :--- |
| **Interprete** | Le code est execute ligne par ligne | Plus rapide a tester |
| **Multi-paradigme** | Supporte plusieurs styles | Procedural, objet, fonctionnel |
| **Type dynamiquement** | Pas de declaration du type | Code plus concis |
| **Open source** | Code source accessible | Gratuit, libre |
| **Portable** | Fonctionne sur tous les OS | Windows, macOS, Linux |

---

## 2. Pourquoi Python est-il si populaire ?

Python est **le langage numero 1** au classement **TIOBE** et **le plus utilise** sur Stack Overflow.

### Syntaxe claire et lisible

**En Python** (1 ligne) :

    print("Bonjour le monde")

**En Java** (5 lignes) :

    public class HelloWorld {
        public static void main(String[] args) {
            System.out.println("Bonjour le monde");
        }
    }

**En C++** (6 lignes) :

    #include <iostream>
    int main() {
        std::cout << "Bonjour le monde" << std::endl;
        return 0;
    }

Python demande **moins de code** pour le meme resultat.

### Ecosysteme immense

- Plus de 400 000 bibliotheques disponibles (PyPI)
- Des outils prets a l'emploi pour presque tous les besoins
- Une communaute active

### Demande professionnelle forte

- Langage numero 1 en Data Science et Intelligence Artificielle
- Tres recherche dans les offres d'emploi tech
- Salaires attractifs

---

## 3. Les grands domaines d'application

| Domaine | Bibliotheques | Exemples concrets |
| :--- | :--- | :--- |
| **Developpement Web** | Django, Flask | Instagram, Spotify (backend) |
| **Data Science** | Pandas, NumPy | Analyse marketing, previsions |
| **Intelligence Artificielle** | TensorFlow, PyTorch | Chatbots, reconnaissance d'images |
| **Calcul scientifique** | SciPy, SymPy | NASA, recherche medicale |
| **Automatisation** | Selenium, BeautifulSoup | Scraping, renommage de fichiers |

---

## 4. Votre premier programme Python

    print("Bonjour Soft Learn !")

### Decomposition

| Element | Role |
| :--- | :--- |
| `print` | Une fonction integree a Python |
| `(` et `)` | Les parentheses |
| `"..."` | Les guillemets delimitent une chaine |

### Resultat a l'ecran

    Bonjour Soft Learn !

---

## 5. Python 2 vs Python 3

| Critere | Python 2 | Python 3 |
| :--- | :--- | :--- |
| Sortie initiale | 2000 | 2008 |
| Fin de support | Janvier 2020 | En cours |
| Statut actuel | Obsolete | Recommande |
| Utilisation | Quasi nulle | 100% |

> **Regle absolue** : Utilisez **toujours Python 3**.

---

## 6. Points cles a retenir

- Python est un langage **interprete, multi-paradigme, type dynamiquement et open source**
- Cree en **1991** par **Guido van Rossum**
- Sa **syntaxe simple** en fait un excellent langage pour debuter
- Utilise dans le **web, la data, l'IA, la science et l'automatisation**
- Il faut **toujours utiliser Python 3**
- La fonction **print()** permet d'afficher du texte

---

## Prochaine etape

Vous savez maintenant ce qu'est Python. Installons-le.

=> **Lecon suivante : Installer Python**
"""

lecon_1_1_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 1, ?, ?, 25)
""", (chap1, "Qu'est-ce que Python ?", lecon_1_1)).lastrowid

print("  [OK] Lecon 1.1 creee.")

# =========================================================
# LECON 1.2 : INSTALLER PYTHON
# =========================================================

lecon_1_2 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Telecharger** Python depuis le site officiel
- **Installer** Python sur Windows, macOS ou Linux
- **Verifier** que l'installation fonctionne
- **Executer** votre premier programme Python

---

## 1. Deux options d'installation

| Option | Pour qui ? | Avantages | Inconvenients |
| :--- | :--- | :--- | :--- |
| **Python officiel** | Debutants | Leger, simple | Bibliotheques a installer |
| **Anaconda** | Data Scientists | 200+ bibliotheques | Plus lourd (~3 Go) |

**Recommandation** : Commencez avec **Python officiel**.

---

## 2. Telecharger Python

### Site officiel

Rendez-vous sur : https://www.python.org/downloads/

> **Rappel** : Choisissez **Python 3**, jamais Python 2.

### Fichier selon votre systeme

| Systeme | Fichier | Taille |
| :--- | :--- | :--- |
| **Windows 64 bits** | python-3.12.x-amd64.exe | ~25 Mo |
| **Windows 32 bits** | python-3.12.x.exe | ~25 Mo |
| **macOS** | python-3.12.x-macos11.pkg | ~35 Mo |
| **Linux** | Preinstalle : sudo apt install python3 | - |

---

## 3. Installation sur Windows (pas a pas)

### Etape 1 : Lancer l'installateur

Double-cliquez sur le fichier .exe telecharge.

### Etape 2 : Cocher "Add Python to PATH" (CRITIQUE)

En bas de la fenetre, cochez :

    [OK] Add Python 3.12 to PATH

> **CRITIQUE** : Sans cette case, Python ne fonctionnera pas depuis le terminal.

### Etape 3 : Install Now

Cliquez sur **Install Now**. L'installation prend ~2 minutes.

### Etape 4 : Verification

Ouvrez un **terminal** (Windows : touche Windows + tapez cmd) et tapez :

    python --version

**Resultat attendu :**

    Python 3.12.0

---

## 4. Installation sur macOS

### Etape 1 : Telecharger le .pkg

Double-cliquez sur le fichier telecharge.

### Etape 2 : Suivre l'assistant

Cliquez sur **Continuer** jusqu'a la fin.

### Etape 3 : Verifier

Ouvrez le **Terminal** et tapez :

    python3 --version

> Sur macOS, on utilise souvent python3 au lieu de python.

---

## 5. Installation sur Linux

### Verifier

    python3 --version

### Installer si necessaire (Ubuntu/Debian)

    sudo apt update
    sudo apt install python3 python3-pip

---

## 6. Tester avec un premier programme

### Creer un fichier test.py

    print("Installation reussie !")

Enregistrez sous **test.py**.

### Executer

    cd chemin/vers/le/dossier
    python test.py

**Resultat attendu :**

    Installation reussie !

---

## 7. Quel editeur de code choisir ?

| Editeur | Niveau | Avantages | Telechargement |
| :--- | :--- | :--- | :--- |
| **IDLE** | Debutant | Livre avec Python | Inclus |
| **VS Code** | Intermediaire | Leger, extensions | code.visualstudio.com |
| **PyCharm** | Avance | IDE complet | jetbrains.com/pycharm |
| **Jupyter** | Data Science | Ideal analyses | jupyter.org |

**Recommandation** : commencez avec **VS Code**.

---

## 8. Erreurs frequentes

| Erreur | Cause | Solution |
| :--- | :--- | :--- |
| python n'est pas reconnu | PATH non configure | Reinstaller en cochant "Add Python to PATH" |
| command not found: python | macOS/Linux | Utiliser python3 |
| Permission refusee | Droits administrateur | Clic droit -> Executer en tant qu'admin |

---

## 9. Points cles a retenir

- Telechargez Python depuis python.org (version 3.x)
- Sur Windows, cochez **"Add Python to PATH"**
- Verifiez avec python --version
- Un fichier Python a l'extension .py
- VS Code est un excellent editeur

---

## Prochaine etape

Python est installe ! Decouvrons maintenant print().

=> **Lecon suivante : Afficher avec print()**
"""

lecon_1_2_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 2, ?, ?, 20)
""", (chap1, "Installer Python", lecon_1_2)).lastrowid

print("  [OK] Lecon 1.2 creee.")

# =========================================================
# CHAPITRE 2
# =========================================================

chap2 = conn.execute("""
    INSERT INTO chapitres(niveau_id, numero, titre, description)
    VALUES (?, 2, ?, ?)
""", (niveau_id, "Bases du langage",
      "print, input, variables, conditions, boucles et fonctions")).lastrowid

print("[INFO] Chapitre 2 cree.")

# =========================================================
# LECON 2.1 : AFFICHER AVEC PRINT()
# =========================================================

lecon_2_1 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Utiliser** la fonction print() pour afficher du texte ou des valeurs
- **Formater** l'affichage avec virgules, f-strings et caracteres speciaux
- **Personnaliser** la sortie avec sep et end
- **Combiner** plusieurs print()

---

## 1. La fonction print()

### Definition

> print() est une **fonction integree** (built-in) qui affiche ses arguments dans la **console**.

### Syntaxe

    print(valeur1, valeur2, sep=" ", end="\\n")

| Parametre | Role | Valeur par defaut |
| :--- | :--- | :--- |
| valeur1, valeur2, ... | Ce qu'on veut afficher | - |
| sep | Separateur entre les valeurs | " " (espace) |
| end | Ce qui est ajoute a la fin | "\\n" (saut de ligne) |

---

## 2. Afficher du texte

    print("Bonjour")
    print('Bonjour aussi')
    print("Les deux fonctionnent !")

**Resultat :**

    Bonjour
    Bonjour aussi
    Les deux fonctionnent !

---

## 3. Afficher des nombres

    print(42)
    print(3.14)
    print(-10)

**Resultat :**

    42
    3.14
    -10

### Difference subtile

    print("42")   # Chaine (str)
    print(42)     # Entier (int)

---

## 4. Afficher plusieurs elements

### Methode 1 : virgules

    nom = "Ahmed"
    age = 25

    print("Nom :", nom, "| Age :", age)

**Resultat :**

    Nom : Ahmed | Age : 25

### Methode 2 : f-string (recommandee)

    nom = "Ahmed"
    age = 25

    print(f"Nom : {nom} | Age : {age}")

**Avantages :**

- Plus lisible
- Permet les calculs : f"Total : {prix * quantite}"
- Formatage : f"{prix:.2f}"

---

## 5. Les parametres sep et end

### sep : changer le separateur

    print("a", "b", "c", sep="-")

**Resultat :**

    a-b-c

### end : changer la fin de ligne

    print("Ligne 1", end=" ")
    print("Ligne 2")

**Resultat :**

    Ligne 1 Ligne 2

### Exemple combine

    for i in range(5):
        print(i, end=" | ")

**Resultat :**

    0 | 1 | 2 | 3 | 4 |

---

## 6. Les caracteres speciaux

| Code | Signification | Exemple |
| :--- | :--- | :--- |
| \\n | Retour a la ligne | print("A\\nB") |
| \\t | Tabulation | print("A\\tB") |
| \\\\ | Backslash | print("C:\\\\Users") |
| \\" | Guillemet double | print("Il dit \\"oui\\"") |

---

## 7. L'operateur de repetition

    print("=" * 30)
    print("Bonjour" * 3)

**Resultat :**

    ==============================
    BonjourBonjourBonjour

### Exemple : Menu

    print("=" * 40)
    print("       MENU PRINCIPAL")
    print("=" * 40)
    print("1. Nouvelle partie")
    print("2. Charger une partie")
    print("3. Quitter")
    print("=" * 40)

---

## 8. Points cles a retenir

- print() affiche du texte ou des valeurs
- Le texte doit etre entre guillemets, les nombres non
- f-string : f"Bonjour {nom}"
- sep change le separateur, end change la fin
- \\n = retour a la ligne, \\t = tabulation

---

## Prochaine etape

Apprenons a demander des informations a l'utilisateur.

=> **Lecon suivante : Saisir avec input()**
"""

lecon_2_1_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 1, ?, ?, 30)
""", (chap2, "Afficher avec print()", lecon_2_1)).lastrowid

print("  [OK] Lecon 2.1 creee.")

# =========================================================
# LECON 2.2 : SAISIR AVEC INPUT()
# =========================================================

lecon_2_2 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Demander** une information a l'utilisateur avec input()
- **Stocker** la reponse dans une variable
- **Convertir** la saisie avec int(), float() ou str()
- **Creer** des programmes interactifs

---

## 1. La fonction input()

### Definition

> input() est une **fonction integree** qui **affiche un message**, **attend** que l'utilisateur tape du texte, puis **retourne** ce texte sous forme de **chaine de caracteres** (str).

### Syntaxe

    variable = input("Message a afficher : ")

### Premier exemple

    nom = input("Quel est votre nom ? ")
    print(f"Bonjour {nom} !")

**Execution :**

    Quel est votre nom ? Ahmed
    Bonjour Ahmed !

---

## 2. Toujours mettre un message clair

    prenom = input("Votre prenom : ")
    age = input("Votre age : ")
    ville = input("Votre ville : ")

    print(f"{prenom}, {age} ans, habite a {ville}.")

**Execution :**

    Votre prenom : Sara
    Votre age : 22
    Votre ville : Alger
    Sara, 22 ans, habite a Alger.

---

## 3. input() retourne TOUJOURS une chaine

**Point crucial** : input() retourne **toujours** une chaine (str).

### Demonstration

    age = input("Votre age : ")
    print(type(age))

**Execution :**

    Votre age : 25
    <class 'str'>

### Consequence : les calculs echouent

    age = input("Votre age : ")
    double = age * 2
    print(double)

**Execution (si l'utilisateur tape 25) :**

    Votre age : 25
    2525

> Le resultat est "2525" (chaine repetee), pas 50 !

---

## 4. Convertir la saisie

| Fonction | Role | Exemple |
| :--- | :--- | :--- |
| int() | Convertit en entier | int("25") -> 25 |
| float() | Convertit en decimal | float("3.14") -> 3.14 |
| str() | Convertit en chaine | str(25) -> "25" |

### Exemple avec int()

    age = int(input("Votre age : "))
    double = age * 2
    print(f"Le double de votre age est {double}")

**Execution :**

    Votre age : 25
    Le double de votre age est 50

### Exemple avec float()

    prix = float(input("Prix du produit : "))
    quantite = int(input("Quantite : "))
    total = prix * quantite

    print(f"Total a payer : {total} DA")

**Execution :**

    Prix du produit : 15.5
    Quantite : 3
    Total a payer : 46.5 DA

### Quelle conversion choisir ?

| Donnee | Type conseille |
| :--- | :--- |
| Age, quantite, annee | int() |
| Prix, distance, pourcentage | float() |
| Nom, ville, message | (pas de conversion) |

---

## 5. Exemple complet : Formulaire

    print("=== INSCRIPTION ===")
    print()

    nom = input("Nom : ")
    prenom = input("Prenom : ")
    age = int(input("Age : "))
    email = input("Email : ")

    print()
    print("=" * 40)
    print("   RECAPITULATIF")
    print("=" * 40)
    print(f"Nom complet : {prenom} {nom}")
    print(f"Age         : {age} ans")
    print(f"Email       : {email}")
    print("=" * 40)

---

## 6. Exemple complet : Calculatrice

    print("=== CALCULATRICE ===")

    a = float(input("Premier nombre : "))
    b = float(input("Deuxieme nombre : "))

    print()
    print(f"Somme      : {a + b}")
    print(f"Difference : {a - b}")
    print(f"Produit    : {a * b}")
    print(f"Quotient   : {a / b:.2f}")

---

## 7. Points cles a retenir

- input() demande une information a l'utilisateur
- Elle retourne **toujours** une chaine (str)
- Pour les calculs, **convertissez** avec int() ou float()
- Mettez toujours un **message clair**

---

## Prochaine etape

Vous savez **afficher** et **demander**. Stockons dans des **variables**.

=> **Lecon suivante : Les variables**
"""

lecon_2_2_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 2, ?, ?, 30)
""", (chap2, "Saisir avec input()", lecon_2_2)).lastrowid

print("  [OK] Lecon 2.2 creee.")

# =========================================================
# LECON 2.3 : LES VARIABLES
# =========================================================

lecon_2_3 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Definir** ce qu'est une variable
- **Creer** et **assigner** des variables
- **Identifier** les types de donnees fondamentaux
- **Respecter** les regles de nommage (PEP 8)
- **Manipuler** des variables

---

## 1. Qu'est-ce qu'une variable ?

### Definition

> Une **variable** est un **espace memoire nomme** qui contient une **valeur**. On la voit comme une **boite etiquetee**.

### Analogie

- L'**etiquette** = le nom de la variable
- Le **contenu** = la valeur stockee

### Exemple concret

    nom = "Ahmed"
    age = 25
    taille = 1.75

Ici :

- nom contient "Ahmed"
- age contient 25
- taille contient 1.75

---

## 2. Creer et assigner une variable

En Python, on utilise **=** (operateur d'assignation).

### Syntaxe

    nom_variable = valeur

> **Attention** : = signifie "recoit", pas "egal a".

### Exemples

    prenom = "Sara"           # Chaine
    age = 22                  # Entier
    moyenne = 15.75           # Decimal
    est_etudiant = True       # Booleen

---

## 3. Les types de donnees fondamentaux

| Type | Nom Python | Exemple | Usage |
| :--- | :--- | :--- | :--- |
| **Chaine** | str | "Bonjour" | Texte |
| **Entier** | int | 42 | Nombres sans virgule |
| **Decimal** | float | 3.14 | Nombres a virgule |
| **Booleen** | bool | True / False | Vrai ou Faux |
| **Aucun** | NoneType | None | Valeur absente |

### Verifier le type avec type()

    nom = "Ahmed"
    age = 25
    taille = 1.75
    actif = True

    print(type(nom))      # <class 'str'>
    print(type(age))      # <class 'int'>
    print(type(taille))   # <class 'float'>
    print(type(actif))    # <class 'bool'>

---

## 4. Regles de nommage

### Regles obligatoires

- Doit commencer par une **lettre** ou un **underscore** _
- Peut contenir des **lettres, chiffres et underscores**
- **Ne peut pas** commencer par un chiffre
- **Ne peut pas** etre un **mot reserve** de Python

### Noms invalides

    2nom = "Ahmed"       # Commence par un chiffre
    mon-nom = "Sara"     # Contient un tiret
    class = "Test"       # Mot reserve

### Noms valides

    nom = "Ahmed"
    nom_etudiant = "Sara"
    _age = 25
    prix_total = 120.5

### Convention Python (PEP 8) : snake_case

    # Bon
    prix_unitaire = 15.5
    nom_complet_etudiant = "Ahmed Benali"

    # Mauvais
    prixUnitaire = 15.5
    NomCompletEtudiant = "Ahmed Benali"

---

## 5. Manipuler des variables

### Modifier la valeur

    age = 20
    print(age)   # 20

    age = 21
    print(age)   # 21

### Utiliser une variable dans une autre

    prix = 100
    quantite = 3
    total = prix * quantite

    print(total)   # 300

### Combiner avec print() et input()

    nom = input("Votre nom : ")
    age = int(input("Votre age : "))

    print(f"{nom}, vous avez {age} ans.")

---

## 6. Afficher une variable : f-string

    nom = "Ahmed"
    age = 25

    print(f"Nom : {nom}, Age : {age}")
    # Nom : Ahmed, Age : 25

---

## 7. Points cles a retenir

- Une **variable** est un espace memoire nomme qui contient une valeur
- On utilise **=** pour assigner
- Les types principaux : **str, int, float, bool, None**
- Nommez en **snake_case**
- Utilisez **type()** pour verifier le type
- **f-string** est la methode moderne pour afficher

---

## Prochaine etape

Apprenons a faire prendre des **decisions** a votre programme.

=> **Lecon suivante : Les conditions**
"""

lecon_2_3_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 3, ?, ?, 30)
""", (chap2, "Les variables", lecon_2_3)).lastrowid

print("  [OK] Lecon 2.3 creee.")

# =========================================================
# LECON 2.4 : LES CONDITIONS
# =========================================================

lecon_2_4 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Comprendre** le role des conditions
- **Utiliser** if, elif et else
- **Combiner** des conditions avec and, or, not
- **Ecrire** des programmes qui prennent des decisions

---

## 1. Pourquoi des conditions ?

Un programme doit **prendre des decisions** :

- Si l'utilisateur a plus de 18 ans -> "Majeur"
- Sinon -> "Mineur"

---

## 2. La structure if

    age = 20

    if age >= 18:
        print("Vous etes majeur")

### Decomposition

| Element | Role |
| :--- | :--- |
| if | Mot-cle de condition |
| age >= 18 | La condition |
| : | Deux-points obligatoires |
| Indentation | 4 espaces obligatoires |

> **L'indentation est CRUCIALE en Python**.

---

## 3. La structure if / else

    age = 15

    if age >= 18:
        print("Vous etes majeur")
    else:
        print("Vous etes mineur")

**Resultat :** Vous etes mineur

---

## 4. La structure if / elif / else

    note = 15

    if note >= 16:
        print("Tres bien")
    elif note >= 14:
        print("Bien")
    elif note >= 12:
        print("Assez bien")
    elif note >= 10:
        print("Passable")
    else:
        print("Insuffisant")

**Resultat :** Bien

> Python teste les conditions **dans l'ordre**.

---

## 5. Les operateurs de comparaison

| Operateur | Signification | Exemple |
| :--- | :--- | :--- |
| == | Egal a | 5 == 5 -> True |
| != | Different de | 5 != 3 -> True |
| > | Superieur | 7 > 3 -> True |
| < | Inferieur | 2 < 5 -> True |
| >= | Superieur ou egal | 5 >= 5 -> True |
| <= | Inferieur ou egal | 3 <= 5 -> True |

> **=** (assignation) different de **==** (comparaison)

---

## 6. Les operateurs logiques

| Operateur | Signification | Exemple |
| :--- | :--- | :--- |
| and | ET logique | age >= 18 and permis |
| or | OU logique | jour == "sam" or jour == "dim" |
| not | Negation | not est_majeur |

### Exemple avec and

    age = 25
    permis = True

    if age >= 18 and permis:
        print("Vous pouvez conduire")

### Exemple avec or

    jour = "samedi"

    if jour == "samedi" or jour == "dimanche":
        print("C'est le week-end !")

---

## 7. Conditions imbriquees

    age = 25
    permis = True

    if age >= 18:
        if permis:
            print("Vous pouvez conduire")
        else:
            print("Majeur mais sans permis")
    else:
        print("Trop jeune")

> **Conseil** : Evitez trop d'imbrications.

---

## 8. Exemple complet : Categorie d'age

    age = int(input("Quel est votre age ? "))

    if age < 0:
        print("Age invalide")
    elif age < 13:
        print("Vous etes un enfant")
    elif age < 18:
        print("Vous etes un adolescent")
    elif age < 65:
        print("Vous etes un adulte")
    else:
        print("Vous etes un senior")

---

## 9. Points cles a retenir

- **if** execute un bloc si la condition est vraie
- **else** execute un bloc si la condition est fausse
- **elif** teste plusieurs conditions
- L'**indentation** (4 espaces) est obligatoire
- **==** compare, **=** assigne
- **and, or, not** combinent les conditions

---

## Prochaine etape

Votre programme peut prendre des **decisions**. Apprenons a **repeter des actions**.

=> **Lecon suivante : Les boucles**
"""

lecon_2_4_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 4, ?, ?, 35)
""", (chap2, "Les conditions", lecon_2_4)).lastrowid

print("  [OK] Lecon 2.4 creee.")

# =========================================================
# LECON 2.5 : LES BOUCLES
# =========================================================

lecon_2_5 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Comprendre** le role des boucles
- **Utiliser** for pour parcourir des sequences
- **Utiliser** while pour repeter tant qu'une condition est vraie
- **Controler** une boucle avec break et continue

---

## 1. Pourquoi des boucles ?

Sans boucle, afficher les nombres de 1 a 100 demande 100 lignes. Avec une boucle : **2 lignes**.

    for i in range(1, 101):
        print(i)

---

## 2. La boucle for

### Syntaxe

    for variable in sequence:
        # instructions a repeter

### Exemple 1 : range()

    for i in range(5):
        print(i)

**Resultat :** 0 1 2 3 4

> **range(5)** genere les nombres **de 0 a 4**.

### Exemple 2 : range avec debut

    for i in range(1, 6):
        print(i)

**Resultat :** 1 2 3 4 5

### Exemple 3 : range avec pas

    for i in range(0, 10, 2):
        print(i)

**Resultat :** 0 2 4 6 8

### Exemple 4 : parcourir une liste

    fruits = ["pomme", "banane", "cerise"]

    for fruit in fruits:
        print(fruit)

### Exemple 5 : parcourir une chaine

    mot = "Python"

    for lettre in mot:
        print(lettre)

**Resultat :** P y t h o n

---

## 3. La boucle while

### Syntaxe

    while condition:
        # instructions

### Exemple 1 : Compter jusqu'a 5

    compteur = 1

    while compteur <= 5:
        print(compteur)
        compteur += 1

**Resultat :** 1 2 3 4 5

> Si vous oubliez compteur += 1, la boucle sera **infinie** !

### Exemple 2 : Saisie utilisateur

    mot_de_passe = ""

    while mot_de_passe != "secret":
        mot_de_passe = input("Entrez le mot de passe : ")

    print("Acces autorise !")

---

## 4. for ou while : lequel choisir ?

| Situation | Boucle |
| :--- | :--- |
| Parcourir une liste, chaine ou intervalle | **for** |
| Repeter jusqu'a une condition precise | **while** |
| Nombre d'iterations connu | **for** |
| Nombre d'iterations inconnu | **while** |

---

## 5. Controler une boucle

### break : sortir immediatement

    for i in range(10):
        if i == 5:
            break
        print(i)

**Resultat :** 0 1 2 3 4

### continue : sauter une iteration

    for i in range(5):
        if i == 2:
            continue
        print(i)

**Resultat :** 0 1 3 4

---

## 6. Boucles imbriquees

    for i in range(1, 4):
        for j in range(1, 4):
            print(f"{i} x {j} = {i * j}")
        print("---")

**Resultat :**

    1 x 1 = 1
    1 x 2 = 2
    1 x 3 = 3
    ---
    2 x 1 = 2
    2 x 2 = 4
    2 x 3 = 6
    ---
    3 x 1 = 3
    3 x 2 = 6
    3 x 3 = 9
    ---

---

## 7. Exemple complet : Table de multiplication

    nombre = int(input("Quelle table voulez-vous ? "))

    for i in range(1, 11):
        resultat = nombre * i
        print(f"{nombre} x {i} = {resultat}")

---

## 8. Points cles a retenir

- **for** parcourt une sequence (liste, chaine, range)
- **while** repete tant qu'une condition est vraie
- **range(a, b)** genere les nombres de a a b-1
- **break** sort de la boucle, **continue** saute une iteration
- Attention aux **boucles infinies** avec while

---

## Prochaine etape

Apprenons a **organiser votre code** avec les fonctions.

=> **Lecon suivante : Les fonctions**
"""

lecon_2_5_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 5, ?, ?, 35)
""", (chap2, "Les boucles", lecon_2_5)).lastrowid

print("  [OK] Lecon 2.5 creee.")

# =========================================================
# LECON 2.6 : LES FONCTIONS
# =========================================================

lecon_2_6 = """## Objectifs de cette lecon

A la fin de cette lecon, vous serez capable de :

- **Comprendre** l'utilite des fonctions
- **Definir** une fonction avec def
- **Appeler** une fonction
- **Passer** des parametres et **retourner** des valeurs
- **Organiser** votre code en blocs reutilisables

---

## 1. Pourquoi des fonctions ?

Sans fonction :

    moyenne_ahmed = (15 + 12 + 18) / 3
    moyenne_sara = (14 + 16 + 13) / 3
    moyenne_karim = (11 + 9 + 15) / 3

Avec une fonction :

    def calculer_moyenne(n1, n2, n3):
        return (n1 + n2 + n3) / 3

    moyenne_ahmed = calculer_moyenne(15, 12, 18)
    moyenne_sara = calculer_moyenne(14, 16, 13)
    moyenne_karim = calculer_moyenne(11, 9, 15)

**Avantages :**

- Code **reutilisable**
- Code **plus lisible**
- **Une seule modification** si la formule change

---

## 2. Definir une fonction

### Syntaxe

    def nom_fonction(parametres):
        # corps de la fonction
        return valeur

### Decomposition

| Element | Role |
| :--- | :--- |
| def | Mot-cle de definition |
| nom_fonction | Nom en snake_case |
| (parametres) | Valeurs d'entree (optionnel) |
| : | Fin de la declaration |
| Indentation | Corps de la fonction |
| return | Valeur renvoyee (optionnel) |

---

## 3. Premier exemple

    def dire_bonjour():
        print("Bonjour Soft Learn !")

    dire_bonjour()

**Resultat :** Bonjour Soft Learn !

> Definir une fonction ne l'execute pas. Il faut l'**appeler**.

---

## 4. Fonction avec parametres

    def dire_bonjour(prenom):
        print(f"Bonjour {prenom} !")

    dire_bonjour("Ahmed")
    dire_bonjour("Sara")
    dire_bonjour("Karim")

**Resultat :**

    Bonjour Ahmed !
    Bonjour Sara !
    Bonjour Karim !

### Plusieurs parametres

    def presenter(nom, age, ville):
        print(f"{nom}, {age} ans, habite a {ville}.")

    presenter("Ahmed", 25, "Alger")

---

## 5. Fonction avec return

    def addition(a, b):
        return a + b

    resultat = addition(5, 3)
    print(resultat)   # 8

### print vs return

| print() | return |
| :--- | :--- |
| Affiche a l'ecran | **Renvoie** une valeur |
| Ne peut pas etre reutilisee | Peut etre stockee |
| Effet visuel | Effet fonctionnel |

    # Mauvais
    def addition(a, b):
        print(a + b)

    x = addition(2, 3)   # Affiche 5, mais x vaut None

    # Bon
    def addition(a, b):
        return a + b

    x = addition(2, 3)   # x vaut 5

---

## 6. Valeurs par defaut

    def saluer(nom, message="Bonjour"):
        print(f"{message}, {nom} !")

    saluer("Ahmed")                    # Bonjour, Ahmed !
    saluer("Sara", "Salut")            # Salut, Sara !

---

## 7. Portee des variables

Les variables definies **dans** une fonction sont **locales** :

    def ma_fonction():
        x = 10      # Variable locale
        print(x)

    ma_fonction()   # 10
    print(x)        # ERREUR : x n'existe pas dehors

---

## 8. Exemple complet : Calcul IMC

    def calculer_imc(poids, taille):
        if taille <= 0:
            return None
        return poids / (taille ** 2)

    def interpreter_imc(imc):
        if imc < 18.5:
            return "Insuffisance ponderale"
        elif imc < 25:
            return "Corpulence normale"
        elif imc < 30:
            return "Surpoids"
        else:
            return "Obesite"

    poids = 70
    taille = 1.75

    imc = calculer_imc(poids, taille)
    print(f"IMC : {imc:.2f}")
    print(f"Interpretation : {interpreter_imc(imc)}")

**Resultat :**

    IMC : 22.86
    Interpretation : Corpulence normale

---

## 9. Bonnes pratiques

- Nommez avec des **verbes** : calculer_, afficher_, verifier_
- Une fonction = **une seule responsabilite**
- Utilisez **return** (pas print) pour renvoyer des valeurs
- Ajoutez une **docstring** (\"""...\""")
- Evitez les fonctions > 30 lignes

---

## 10. Points cles a retenir

- Une **fonction** est un bloc de code reutilisable
- On la definit avec **def**
- On l'**appelle** avec nom_fonction()
- **return** renvoie une valeur, **print** affiche
- Les variables internes sont **locales**
- Les **parametres** peuvent avoir des **valeurs par defaut**

---

## Prochaine etape

Vous maitrisez maintenant les **fondamentaux** de Python.

Il est temps de mettre tout cela en pratique avec les **exercices** et l'**evaluation finale**.

=> **Rendez-vous dans la section Exercices de ce niveau.**
"""

lecon_2_6_id = conn.execute("""
    INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
    VALUES (?, 6, ?, ?, 40)
""", (chap2, "Les fonctions", lecon_2_6)).lastrowid

print("  [OK] Lecon 2.6 creee.")

# =========================================================
# FINALISATION
# =========================================================

conn.commit()
conn.close()

print()
print("=" * 60)
print("[OK] MISE A JOUR PYTHON N1 TERMINEE")
print("=" * 60)
print("2 chapitres - 6 lecons enrichies")
print("=" * 60)
print()
print("Pour tester :")
print("   python app.py")
print("   Puis connectez-vous comme etudiant")
print("=" * 60)