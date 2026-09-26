# =========================================================
# SOFT LEARN — APPLICATION FLASK
# =========================================================

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_from_directory, make_response
)
import json
import uuid
import markdown
import io
from markupsafe import Markup
from pathlib import Path
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas

import config
from db_adapter import get_db

BASE_DIR = config.BASE_DIR
DB_PATH = config.SQLITE_PATH

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

CERTIFICATES_FOLDER = config.CERTIFICATES_FOLDER

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# =========================================================
# HELPERS REDIRECTION
# =========================================================

def redirect_to_section(section):
    """Redirige vers le dashboard en ouvrant une section specifique (via query param)."""
    return redirect(url_for("dashboard", section=section))


# =========================================================
# FILTRES JINJA
# =========================================================

@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ""
    html = markdown.markdown(
        text,
        extensions=['extra', 'fenced_code', 'tables',
                    'nl2br', 'sane_lists', 'codehilite']
    )
    return Markup(html)


@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s) if s else []
    except (ValueError, TypeError):
        return []


# =========================================================
# HELPERS
# =========================================================




def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, prefix):
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{prefix}_{uuid.uuid4().hex[:10]}.{ext}"
    file.save(str(UPLOAD_FOLDER / unique_name))
    return unique_name


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("index"))
            if session.get("role") not in roles:
                flash("Accès non autorisé.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# =========================================================
# LOGIQUE METIER
# =========================================================

def compute_formation_progression(conn, user_id, formation_id):
    niveaux = conn.execute("""
        SELECT * FROM niveaux WHERE formation_id = ? ORDER BY numero
    """, (formation_id,)).fetchall()

    if not niveaux:
        return {"pourcentage": 0, "niveaux_completes": [], "niveau_actuel_id": None}

    total_niveaux = len(niveaux)
    niveaux_completes = []
    niveau_actuel_id = None

    for n in niveaux:
        insc = conn.execute("""
            SELECT * FROM inscriptions
            WHERE user_id = ? AND niveau_id = ?
            AND statut IN ('active', 'completed')
        """, (user_id, n["id"])).fetchone()

        if insc and insc["statut"] == "completed":
            niveaux_completes.append(n["numero"])
        elif insc and insc["statut"] == "active":
            niveau_actuel_id = n["id"]

    pourcentage = int((len(niveaux_completes) / total_niveaux) * 100)

    conn.execute("""
        INSERT INTO progressions_etudiant
        (user_id, formation_id, niveau_actuel_id, niveaux_completes,
         pourcentage_global, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, formation_id) DO UPDATE SET
            niveau_actuel_id = excluded.niveau_actuel_id,
            niveaux_completes = excluded.niveaux_completes,
            pourcentage_global = excluded.pourcentage_global,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, formation_id, niveau_actuel_id,
          json.dumps(niveaux_completes), pourcentage))

    return {
        "pourcentage": pourcentage,
        "niveaux_completes": niveaux_completes,
        "niveau_actuel_id": niveau_actuel_id
    }


def check_niveau_access(conn, user_id, niveau_id):
    niveau = conn.execute("""
        SELECT n.*, f.id AS formation_id
        FROM niveaux n JOIN formations f ON f.id = n.formation_id
        WHERE n.id = ?
    """, (niveau_id,)).fetchone()

    if not niveau:
        return False, "Niveau introuvable."

    deja = conn.execute("""
        SELECT id FROM inscriptions
        WHERE user_id = ? AND niveau_id = ?
    """, (user_id, niveau_id)).fetchone()
    if deja:
        return False, "Vous êtes déjà inscrit à ce niveau."

    actif = conn.execute("""
        SELECT n.numero FROM inscriptions i
        JOIN niveaux n ON n.id = i.niveau_id
        WHERE i.user_id = ? AND i.formation_id = ?
        AND i.statut = 'active'
    """, (user_id, niveau["formation_id"])).fetchone()

    if niveau["numero"] == 1:
        if actif:
            return False, f"Vous devez d'abord terminer le niveau {actif['numero']}."
        return True, "OK"

    niveau_prec = conn.execute("""
        SELECT * FROM niveaux
        WHERE formation_id = ? AND numero = ?
    """, (niveau["formation_id"], niveau["numero"] - 1)).fetchone()

    if not niveau_prec:
        return False, "Niveau précédent introuvable."

    insc_prec = conn.execute("""
        SELECT * FROM inscriptions
        WHERE user_id = ? AND niveau_id = ?
    """, (user_id, niveau_prec["id"])).fetchone()

    if insc_prec and insc_prec["statut"] == "completed":
        if actif:
            return False, f"Vous devez d'abord terminer le niveau {actif['numero']}."
        return True, "Niveau précédent complété ✅"

    pretest_reussi = conn.execute("""
        SELECT * FROM soumissions_pretest
        WHERE user_id = ? AND niveau_id = ? AND reussi = 1
        ORDER BY date_passage DESC LIMIT 1
    """, (user_id, niveau_id)).fetchone()

    if pretest_reussi:
        if actif:
            return False, f"Vous devez d'abord terminer le niveau {actif['numero']}."
        return True, "Pré-test réussi ✅"

    pretest = conn.execute("""
        SELECT * FROM pretests WHERE niveau_id = ?
    """, (niveau_id,)).fetchone()

    if pretest:
        return False, "Vous devez passer le pré-test ou terminer le niveau précédent."

    return False, f"Vous devez d'abord terminer le niveau {niveau['numero'] - 1}."


def ia_pre_correction(exercice, contenu_etudiant):
    if not contenu_etudiant:
        return 0, "Aucune réponse fournie."

    longueur = len(contenu_etudiant)
    if longueur < 20:
        return 8, "Réponse trop courte. Développez votre raisonnement."
    elif longueur < 100:
        return 14, "Bonne réponse, quelques détails pourraient être ajoutés."
    else:
        return 17, "Très bonne réponse, bien structurée et complète."


# =========================================================
# INDEX
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# INSCRIPTION
# =========================================================

@app.post("/register")
def register():
    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    role = request.form.get("role", "student")

    if role not in ("student", "trainer"):
        flash("Le rôle choisi est invalide.", "danger")
        return redirect(url_for("index"))

    if not all([nom, prenom, email, password]):
        flash("Veuillez remplir tous les champs obligatoires.", "danger")
        return redirect(url_for("index"))

    if password != confirm:
        flash("Les deux mots de passe ne correspondent pas.", "danger")
        return redirect(url_for("index"))

    if len(password) < 6:
        flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
        return redirect(url_for("index"))

    diplome = None
    cv_file = None
    diplome_file = None
    experience = None
    statut_validation = "approved"

    if role == "trainer":
        diplome = request.form.get("diplome", "").strip()
        experience = request.form.get("experience", "").strip()

        cv_obj = request.files.get("cv")
        diplome_obj = request.files.get("diplome_file")

        if not diplome:
            flash("Veuillez indiquer votre diplôme.", "danger")
            return redirect(url_for("index"))
        if not experience or len(experience) < 30:
            flash("Veuillez décrire votre expérience (30 caractères minimum).", "danger")
            return redirect(url_for("index"))
        if not cv_obj or cv_obj.filename == "":
            flash("Veuillez téléverser votre CV.", "danger")
            return redirect(url_for("index"))
        if not diplome_obj or diplome_obj.filename == "":
            flash("Veuillez téléverser votre diplôme.", "danger")
            return redirect(url_for("index"))

        cv_file = save_upload(cv_obj, "cv")
        diplome_file = save_upload(diplome_obj, "diplome")

        if not cv_file or not diplome_file:
            flash("Format de fichier non autorisé (PDF, DOC, DOCX, JPG, PNG).", "danger")
            return redirect(url_for("index"))

        statut_validation = "pending"

    conn = get_db()
    try:
        if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash("Cette adresse e-mail existe déjà.", "danger")
            return redirect(url_for("index"))

        conn.execute("""
            INSERT INTO users(
                nom, prenom, telephone, email, password, role,
                statut_validation, diplome, cv, diplome_file, experience
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, prenom, telephone, email,
              generate_password_hash(password), role,
              statut_validation, diplome, cv_file, diplome_file, experience))
        conn.commit()

        if role == "trainer":
            flash("Inscription réussie. Votre dossier est en cours de vérification.",
                  "success")
        else:
            flash("Inscription réussie. Vous pouvez maintenant vous connecter.",
                  "success")
    finally:
        conn.close()

    return redirect(url_for("index"))


# =========================================================
# CONNEXION
# =========================================================

@app.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if not user or not check_password_hash(user["password"], password):
        flash("E-mail ou mot de passe incorrect.", "danger")
        return redirect(url_for("index"))

    statut = user["statut_validation"] or "approved"

    if user["role"] == "trainer" and statut == "pending":
        flash("Votre compte formateur est en attente de validation. "
              "Vous recevrez une réponse après vérification de votre dossier.",
              "warning")
        return redirect(url_for("index"))

    if user["role"] == "trainer" and statut == "rejected":
        motif = user["motif_refus"] or "non précisé"
        flash(f"Votre compte formateur a été refusé. Motif : {motif}", "danger")
        return redirect(url_for("index"))

    session.clear()
    session["user_id"] = user["id"]
    session["nom"] = user["nom"]
    session["prenom"] = user["prenom"]
    session["email"] = user["email"]
    session["telephone"] = user["telephone"]
    session["role"] = user["role"]
    return redirect(url_for("dashboard"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    user_id = session["user_id"]

    current_section = request.args.get("section", "").strip()
    if not current_section:
        current_section = "accueil"

    conn = get_db()

    try:
        # ==================== ETUDIANT ====================
        if role == "student":
            formations = conn.execute("""
                SELECT i.id AS inscription_id,
                       f.nom AS formation_nom, f.id AS formation_id,
                       n.id AS niveau_id, n.numero, n.titre, n.prix,
                       i.progression, i.statut
                FROM inscriptions i
                JOIN niveaux n ON n.id = i.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE i.user_id = ?
                ORDER BY f.nom, n.numero
            """, (user_id,)).fetchall()

            catalogue = conn.execute("""
                SELECT f.id, f.nom, f.description, f.categorie,
                       f.plateforme_defaut,
                       COUNT(n.id) AS nb_niveaux
                FROM formations f
                LEFT JOIN niveaux n ON n.formation_id = f.id
                GROUP BY f.id
                ORDER BY f.nom
            """).fetchall()

            niveaux_data = []
            tous_niveaux = conn.execute("""
                SELECT n.*, f.nom AS formation_nom, f.id AS formation_id,
                       f.plateforme_defaut
                FROM niveaux n JOIN formations f ON f.id = n.formation_id
                ORDER BY f.nom, n.numero
            """).fetchall()

            for n in tous_niveaux:
                insc = conn.execute("""
                    SELECT id, statut FROM inscriptions
                    WHERE user_id = ? AND niveau_id = ?
                """, (user_id, n["id"])).fetchone()

                pending = conn.execute("""
                    SELECT id FROM paiements
                    WHERE user_id = ? AND niveau_id = ? AND statut = 'pending'
                """, (user_id, n["id"])).fetchone()

                pretest = conn.execute("""
                    SELECT * FROM pretests WHERE niveau_id = ?
                """, (n["id"],)).fetchone()

                pretest_reussi = conn.execute("""
                    SELECT id FROM soumissions_pretest
                    WHERE user_id = ? AND niveau_id = ? AND reussi = 1
                """, (user_id, n["id"])).fetchone()

                peut, raison = check_niveau_access(conn, user_id, n["id"])

                niveaux_data.append({
                    "niveau": n,
                    "inscription": insc,
                    "paiement_en_attente": pending,
                    "pretest": pretest,
                    "pretest_reussi": pretest_reussi,
                    "peut_acheter": peut,
                    "raison": raison
                })

            paiements = conn.execute("""
                SELECT p.*, f.nom AS formation_nom, n.numero, n.titre
                FROM paiements p
                JOIN niveaux n ON n.id = p.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE p.user_id = ?
                ORDER BY p.date_paiement DESC
            """, (user_id,)).fetchall()

            return render_template(
                "dashboard.html",
                role=role,
                formations=formations,
                catalogue=catalogue,
                niveaux_data=niveaux_data,
                paiements=paiements,
                current_section=current_section
            )

        # ==================== FORMATEUR ====================
        elif role == "trainer":
            my_formations = conn.execute("""
                SELECT f.*, COUNT(DISTINCT n.id) AS nb_niveaux
                FROM formations f
                LEFT JOIN niveaux n ON n.formation_id = f.id
                WHERE f.trainer_id = ?
                GROUP BY f.id
                ORDER BY f.created_at DESC
            """, (user_id,)).fetchall()

            submissions = conn.execute("""
                SELECT s.*, e.titre AS exercice_titre, e.type,
                       e.est_evaluation_finale,
                       u.prenom, u.nom
                FROM soumissions s
                JOIN exercices e ON e.id = s.exercice_id
                JOIN niveaux n ON n.id = e.niveau_id
                JOIN formations f ON f.id = n.formation_id
                JOIN users u ON u.id = s.user_id
                WHERE f.trainer_id = ?
                ORDER BY s.date_soumission DESC
            """, (user_id,)).fetchall()

            students = conn.execute("""
                SELECT DISTINCT u.id, u.nom, u.prenom, u.email,
                       f.nom AS formation_nom, f.id AS formation_id,
                       i.progression, i.statut,
                       n.titre AS niveau_titre, n.numero AS niveau_numero
                FROM inscriptions i
                JOIN users u ON u.id = i.user_id
                JOIN niveaux n ON n.id = i.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE f.trainer_id = ?
                ORDER BY u.nom, u.prenom, n.numero
            """, (user_id,)).fetchall()

            certificats = conn.execute("""
                SELECT c.*, u.prenom, u.nom, f.nom AS formation_nom,
                       n.titre AS niveau_titre, n.numero AS niveau_numero
                FROM certificats c
                JOIN users u ON u.id = c.user_id
                JOIN formations f ON f.id = c.formation_id
                JOIN niveaux n ON n.id = c.niveau_id
                WHERE f.trainer_id = ?
                ORDER BY c.date_obtention DESC
            """, (user_id,)).fetchall()

            formations_avec_cours = []
            for f in my_formations:
                niveaux_data_t = []
                niveaux = conn.execute("""
                    SELECT * FROM niveaux WHERE formation_id = ? ORDER BY numero
                """, (f["id"],)).fetchall()

                for n in niveaux:
                    chapitres = conn.execute("""
                        SELECT * FROM chapitres WHERE niveau_id = ? ORDER BY numero
                    """, (n["id"],)).fetchall()

                    chapitres_data = []
                    for c in chapitres:
                        lecons = conn.execute("""
                            SELECT * FROM lecons WHERE chapitre_id = ? ORDER BY numero
                        """, (c["id"],)).fetchall()
                        chapitres_data.append({"chapitre": c, "lecons": lecons})

                    exercices_n = conn.execute("""
                        SELECT * FROM exercices WHERE niveau_id = ? ORDER BY id
                    """, (n["id"],)).fetchall()

                    pretest_n = conn.execute("""
                        SELECT * FROM pretests WHERE niveau_id = ?
                    """, (n["id"],)).fetchone()

                    niveaux_data_t.append({
                        "niveau": n,
                        "chapitres": chapitres_data,
                        "exercices": exercices_n,
                        "pretest": pretest_n
                    })

                formations_avec_cours.append({
                    "formation": f,
                    "niveaux": niveaux_data_t
                })

            return render_template(
                "dashboard.html",
                role=role,
                my_formations=my_formations,
                submissions=submissions,
                students=students,
                formations_avec_cours=formations_avec_cours,
                certificats=certificats,
                current_section=current_section
            )

        # ==================== ADMIN ====================
        else:
            users = conn.execute("""
                SELECT id, nom, prenom, email, telephone, role,
                       statut_validation, created_at
                FROM users ORDER BY role, nom, prenom
            """).fetchall()

            formations = conn.execute("""
                SELECT f.*, u.prenom AS trainer_prenom, u.nom AS trainer_nom
                FROM formations f
                LEFT JOIN users u ON u.id = f.trainer_id
                ORDER BY f.created_at DESC
            """).fetchall()

            pending_payments = conn.execute("""
                SELECT p.*, u.prenom, u.nom, u.email,
                       f.nom AS formation_nom, n.numero, n.titre
                FROM paiements p
                JOIN users u ON u.id = p.user_id
                JOIN niveaux n ON n.id = p.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE p.statut = 'pending'
                ORDER BY p.date_paiement DESC
            """).fetchall()

            paid_payments = conn.execute("""
                SELECT p.*, u.prenom, u.nom, u.email,
                       f.nom AS formation_nom, n.numero, n.titre
                FROM paiements p
                JOIN users u ON u.id = p.user_id
                JOIN niveaux n ON n.id = p.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE p.statut = 'paid'
                ORDER BY p.date_paiement DESC
            """).fetchall()

            rejected_payments = conn.execute("""
                SELECT p.*, u.prenom, u.nom, u.email,
                       f.nom AS formation_nom, n.numero, n.titre
                FROM paiements p
                JOIN users u ON u.id = p.user_id
                JOIN niveaux n ON n.id = p.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE p.statut = 'rejected'
                ORDER BY p.date_paiement DESC
            """).fetchall()

            total_revenue = conn.execute("""
                SELECT COALESCE(SUM(montant), 0) AS total
                FROM paiements WHERE statut = 'paid'
            """).fetchone()["total"]

            monthly_revenue = conn.execute("""
                SELECT COALESCE(SUM(montant), 0) AS total
                FROM paiements
                WHERE statut = 'paid'
                  AND strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now')
            """).fetchone()["total"]

            revenue_by_formation = conn.execute("""
                SELECT f.nom AS formation_nom,
                       COUNT(p.id) AS nb_paiements,
                       COALESCE(SUM(p.montant), 0) AS total
                FROM paiements p
                JOIN niveaux n ON n.id = p.niveau_id
                JOIN formations f ON f.id = n.formation_id
                WHERE p.statut = 'paid'
                GROUP BY f.id
                ORDER BY total DESC
            """).fetchall()

            stats_paiements = conn.execute("""
                SELECT
                    SUM(CASE WHEN statut='pending' THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN statut='paid' THEN 1 ELSE 0 END) AS paid,
                    SUM(CASE WHEN statut='rejected' THEN 1 ELSE 0 END) AS rejected
                FROM paiements
            """).fetchone()

            pending_trainers = conn.execute("""
                SELECT * FROM users
                WHERE role = 'trainer' AND statut_validation = 'pending'
                ORDER BY created_at DESC
            """).fetchall()

            all_trainers = conn.execute("""
                SELECT * FROM users WHERE role = 'trainer'
                ORDER BY statut_validation, created_at DESC
            """).fetchall()

            return render_template(
                "dashboard.html",
                role=role, users=users, formations=formations,
                pending_payments=pending_payments,
                paid_payments=paid_payments,
                rejected_payments=rejected_payments,
                total_revenue=total_revenue,
                monthly_revenue=monthly_revenue,
                revenue_by_formation=revenue_by_formation,
                stats_paiements=stats_paiements,
                pending_trainers=pending_trainers,
                all_trainers=all_trainers,
                current_section=current_section
            )
    finally:
        conn.close()


# =========================================================
# ACHETER UN NIVEAU
# =========================================================

@app.post("/buy-level/<int:niveau_id>")
@role_required("student")
def buy_level(niveau_id):
    conn = get_db()
    try:
        peut, raison = check_niveau_access(conn, session["user_id"], niveau_id)
        if not peut:
            flash(raison, "danger")
            return redirect_to_section("catalogue")

        niveau = conn.execute("SELECT * FROM niveaux WHERE id = ?",
                              (niveau_id,)).fetchone()
        if not niveau:
            flash("Niveau introuvable.", "danger")
            return redirect_to_section("catalogue")

        pending = conn.execute("""
            SELECT id FROM paiements
            WHERE user_id = ? AND niveau_id = ? AND statut = 'pending'
        """, (session["user_id"], niveau_id)).fetchone()
        if pending:
            flash("Une demande de paiement est déjà en attente.", "info")
            return redirect_to_section("catalogue")

        conn.execute("""
            INSERT INTO paiements(user_id, niveau_id, montant, statut, reference)
            VALUES (?, ?, ?, 'pending', ?)
        """, (session["user_id"], niveau_id, niveau["prix"],
              f"SL-{session['user_id']}-{niveau_id}"))
        conn.commit()
        flash("Demande de paiement envoyée. Elle sera activée après validation.",
              "success")
    finally:
        conn.close()
    return redirect_to_section("catalogue")


# =========================================================
# PRE-TEST
# =========================================================

@app.get("/pretest/<int:niveau_id>")
@role_required("student")
def view_pretest(niveau_id):
    conn = get_db()
    try:
        pretest = conn.execute("""
            SELECT p.*, n.titre AS niveau_titre, f.nom AS formation_nom
            FROM pretests p
            JOIN niveaux n ON n.id = p.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE p.niveau_id = ?
        """, (niveau_id,)).fetchone()

        if not pretest:
            flash("Aucun pré-test pour ce niveau.", "danger")
            return redirect_to_section("catalogue")

        passe = conn.execute("""
            SELECT * FROM soumissions_pretest
            WHERE user_id = ? AND niveau_id = ?
            ORDER BY date_passage DESC LIMIT 1
        """, (session["user_id"], niveau_id)).fetchone()

        return render_template("pretest.html",
                               pretest=pretest,
                               niveau_id=niveau_id,
                               passe=passe)
    finally:
        conn.close()


@app.post("/pretest/<int:niveau_id>/submit")
@role_required("student")
def submit_pretest(niveau_id):
    conn = get_db()
    try:
        pretest = conn.execute("""
            SELECT * FROM pretests WHERE niveau_id = ?
        """, (niveau_id,)).fetchone()

        if not pretest:
            flash("Pre-test introuvable.", "danger")
            return redirect_to_section("catalogue")

        deja_passe = conn.execute("""
            SELECT id FROM soumissions_pretest
            WHERE user_id = ? AND niveau_id = ?
        """, (session["user_id"], niveau_id)).fetchone()

        if deja_passe:
            flash("Vous avez deja passe ce pre-test.", "warning")
            return redirect_to_section("catalogue")

        qcm = json.loads(pretest["qcm_data"] or "[]")

        reponses_stockees = []
        bonnes = 0

        for i, q in enumerate(qcm):
            rep = request.form.get(f"q_{i}")
            reponses_stockees.append(rep)

            if rep is not None and int(rep) == q["bonne"]:
                bonnes += 1

        score = int((bonnes / len(qcm)) * 100) if qcm else 0
        reussi = 1 if score >= pretest["seuil_reussite"] else 0

        conn.execute("""
            INSERT INTO soumissions_pretest
            (pretest_id, user_id, niveau_id, reponses, score, reussi)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pretest["id"],
            session["user_id"],
            niveau_id,
            json.dumps(reponses_stockees),
            score,
            reussi
        ))
        conn.commit()

        if reussi:
            flash(
                f"Felicitations ! Pre-test reussi avec {score}%. "
                f"Vous pouvez maintenant acheter ce niveau.",
                "success"
            )
        else:
            flash(
                f"Pre-test echoue ({score}%). "
                f"Seuil requis : {pretest['seuil_reussite']}%. "
                f"Vous devez passer par le niveau precedent.",
                "danger"
            )

    finally:
        conn.close()

    return redirect_to_section("catalogue")


# =========================================================
# PAGE D'UN NIVEAU (ETUDIANT)
# =========================================================

@app.get("/level/<int:niveau_id>")
@role_required("student")
def level_detail(niveau_id):
    conn = get_db()
    try:
        niveau = conn.execute("""
            SELECT n.*, f.nom AS formation_nom, f.plateforme_defaut
            FROM niveaux n JOIN formations f ON f.id = n.formation_id
            WHERE n.id = ?
        """, (niveau_id,)).fetchone()

        if not niveau:
            flash("Niveau introuvable.", "danger")
            return redirect(url_for("dashboard"))

        acces = conn.execute("""
            SELECT * FROM inscriptions
            WHERE user_id = ? AND niveau_id = ?
            AND statut IN ('active', 'completed')
        """, (session["user_id"], niveau_id)).fetchone()

        if not acces:
            flash("Vous devez d'abord acheter ce niveau.", "danger")
            return redirect(url_for("dashboard"))

        chapitres = conn.execute("""
            SELECT * FROM chapitres WHERE niveau_id = ? ORDER BY numero
        """, (niveau_id,)).fetchall()

        chapitres_data = []
        total_lecons = 0
        lecons_terminees = 0

        for chap in chapitres:
            lecons = conn.execute("""
                SELECT l.*, COALESCE(pl.termine, 0) AS termine
                FROM lecons l
                LEFT JOIN progressions_lecons pl
                    ON pl.lecon_id = l.id AND pl.user_id = ?
                WHERE l.chapitre_id = ?
                ORDER BY l.numero
            """, (session["user_id"], chap["id"])).fetchall()

            total_lecons += len(lecons)
            lecons_terminees += sum(1 for l in lecons if l["termine"])
            chapitres_data.append({"chapitre": chap, "lecons": lecons})

        progression = int((lecons_terminees / total_lecons * 100)) \
            if total_lecons > 0 else 0

        exercices = conn.execute("""
            SELECT e.*,
                   (SELECT id FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_id,
                   (SELECT statut FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_statut,
                   (SELECT note FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS note,
                   (SELECT note_ia FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS note_ia,
                   (SELECT contenu FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_contenu,
                   (SELECT details FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_details,
                   (SELECT commentaire FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_commentaire,
                   (SELECT commentaire_ia FROM soumissions s
                    WHERE s.exercice_id = e.id AND s.user_id = ?
                    ORDER BY s.date_soumission DESC LIMIT 1) AS soumission_commentaire_ia
            FROM exercices e
            WHERE e.niveau_id = ?
            ORDER BY e.id
        """, (session["user_id"], session["user_id"],
              session["user_id"], session["user_id"],
              session["user_id"], session["user_id"],
              session["user_id"], session["user_id"],
              niveau_id)).fetchall()

        # =========================================================
        # CALCUL DES EXERCICES NORMAUX NON TERMINES
        # =========================================================
        exs_non_faits_ids = []
        for ex in exercices:
            if ex["est_evaluation_finale"]:
                continue

            a_soumission = ex["soumission_id"] is not None
            statut = ex["soumission_statut"]

            est_termine = a_soumission and statut in (
                'graded', 'ai_corrected', 'submitted'
            )

            if not est_termine:
                exs_non_faits_ids.append(ex["id"])

        statut_new = "completed" if progression >= 100 else "active"
        conn.execute("""
            UPDATE inscriptions SET progression = ?, statut = ?
            WHERE user_id = ? AND niveau_id = ?
        """, (progression, statut_new, session["user_id"], niveau_id))

        if statut_new == "completed":
            conn.execute("""
                UPDATE inscriptions SET date_completion = CURRENT_TIMESTAMP
                WHERE user_id = ? AND niveau_id = ? AND date_completion IS NULL
            """, (session["user_id"], niveau_id))

        conn.commit()

        compute_formation_progression(conn, session["user_id"],
                                      niveau["formation_id"])
        conn.commit()

        certificat = conn.execute("""
            SELECT * FROM certificats
            WHERE user_id = ? AND niveau_id = ?
        """, (session["user_id"], niveau_id)).fetchone()

        return render_template("level.html",
                               niveau=niveau,
                               chapitres=chapitres_data,
                               progression=progression,
                               total_lecons=total_lecons,
                               lecons_terminees=lecons_terminees,
                               exercices=exercices,
                               certificat=certificat,
                               exs_non_faits=exs_non_faits_ids)
    finally:
        conn.close()


# =========================================================
# REFAIRE L'EVALUATION FINALE
# =========================================================

@app.post("/level/<int:niveau_id>/retry-evaluation")
@role_required("student")
def retry_evaluation(niveau_id):
    conn = get_db()
    try:
        acces = conn.execute("""
            SELECT id FROM inscriptions
            WHERE user_id = ? AND niveau_id = ?
            AND statut IN ('active', 'completed')
        """, (session["user_id"], niveau_id)).fetchone()

        if not acces:
            flash("Acces non autorise.", "danger")
            return redirect(url_for("dashboard"))

        certificat = conn.execute("""
            SELECT id FROM certificats
            WHERE user_id = ? AND niveau_id = ?
        """, (session["user_id"], niveau_id)).fetchone()

        if certificat:
            flash(
                "Vous avez deja obtenu votre certification pour ce niveau.",
                "info"
            )
            return redirect(url_for("level_detail", niveau_id=niveau_id))

        conn.execute("""
            DELETE FROM soumissions
            WHERE user_id = ?
              AND exercice_id IN (
                  SELECT id FROM exercices
                  WHERE niveau_id = ? AND est_evaluation_finale = 1
              )
        """, (session["user_id"], niveau_id))
        conn.commit()

        flash(
            "Vous pouvez maintenant refaire l'evaluation finale. Bonne chance !",
            "success"
        )
    finally:
        conn.close()

    return redirect(url_for("level_detail", niveau_id=niveau_id))


# =========================================================
# VOIR UNE LECON
# =========================================================

@app.get("/lecon/<int:lecon_id>")
@role_required("student")
def view_lecon(lecon_id):
    conn = get_db()
    try:
        lecon = conn.execute("""
            SELECT l.*, c.titre AS chapitre_titre, c.niveau_id,
                   c.numero AS chapitre_numero
            FROM lecons l JOIN chapitres c ON c.id = l.chapitre_id
            WHERE l.id = ?
        """, (lecon_id,)).fetchone()

        if not lecon:
            flash("Leçon introuvable.", "danger")
            return redirect(url_for("dashboard"))

        acces = conn.execute("""
            SELECT id FROM inscriptions
            WHERE user_id = ? AND niveau_id = ?
            AND statut IN ('active', 'completed')
        """, (session["user_id"], lecon["niveau_id"])).fetchone()

        if not acces:
            flash("Accès non autorisé.", "danger")
            return redirect(url_for("dashboard"))

        conn.execute("""
            INSERT OR REPLACE INTO progressions_lecons
            (user_id, lecon_id, termine, date_termine)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        """, (session["user_id"], lecon_id))
        conn.commit()

        lecon_prec = conn.execute("""
            SELECT id FROM lecons WHERE chapitre_id = ? AND numero < ?
            ORDER BY numero DESC LIMIT 1
        """, (lecon["chapitre_id"], lecon["numero"])).fetchone()

        lecon_suiv = conn.execute("""
            SELECT id FROM lecons WHERE chapitre_id = ? AND numero > ?
            ORDER BY numero ASC LIMIT 1
        """, (lecon["chapitre_id"], lecon["numero"])).fetchone()

        return render_template("lecon.html",
                               lecon=lecon,
                               lecon_prec=lecon_prec,
                               lecon_suiv=lecon_suiv)
    finally:
        conn.close()


# =========================================================
# SOUMETTRE UN EXERCICE
# =========================================================

@app.post("/student/exercise/<int:exercice_id>/submit")
@role_required("student")
def submit_exercise(exercice_id):
    contenu = request.form.get("contenu", "").strip()

    conn = get_db()
    try:
        ex = conn.execute("""
            SELECT e.*, n.id AS niveau_id, f.id AS formation_id,
                   f.nom AS formation_nom
            FROM exercices e
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            JOIN inscriptions i ON i.niveau_id = e.niveau_id
            WHERE e.id = ? AND i.user_id = ?
            AND i.statut IN ('active','completed')
        """, (exercice_id, session["user_id"])).fetchone()

        if not ex:
            flash("Acces non autorise a cet exercice.", "danger")
            return redirect(url_for("dashboard"))

        niveau_id = ex["niveau_id"]

        # ========== QCM ==========
        if ex["type"] == "qcm":
            qcm_data = json.loads(ex["qcm_data"] or "[]")
            reponses = []
            bonnes = 0
            details = []

            for i, q in enumerate(qcm_data):
                rep = request.form.get(f"q_{i}")
                reponses.append(rep)

                est_correcte = rep is not None and int(rep) == q["bonne"]
                if est_correcte:
                    bonnes += 1

                details.append({
                    "question": q["question"],
                    "options": q["options"],
                    "votre_reponse": int(rep) if rep is not None else None,
                    "bonne_reponse": q["bonne"],
                    "correcte": est_correcte
                })

            note = round((bonnes / len(qcm_data)) * 20, 2) if qcm_data else 0

            conn.execute("""
                INSERT INTO soumissions(exercice_id, user_id, contenu,
                                        note, statut, details)
                VALUES (?, ?, ?, ?, 'graded', ?)
            """, (exercice_id, session["user_id"],
                  json.dumps(reponses), note, json.dumps(details)))
            conn.commit()

            if ex["est_evaluation_finale"]:
                flash(f"QCM final termine ! Score : {note}/20", "success")
            else:
                flash(f"QCM termine ! Note : {note}/20", "success")

            if ex["est_evaluation_finale"]:
                check_and_create_certificate(
                    conn, session["user_id"], niveau_id
                )

            return redirect(url_for("level_detail", niveau_id=niveau_id))

        # ========== CODE / TEXTE ==========
        if not contenu:
            flash("Veuillez saisir votre reponse.", "danger")
            return redirect(url_for("level_detail", niveau_id=niveau_id))

        conn.execute("""
            INSERT INTO soumissions(exercice_id, user_id, contenu, statut)
            VALUES (?, ?, ?, 'submitted')
        """, (exercice_id, session["user_id"], contenu))
        conn.commit()

        if ex["est_evaluation_finale"]:
            flash("Votre code a ete envoye. Il sera corrige par le formateur.",
                  "success")
        else:
            flash("Travail envoye. Il sera corrige par le formateur.", "success")

        if ex["est_evaluation_finale"]:
            check_and_create_certificate(
                conn, session["user_id"], niveau_id
            )

        return redirect(url_for("level_detail", niveau_id=niveau_id))

    finally:
        conn.close()


# =========================================================
# FONCTION : VERIFIER ET CREER LE CERTIFICAT
# =========================================================

def check_and_create_certificate(conn, user_id, niveau_id):
    evaluations = conn.execute("""
        SELECT e.id AS exercice_id, e.type, e.partie,
               MAX(s.note) AS meilleure_note
        FROM exercices e
        LEFT JOIN soumissions s
            ON s.exercice_id = e.id
            AND s.user_id = ?
            AND s.note IS NOT NULL
        WHERE e.niveau_id = ?
          AND e.est_evaluation_finale = 1
        GROUP BY e.id
    """, (user_id, niveau_id)).fetchall()

    if not evaluations:
        return False

    total_obtenu = 0.0
    total_attendu = 0.0

    for ev in evaluations:
        points_max = 20.0 if ev["partie"] == "qcm" else 4.0
        total_attendu += points_max

        if ev["meilleure_note"] is not None:
            if ev["partie"] == "qcm":
                note_ramenee = min(ev["meilleure_note"], 20.0)
            else:
                note_ramenee = min(ev["meilleure_note"] / 20 * 4, 4.0)
            total_obtenu += note_ramenee

    if total_attendu == 0:
        return False

    pourcentage = (total_obtenu / total_attendu) * 100

    if pourcentage < 90:
        flash(
            f"Score insuffisant : {total_obtenu:.1f}/{total_attendu:.0f} "
            f"({pourcentage:.1f}%). Le seuil est de 90%. "
            f"Vous pouvez refaire l'evaluation depuis la page du niveau.",
            "warning"
        )
        return False

    existing = conn.execute("""
        SELECT id FROM certificats
        WHERE user_id = ? AND niveau_id = ?
    """, (user_id, niveau_id)).fetchone()

    if existing:
        return False

    niveau_info = conn.execute("""
        SELECT n.id, n.formation_id, f.nom AS formation_nom
        FROM niveaux n JOIN formations f ON f.id = n.formation_id
        WHERE n.id = ?
    """, (niveau_id,)).fetchone()

    if not niveau_info:
        return False

    numero = build_numero_certificat(user_id, niveau_id)

    try:
        conn.execute("""
            INSERT INTO certificats(
                user_id, niveau_id, formation_id,
                numero_certificat, score_obtenu,
                score_total, pourcentage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, niveau_id, niveau_info["formation_id"],
            numero, round(total_obtenu, 2),
            round(total_attendu, 2), round(pourcentage, 2)
        ))

        conn.execute("""
            UPDATE inscriptions
            SET statut = 'completed',
                progression = 100,
                date_completion = COALESCE(date_completion, CURRENT_TIMESTAMP)
            WHERE user_id = ? AND niveau_id = ?
        """, (user_id, niveau_id))

        conn.commit()

        flash(
            f"Felicitations ! Vous avez obtenu votre certification "
            f"avec {total_obtenu:.1f}/{total_attendu:.0f} "
            f"({pourcentage:.1f}%).",
            "success"
        )
        return True

    except sqlite3.IntegrityError:
        conn.rollback()
        return False


# =========================================================
# FORMATEUR — CREATION
# =========================================================

@app.post("/trainer/formation/create")
@role_required("trainer")
def create_formation():
    nom = request.form.get("nom", "").strip()
    description = request.form.get("description", "").strip()
    categorie = request.form.get("categorie", "data").strip()

    if not nom:
        flash("Le nom de la formation est obligatoire.", "danger")
        return redirect_to_section("creer-formation")

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO formations(nom, description, categorie, trainer_id)
            VALUES (?, ?, ?, ?)
        """, (nom, description, categorie, session["user_id"]))
        conn.commit()
        flash("Formation créée.", "success")
    finally:
        conn.close()
    return redirect_to_section("creer-formation")


@app.post("/trainer/level/create/<int:formation_id>")
@role_required("trainer")
def create_level(formation_id):
    numero = request.form.get("numero", type=int)
    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    prix = request.form.get("prix", type=float)

    conn = get_db()
    try:
        owned = conn.execute(
            "SELECT id FROM formations WHERE id=? AND trainer_id=?",
            (formation_id, session["user_id"])).fetchone()
        if not owned:
            flash("Formation non autorisée.", "danger")
            return redirect_to_section("niveaux")

        if not numero or not titre or prix is None or prix < 0:
            flash("Veuillez saisir numéro, titre et prix correctement.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("""
            INSERT INTO niveaux(formation_id, numero, titre, description, prix)
            VALUES (?, ?, ?, ?, ?)
        """, (formation_id, numero, titre, description, prix))
        conn.commit()
        flash("Niveau ajouté.", "success")
    except sqlite3.IntegrityError:
        flash("Ce numéro de niveau existe déjà pour cette formation.", "danger")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


@app.post("/trainer/chapitre/create/<int:niveau_id>")
@role_required("trainer")
def create_chapitre(niveau_id):
    numero = request.form.get("numero", type=int)
    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()

    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
            WHERE n.id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not owned:
            flash("Niveau non autorisé.", "danger")
            return redirect_to_section("niveaux")

        if not numero or not titre:
            flash("Veuillez saisir un numéro et un titre.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("""
            INSERT INTO chapitres(niveau_id, numero, titre, description)
            VALUES (?, ?, ?, ?)
        """, (niveau_id, numero, titre, description))
        conn.commit()
        flash("Chapitre créé.", "success")
    except sqlite3.IntegrityError:
        flash("Ce numéro existe déjà.", "danger")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


@app.post("/trainer/lecon/create/<int:chapitre_id>")
@role_required("trainer")
def create_lecon(chapitre_id):
    numero = request.form.get("numero", type=int)
    titre = request.form.get("titre", "").strip()
    contenu = request.form.get("contenu", "").strip()
    duree = request.form.get("duree", type=int) or 5

    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT c.id FROM chapitres c
            JOIN niveaux n ON n.id = c.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE c.id = ? AND f.trainer_id = ?
        """, (chapitre_id, session["user_id"])).fetchone()

        if not owned:
            flash("Non autorisé.", "danger")
            return redirect_to_section("niveaux")

        if not numero or not titre or not contenu:
            flash("Veuillez remplir tous les champs.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("""
            INSERT INTO lecons(chapitre_id, numero, titre, contenu, duree)
            VALUES (?, ?, ?, ?, ?)
        """, (chapitre_id, numero, titre, contenu, duree))
        conn.commit()
        flash("Leçon créée.", "success")
    except sqlite3.IntegrityError:
        flash("Ce numéro de leçon existe déjà.", "danger")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


@app.post("/trainer/chapitre/<int:chapitre_id>/delete")
@role_required("trainer")
def delete_chapitre(chapitre_id):
    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT c.id FROM chapitres c
            JOIN niveaux n ON n.id = c.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE c.id = ? AND f.trainer_id = ?
        """, (chapitre_id, session["user_id"])).fetchone()
        if not owned:
            flash("Non autorisé.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("DELETE FROM chapitres WHERE id = ?", (chapitre_id,))
        conn.commit()
        flash("Chapitre supprimé.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


@app.post("/trainer/lecon/<int:lecon_id>/delete")
@role_required("trainer")
def delete_lecon(lecon_id):
    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT l.id FROM lecons l
            JOIN chapitres c ON c.id = l.chapitre_id
            JOIN niveaux n ON n.id = c.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE l.id = ? AND f.trainer_id = ?
        """, (lecon_id, session["user_id"])).fetchone()
        if not owned:
            flash("Non autorisé.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("DELETE FROM lecons WHERE id = ?", (lecon_id,))
        conn.commit()
        flash("Leçon supprimée.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


# =========================================================
# FORMATEUR — VOIR UNE LECON (APERCU)
# =========================================================

@app.get("/trainer/lecon/<int:lecon_id>/view")
@role_required("trainer")
def view_lecon_trainer(lecon_id):
    """Apercu d'une lecon cote formateur (ne marque pas comme lue)."""
    conn = get_db()
    try:
        lecon = conn.execute("""
            SELECT l.*, c.titre AS chapitre_titre, c.niveau_id,
                   c.numero AS chapitre_numero,
                   n.titre AS niveau_titre, n.numero AS niveau_numero,
                   f.nom AS formation_nom, f.id AS formation_id
            FROM lecons l
            JOIN chapitres c ON c.id = l.chapitre_id
            JOIN niveaux n ON n.id = c.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE l.id = ? AND f.trainer_id = ?
        """, (lecon_id, session["user_id"])).fetchone()

        if not lecon:
            flash("Leçon introuvable ou non autorisée.", "danger")
            return redirect_to_section("niveaux")

        lecon_prec = conn.execute("""
            SELECT id FROM lecons
            WHERE chapitre_id = ? AND numero < ?
            ORDER BY numero DESC LIMIT 1
        """, (lecon["chapitre_id"], lecon["numero"])).fetchone()

        lecon_suiv = conn.execute("""
            SELECT id FROM lecons
            WHERE chapitre_id = ? AND numero > ?
            ORDER BY numero ASC LIMIT 1
        """, (lecon["chapitre_id"], lecon["numero"])).fetchone()

        return render_template("lecon_apercu.html",
                               lecon=lecon,
                               lecon_prec=lecon_prec,
                               lecon_suiv=lecon_suiv)
    finally:
        conn.close()


# =========================================================
# FORMATEUR — MODIFIER UNE LECON
# =========================================================

@app.route("/trainer/lecon/<int:lecon_id>/edit", methods=["GET", "POST"])
@role_required("trainer")
def edit_lecon(lecon_id):
    """Modification d'une lecon existante."""
    conn = get_db()

    try:
        lecon = conn.execute("""
            SELECT l.*, c.titre AS chapitre_titre, c.niveau_id,
                   c.numero AS chapitre_numero,
                   n.titre AS niveau_titre,
                   f.nom AS formation_nom
            FROM lecons l
            JOIN chapitres c ON c.id = l.chapitre_id
            JOIN niveaux n ON n.id = c.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE l.id = ? AND f.trainer_id = ?
        """, (lecon_id, session["user_id"])).fetchone()

        if not lecon:
            flash("Leçon introuvable ou non autorisée.", "danger")
            return redirect_to_section("niveaux")

        if request.method == "POST":
            numero = request.form.get("numero", type=int)
            titre = request.form.get("titre", "").strip()
            contenu = request.form.get("contenu", "").strip()
            duree = request.form.get("duree", type=int) or 5

            if not numero or not titre or not contenu:
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                return render_template("lecon_edit.html", lecon=lecon)

            conflict = conn.execute("""
                SELECT id FROM lecons
                WHERE chapitre_id = ? AND numero = ? AND id != ?
            """, (lecon["chapitre_id"], numero, lecon_id)).fetchone()

            if conflict:
                flash(
                    f"Le numéro {numero} est déjà utilisé par une autre leçon "
                    f"de ce chapitre.",
                    "danger"
                )
                return render_template("lecon_edit.html", lecon=lecon)

            conn.execute("""
                UPDATE lecons
                SET numero = ?, titre = ?, contenu = ?, duree = ?
                WHERE id = ?
            """, (numero, titre, contenu, duree, lecon_id))
            conn.commit()

            flash(f"Leçon « {titre} » modifiée avec succès.", "success")
            return redirect_to_section("niveaux")

        return render_template("lecon_edit.html", lecon=lecon)
    finally:
        conn.close()


@app.post("/trainer/exercise/create-v2/<int:niveau_id>")
@role_required("trainer")
def create_exercise_v2(niveau_id):
    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    ex_type = request.form.get("type", "texte")
    contenu = request.form.get("contenu", "").strip()
    langage = request.form.get("langage", "").strip()
    reponse_attendue = request.form.get("reponse_attendue", "").strip()
    plateforme_url = request.form.get("plateforme_url", "").strip() or None

    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
            WHERE n.id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not owned:
            flash("Non autorisé.", "danger")
            return redirect_to_section("niveaux")

        if not titre:
            flash("Titre obligatoire.", "danger")
            return redirect_to_section("niveaux")

        corrige_auto = 1 if ex_type == "qcm" else 0

        conn.execute("""
            INSERT INTO exercices(niveau_id, titre, description, type,
                                  langage, contenu, reponse_attendue,
                                  plateforme_url, corrige_auto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (niveau_id, titre, description, ex_type, langage,
              contenu, reponse_attendue, plateforme_url, corrige_auto))
        conn.commit()
        flash("Exercice créé.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


@app.post("/trainer/pretest/create/<int:niveau_id>")
@role_required("trainer")
def create_pretest(niveau_id):
    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    seuil = request.form.get("seuil", type=int) or 70

    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT n.id FROM niveaux n JOIN formations f ON f.id = n.formation_id
            WHERE n.id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not owned:
            flash("Non autorisé.", "danger")
            return redirect_to_section("niveaux")

        questions = []
        i = 0
        while True:
            q_text = request.form.get(f"question_{i}", "").strip()
            if not q_text:
                break

            options = []
            for j in range(4):
                opt = request.form.get(f"q{i}_opt{j}", "").strip()
                if opt:
                    options.append(opt)

            bonne = request.form.get(f"q{i}_bonne", type=int)
            if len(options) >= 2 and bonne is not None:
                questions.append({
                    "question": q_text,
                    "options": options,
                    "bonne": bonne
                })
            i += 1

        if len(questions) < 3:
            flash("Veuillez ajouter au moins 3 questions.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("""
            INSERT OR REPLACE INTO pretests
            (niveau_id, titre, description, seuil_reussite, qcm_data)
            VALUES (?, ?, ?, ?, ?)
        """, (niveau_id, titre or "Pré-test", description, seuil,
              json.dumps(questions)))
        conn.commit()
        flash("Pré-test enregistré.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


# =========================================================
# FORMATEUR — VOIR UN EXERCICE (APERCU)
# =========================================================

@app.get("/trainer/exercise/<int:exercice_id>/view")
@role_required("trainer")
def view_exercise_trainer(exercice_id):
    """Apercu d'un exercice cote formateur."""
    conn = get_db()
    try:
        ex = conn.execute("""
            SELECT e.*,
                   n.titre AS niveau_titre, n.numero AS niveau_numero,
                   f.nom AS formation_nom, f.id AS formation_id
            FROM exercices e
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE e.id = ? AND f.trainer_id = ?
        """, (exercice_id, session["user_id"])).fetchone()

        if not ex:
            flash("Exercice introuvable ou non autorisé.", "danger")
            return redirect_to_section("niveaux")

        return render_template("exercice_apercu.html", ex=ex)
    finally:
        conn.close()


# =========================================================
# FORMATEUR — MODIFIER UN EXERCICE
# =========================================================

@app.route("/trainer/exercise/<int:exercice_id>/edit", methods=["GET", "POST"])
@role_required("trainer")
def edit_exercise(exercice_id):
    """Modification d'un exercice existant."""
    conn = get_db()

    try:
        ex = conn.execute("""
            SELECT e.*,
                   n.titre AS niveau_titre, n.numero AS niveau_numero,
                   f.nom AS formation_nom
            FROM exercices e
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE e.id = ? AND f.trainer_id = ?
        """, (exercice_id, session["user_id"])).fetchone()

        if not ex:
            flash("Exercice introuvable ou non autorisé.", "danger")
            return redirect_to_section("niveaux")

        if request.method == "POST":
            titre = request.form.get("titre", "").strip()
            description = request.form.get("description", "").strip()
            ex_type = request.form.get("type", "texte")
            langage = request.form.get("langage", "").strip()
            contenu = request.form.get("contenu", "").strip()
            reponse_attendue = request.form.get("reponse_attendue", "").strip()
            plateforme_url = request.form.get("plateforme_url", "").strip() or None
            qcm_data = request.form.get("qcm_data", "").strip()

            if not titre:
                flash("Le titre est obligatoire.", "danger")
                return render_template("exercice_edit.html", ex=ex)

            qcm_json = None
            corrige_auto = 0

            if ex_type == "qcm":
                corrige_auto = 1
                if qcm_data:
                    try:
                        parsed = json.loads(qcm_data)
                        if not isinstance(parsed, list) or len(parsed) == 0:
                            raise ValueError("Format invalide")
                        qcm_json = json.dumps(parsed)
                    except (json.JSONDecodeError, ValueError):
                        flash(
                            "Le format du QCM est invalide. "
                            "Veuillez corriger le JSON.",
                            "danger"
                        )
                        return render_template("exercice_edit.html", ex=ex)
                else:
                    qcm_json = ex["qcm_data"]

            conn.execute("""
                UPDATE exercices
                SET titre = ?, description = ?, type = ?, langage = ?,
                    contenu = ?, reponse_attendue = ?, plateforme_url = ?,
                    qcm_data = ?, corrige_auto = ?
                WHERE id = ?
            """, (titre, description, ex_type, langage,
                  contenu, reponse_attendue, plateforme_url,
                  qcm_json, corrige_auto, exercice_id))
            conn.commit()

            flash(f"Exercice « {titre} » modifié avec succès.", "success")
            return redirect_to_section("niveaux")

        return render_template("exercice_edit.html", ex=ex)
    finally:
        conn.close()


# =========================================================
# FORMATEUR — SUPPRIMER UN EXERCICE
# =========================================================

@app.post("/trainer/exercise/<int:exercice_id>/delete")
@role_required("trainer")
def delete_exercise(exercice_id):
    """Suppression d'un exercice."""
    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT e.id, e.titre FROM exercices e
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE e.id = ? AND f.trainer_id = ?
        """, (exercice_id, session["user_id"])).fetchone()

        if not owned:
            flash("Exercice non autorisé.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("DELETE FROM soumissions WHERE exercice_id = ?",
                     (exercice_id,))
        conn.execute("DELETE FROM exercices WHERE id = ?", (exercice_id,))
        conn.commit()

        flash(f"Exercice « {owned['titre']} » supprimé.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


# =========================================================
# FORMATEUR — VOIR UN PRE-TEST (APERCU)
# =========================================================

@app.get("/trainer/pretest/<int:niveau_id>/view")
@role_required("trainer")
def view_pretest_trainer(niveau_id):
    """Apercu d'un pre-test cote formateur."""
    conn = get_db()
    try:
        pretest = conn.execute("""
            SELECT p.*,
                   n.titre AS niveau_titre, n.numero AS niveau_numero,
                   f.nom AS formation_nom, f.id AS formation_id
            FROM pretests p
            JOIN niveaux n ON n.id = p.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE p.niveau_id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not pretest:
            flash("Pré-test introuvable ou non autorisé.", "danger")
            return redirect_to_section("niveaux")

        return render_template("pretest_apercu.html", pretest=pretest)
    finally:
        conn.close()


# =========================================================
# FORMATEUR — MODIFIER UN PRE-TEST
# =========================================================

@app.route("/trainer/pretest/<int:niveau_id>/edit", methods=["GET", "POST"])
@role_required("trainer")
def edit_pretest(niveau_id):
    """Modification d'un pre-test existant."""
    conn = get_db()

    try:
        pretest = conn.execute("""
            SELECT p.*,
                   n.titre AS niveau_titre, n.numero AS niveau_numero,
                   f.nom AS formation_nom
            FROM pretests p
            JOIN niveaux n ON n.id = p.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE p.niveau_id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not pretest:
            flash("Pré-test introuvable ou non autorisé.", "danger")
            return redirect_to_section("niveaux")

        if request.method == "POST":
            titre = request.form.get("titre", "").strip()
            description = request.form.get("description", "").strip()
            seuil = request.form.get("seuil", type=int) or 70

            questions = []
            i = 0
            while True:
                q_text = request.form.get(f"question_{i}", "").strip()
                if not q_text:
                    break

                options = []
                for j in range(4):
                    opt = request.form.get(f"q{i}_opt{j}", "").strip()
                    if opt:
                        options.append(opt)

                bonne = request.form.get(f"q{i}_bonne", type=int)
                if len(options) >= 2 and bonne is not None:
                    questions.append({
                        "question": q_text,
                        "options": options,
                        "bonne": bonne
                    })
                i += 1

            if not titre:
                flash("Le titre est obligatoire.", "danger")
                return render_template("pretest_edit.html", pretest=pretest)

            if len(questions) < 3:
                flash("Veuillez ajouter au moins 3 questions.", "danger")
                return render_template("pretest_edit.html", pretest=pretest)

            conn.execute("""
                UPDATE pretests
                SET titre = ?, description = ?, seuil_reussite = ?, qcm_data = ?
                WHERE niveau_id = ?
            """, (titre, description, seuil, json.dumps(questions), niveau_id))
            conn.commit()

            flash(f"Pré-test « {titre} » modifié avec succès.", "success")
            return redirect_to_section("niveaux")

        return render_template("pretest_edit.html", pretest=pretest)
    finally:
        conn.close()


# =========================================================
# FORMATEUR — SUPPRIMER UN PRE-TEST
# =========================================================

@app.post("/trainer/pretest/<int:niveau_id>/delete")
@role_required("trainer")
def delete_pretest(niveau_id):
    """Suppression d'un pre-test."""
    conn = get_db()
    try:
        owned = conn.execute("""
            SELECT p.id, p.titre FROM pretests p
            JOIN niveaux n ON n.id = p.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE p.niveau_id = ? AND f.trainer_id = ?
        """, (niveau_id, session["user_id"])).fetchone()

        if not owned:
            flash("Pré-test non autorisé.", "danger")
            return redirect_to_section("niveaux")

        conn.execute("DELETE FROM soumissions_pretest WHERE pretest_id = ?",
                     (owned["id"],))
        conn.execute("DELETE FROM pretests WHERE id = ?", (owned["id"],))
        conn.commit()

        flash(f"Pré-test « {owned['titre']} » supprimé.", "success")
    finally:
        conn.close()
    return redirect_to_section("niveaux")


# =========================================================
# FORMATEUR — CORRECTION IA + NOTATION
# =========================================================

@app.post("/trainer/submission/<int:submission_id>/ai-correct")
@role_required("trainer")
def ai_correct_submission(submission_id):
    conn = get_db()
    try:
        sub = conn.execute("""
            SELECT s.*, e.description AS ex_description, e.reponse_attendue
            FROM soumissions s
            JOIN exercices e ON e.id = s.exercice_id
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE s.id = ? AND f.trainer_id = ?
        """, (submission_id, session["user_id"])).fetchone()

        if not sub:
            flash("Non autorisé.", "danger")
            return redirect_to_section("corrections")

        note_ia, comm_ia = ia_pre_correction(
            {"description": sub["ex_description"]},
            sub["contenu"] or ""
        )
        conn.execute("""
            UPDATE soumissions
            SET note_ia = ?, commentaire_ia = ?,
                date_correction_ia = CURRENT_TIMESTAMP,
                statut = CASE WHEN statut='submitted'
                              THEN 'ai_corrected' ELSE statut END
            WHERE id = ?
        """, (note_ia, comm_ia, submission_id))
        conn.commit()
        flash(f"Pré-correction IA : {note_ia}/20", "success")
    finally:
        conn.close()
    return redirect_to_section("corrections")


@app.post("/trainer/submission/<int:submission_id>/grade")
@role_required("trainer")
def grade_submission(submission_id):
    note = request.form.get("note", type=float)
    commentaire = request.form.get("commentaire", "").strip()

    if note is None or note < 0 or note > 20:
        flash("Note entre 0 et 20.", "danger")
        return redirect_to_section("corrections")

    conn = get_db()
    try:
        valid = conn.execute("""
            SELECT s.id, s.user_id, e.niveau_id
            FROM soumissions s
            JOIN exercices e ON e.id = s.exercice_id
            JOIN niveaux n ON n.id = e.niveau_id
            JOIN formations f ON f.id = n.formation_id
            WHERE s.id = ? AND f.trainer_id = ?
        """, (submission_id, session["user_id"])).fetchone()

        if not valid:
            flash("Non autorisé.", "danger")
            return redirect_to_section("corrections")

        conn.execute("""
            UPDATE soumissions SET note=?, commentaire=?, statut='graded'
            WHERE id=?
        """, (note, commentaire, submission_id))
        conn.commit()

        ex_check = conn.execute("""
            SELECT e.est_evaluation_finale
            FROM soumissions s
            JOIN exercices e ON e.id = s.exercice_id
            WHERE s.id = ?
        """, (submission_id,)).fetchone()

        if ex_check and ex_check["est_evaluation_finale"]:
            check_and_create_certificate(
                conn, valid["user_id"], valid["niveau_id"]
            )

        flash("Note enregistrée.", "success")
    finally:
        conn.close()
    return redirect_to_section("corrections")


# =========================================================
# ADMIN — VALIDER PAIEMENT / FORMATEUR
# =========================================================

@app.post("/admin/payment/<int:payment_id>/<action>")
@role_required("admin")
def admin_payment(payment_id, action):
    if action not in ("approve", "reject"):
        flash("Action invalide.", "danger")
        return redirect_to_section("paiements-admin")

    conn = get_db()
    try:
        p = conn.execute("SELECT * FROM paiements WHERE id = ?",
                         (payment_id,)).fetchone()
        if not p:
            flash("Paiement introuvable.", "danger")
            return redirect_to_section("paiements-admin")

        if action == "approve":
            niveau = conn.execute(
                "SELECT formation_id FROM niveaux WHERE id = ?",
                (p["niveau_id"],)).fetchone()

            actif = conn.execute("""
                SELECT i.id, n.numero FROM inscriptions i
                JOIN niveaux n ON n.id = i.niveau_id
                WHERE i.user_id = ? AND i.formation_id = ?
                AND i.statut = 'active'
            """, (p["user_id"], niveau["formation_id"])).fetchone()

            if actif:
                conn.execute("UPDATE paiements SET statut='cancelled' WHERE id=?",
                             (payment_id,))
                conn.commit()
                flash(f"Impossible : l'étudiant a déjà le niveau "
                      f"{actif['numero']} actif.", "danger")
                return redirect_to_section("paiements-admin")

            conn.execute("UPDATE paiements SET statut='paid' WHERE id=?",
                         (payment_id,))
            conn.execute("""
                INSERT OR IGNORE INTO inscriptions
                (user_id, niveau_id, formation_id, progression, statut)
                VALUES (?, ?, ?, 0, 'active')
            """, (p["user_id"], p["niveau_id"], niveau["formation_id"]))
            message = "Paiement validé et niveau activé."
        else:
            conn.execute("UPDATE paiements SET statut='rejected' WHERE id=?",
                         (payment_id,))
            message = "Paiement refusé."

        conn.commit()
        flash(message, "success")
    finally:
        conn.close()
    return redirect_to_section("paiements-admin")


@app.post("/admin/trainer/<int:trainer_id>/approve")
@role_required("admin")
def approve_trainer(trainer_id):
    conn = get_db()
    try:
        conn.execute("""
            UPDATE users SET statut_validation='approved',
                date_validation=CURRENT_TIMESTAMP, motif_refus=NULL
            WHERE id=? AND role='trainer'
        """, (trainer_id,))
        conn.commit()
        flash("Formateur approuvé.", "success")
    finally:
        conn.close()
    return redirect_to_section("formateurs-validation")


@app.post("/admin/trainer/<int:trainer_id>/reject")
@role_required("admin")
def reject_trainer(trainer_id):
    motif = request.form.get("motif_refus", "").strip()
    if not motif:
        flash("Motif requis.", "danger")
        return redirect_to_section("formateurs-validation")

    conn = get_db()
    try:
        conn.execute("""
            UPDATE users SET statut_validation='rejected',
                date_validation=CURRENT_TIMESTAMP, motif_refus=?
            WHERE id=? AND role='trainer'
        """, (motif, trainer_id))
        conn.commit()
        flash("Formateur refusé.", "success")
    finally:
        conn.close()
    return redirect_to_section("formateurs-validation")


@app.get("/uploads/<filename>")
@login_required
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# =========================================================
# MOT DE PASSE / COMPTE
# =========================================================

@app.post("/change-password")
@login_required
def change_password():
    current_pwd = request.form.get("current_password", "")
    new_pwd = request.form.get("new_password", "")
    confirm_pwd = request.form.get("confirm_password", "")

    if not all([current_pwd, new_pwd, confirm_pwd]):
        flash("Tous les champs sont requis.", "danger")
        return redirect_to_section("compte")

    if new_pwd != confirm_pwd:
        flash("Mots de passe différents.", "danger")
        return redirect_to_section("compte")

    if len(new_pwd) < 6:
        flash("Minimum 6 caractères.", "danger")
        return redirect_to_section("compte")

    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?",
                            (session["user_id"],)).fetchone()
        if not user or not check_password_hash(user["password"], current_pwd):
            flash("Mot de passe actuel incorrect.", "danger")
            return redirect_to_section("compte")

        conn.execute("UPDATE users SET password = ? WHERE id = ?",
                     (generate_password_hash(new_pwd), session["user_id"]))
        conn.commit()
        flash("Mot de passe modifié.", "success")
    finally:
        conn.close()
    return redirect_to_section("compte")


@app.post("/delete-account")
@login_required
def delete_account():
    password = request.form.get("confirm_delete_password", "")
    if not password:
        flash("Mot de passe requis.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?",
                            (session["user_id"],)).fetchone()
        if not user or not check_password_hash(user["password"], password):
            flash("Mot de passe incorrect.", "danger")
            return redirect(url_for("dashboard"))

        if user["role"] == "admin":
            admins = conn.execute(
                "SELECT COUNT(*) AS total FROM users WHERE role='admin'"
            ).fetchone()["total"]
            if admins <= 1:
                flash("Impossible : dernier administrateur.", "danger")
                return redirect(url_for("dashboard"))

        conn.execute("UPDATE formations SET trainer_id=NULL WHERE trainer_id=?",
                     (session["user_id"],))
        conn.execute("DELETE FROM users WHERE id=?", (session["user_id"],))
        conn.commit()
        session.clear()
        flash("Compte supprimé.", "success")
    finally:
        conn.close()
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_pwd = request.form.get("new_password", "")
        confirm_pwd = request.form.get("confirm_password", "")
        security_answer = request.form.get("security_answer", "").strip().lower()

        conn = get_db()
        try:
            user = conn.execute("SELECT * FROM users WHERE email=?",
                                (email,)).fetchone()
            if not user:
                flash("Aucun compte.", "danger")
                return redirect(url_for("forgot_password"))

            expected = (user["nom"] + user["prenom"]).lower()
            if security_answer != expected:
                flash("Réponse incorrecte.", "danger")
                return redirect(url_for("forgot_password"))

            if new_pwd != confirm_pwd or len(new_pwd) < 6:
                flash("Mots de passe invalides.", "danger")
                return redirect(url_for("forgot_password"))

            conn.execute("UPDATE users SET password=? WHERE id=?",
                         (generate_password_hash(new_pwd), user["id"]))
            conn.commit()
            flash("Mot de passe réinitialisé.", "success")
            return redirect(url_for("index"))
        finally:
            conn.close()

    return render_template("forgot_password.html")


# =========================================================
# GENERATION DE CERTIFICAT PDF (AVEC LOGO)
# =========================================================

def generate_certificate_pdf(user, niveau, formation, certificat):
    buffer = io.BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    primary = HexColor("#087ee8")
    secondary = HexColor("#6630d8")
    dark = HexColor("#102f59")
    light_gray = HexColor("#e4e9f1")
    text_color = HexColor("#172033")

    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    margin = 15 * mm
    c.setStrokeColor(primary)
    c.setLineWidth(6)
    c.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)

    c.setStrokeColor(secondary)
    c.setLineWidth(2)
    inner_margin = margin + 3 * mm
    c.rect(inner_margin, inner_margin,
           page_width - 2 * inner_margin,
           page_height - 2 * inner_margin)

    # ========== BANDEAU SUPERIEUR ==========
    banner_height = 30 * mm
    banner_y = page_height - margin - 3 * mm - banner_height

    c.setFillColor(primary)
    c.rect(inner_margin, banner_y,
           page_width - 2 * inner_margin, banner_height,
           fill=1, stroke=0)

    # ---------- LOGO dans le bandeau ----------
    logo_path = BASE_DIR / "static" / "images" / "logo.jpg"
    logo_size = 22 * mm
    logo_x = inner_margin + 15 * mm
    logo_y = banner_y + (banner_height - logo_size) / 2

    try:
        if logo_path.exists():
            # Fond blanc rond derriere le logo (pour contraste)
            c.setFillColor(white)
            c.circle(
                logo_x + logo_size / 2,
                logo_y + logo_size / 2,
                logo_size / 2 + 1.5 * mm,
                fill=1, stroke=0
            )

            c.drawImage(
                str(logo_path),
                logo_x, logo_y,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True,
                mask='auto'
            )
    except Exception as e:
        print(f"[CERTIFICAT] Impossible de charger le logo : {e}")

    # ---------- TEXTE decale a droite ----------
    text_center_x = page_width / 2 + 15 * mm

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(text_center_x, banner_y + 15 * mm, "SOFT LEARN")

    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(HexColor("#c7d5e8"))
    c.drawCentredString(text_center_x, banner_y + 8 * mm,
                        "Apprendre. Pratiquer. Progresser.")

    # ========== TITRE PRINCIPAL ==========
    title_y = banner_y - 25 * mm
    c.setFillColor(secondary)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_width / 2, title_y + 10 * mm,
                        "CERTIFICAT DE REUSSITE")

    c.setStrokeColor(secondary)
    c.setLineWidth(2)
    line_width = 60 * mm
    c.line(page_width / 2 - line_width / 2, title_y + 6 * mm,
           page_width / 2 + line_width / 2, title_y + 6 * mm)

    # ========== CORPS DU CERTIFICAT ==========
    body_start_y = title_y - 15 * mm

    c.setFillColor(text_color)
    c.setFont("Helvetica", 13)
    c.drawCentredString(page_width / 2, body_start_y,
                        "Ce certificat est decerne a")

    full_name = f"{user['prenom']} {user['nom']}"
    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(page_width / 2, body_start_y - 15 * mm, full_name)

    c.setStrokeColor(light_gray)
    c.setLineWidth(1)
    name_line_width = 130 * mm
    c.line(page_width / 2 - name_line_width / 2, body_start_y - 18 * mm,
           page_width / 2 + name_line_width / 2, body_start_y - 18 * mm)

    c.setFillColor(text_color)
    c.setFont("Helvetica", 13)
    c.drawCentredString(page_width / 2, body_start_y - 27 * mm,
                        "pour avoir reussi avec succes le niveau")

    level_title = f"{formation['nom']} - {niveau['titre']}"
    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(page_width / 2, body_start_y - 37 * mm, level_title)

    c.setFillColor(text_color)
    c.setFont("Helvetica", 12)
    score_text = (f"avec un score de "
                  f"{int(certificat['score_obtenu'])}/{int(certificat['score_total'])} "
                  f"({certificat['pourcentage']:.1f}%)")
    c.drawCentredString(page_width / 2, body_start_y - 46 * mm, score_text)

    # ========== BAS DE PAGE ==========
    bottom_y = margin + 25 * mm

    c.setFillColor(secondary)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 25 * mm, bottom_y + 5 * mm, "DATE D'OBTENTION")

    c.setFillColor(text_color)
    c.setFont("Helvetica", 11)
    date_str = certificat['date_obtention'][:10]
    c.drawString(margin + 25 * mm, bottom_y, date_str)

    c.setStrokeColor(dark)
    c.setLineWidth(1)
    sig_width = 60 * mm
    sig_x = page_width / 2 - sig_width / 2
    c.line(sig_x, bottom_y + 3 * mm, sig_x + sig_width, bottom_y + 3 * mm)

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_width / 2, bottom_y - 5 * mm, "Soft Learn")
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(text_color)
    c.drawCentredString(page_width / 2, bottom_y - 11 * mm,
                        "Direction pedagogique")

    c.setFillColor(secondary)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(page_width - margin - 25 * mm,
                      bottom_y + 5 * mm, "NUMERO")
    c.setFillColor(text_color)
    c.setFont("Helvetica", 10)
    c.drawRightString(page_width - margin - 25 * mm,
                      bottom_y, certificat['numero_certificat'])

    # ========== SCEAU / MEDAILLE ==========
    seal_x = page_width - margin - 40 * mm
    seal_y = bottom_y + 20 * mm
    seal_radius = 15 * mm

    c.setFillColor(secondary)
    c.circle(seal_x, seal_y, seal_radius, fill=1, stroke=0)

    c.setFillColor(primary)
    c.circle(seal_x, seal_y, seal_radius - 2 * mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(seal_x, seal_y - 4 * mm, "OK")

    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(seal_x, seal_y - 11 * mm, "CERTIFIE")

    # ========== FILIGRANE ==========
    c.saveState()
    c.setFillColor(HexColor("#f5f8fc"))
    c.setFont("Helvetica-Bold", 120)
    c.translate(page_width / 2, page_height / 2)
    c.rotate(30)
    c.setFillAlpha(0.08)
    c.drawCentredString(0, 0, "SOFT LEARN")
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def build_numero_certificat(user_id, niveau_id):
    now = datetime.now()
    return f"SL-{now.year}{now.month:02d}-{user_id:04d}-{niveau_id:04d}"


@app.route("/certificate/<int:niveau_id>")
@login_required
def download_certificate(niveau_id):
    user_id = session["user_id"]
    conn = get_db()
    try:
        certificat = conn.execute("""
            SELECT * FROM certificats
            WHERE user_id = ? AND niveau_id = ?
        """, (user_id, niveau_id)).fetchone()

        if not certificat:
            flash("Aucun certificat trouve pour ce niveau.", "danger")
            return redirect(url_for("level_detail", niveau_id=niveau_id))

        user = conn.execute("SELECT * FROM users WHERE id = ?",
                            (user_id,)).fetchone()

        niveau = conn.execute("""
            SELECT n.*, f.nom AS formation_nom, f.id AS formation_id
            FROM niveaux n JOIN formations f ON f.id = n.formation_id
            WHERE n.id = ?
        """, (niveau_id,)).fetchone()

        formation = {"nom": niveau["formation_nom"]}

        buffer = generate_certificate_pdf(user, niveau, formation, certificat)

        filename = f"certificat_{certificat['numero_certificat']}.pdf"
        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response
    finally:
        conn.close()


# =========================================================
# ROUTE TEMPORAIRE : INITIALISER LA BASE POSTGRESQL
# ⚠️ À SUPPRIMER APRÈS UTILISATION
# =========================================================

@app.route("/init-db-secret-xyz-2026")
def init_db_secret():
    """Route temporaire pour initialiser la base PostgreSQL sur Render."""
    import psycopg2
    from werkzeug.security import generate_password_hash

    if not config.USE_POSTGRES:
        return "❌ Cette route ne fonctionne qu'avec PostgreSQL."

    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cur = conn.cursor()

        # ---------- USERS ----------
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

        # ---------- FORMATIONS ----------
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

        # ---------- NIVEAUX ----------
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

        # ---------- INSCRIPTIONS ----------
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

        # ---------- PAIEMENTS ----------
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

        # ---------- CHAPITRES ----------
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

        # ---------- LECONS ----------
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

        # ---------- PROGRESSIONS LECONS ----------
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

        # ---------- EXERCICES ----------
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

        # ---------- SOUMISSIONS ----------
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

        # ---------- PRETESTS ----------
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

        # ---------- SOUMISSIONS PRETEST ----------
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

        # ---------- CERTIFICATS ----------
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

        # ---------- PROGRESSION ETUDIANT ----------
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

        # ---------- ADMIN PAR DEFAUT ----------
        cur.execute("SELECT id FROM users WHERE email = %s",
                    ("admin@softlearn.com",))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users(nom, prenom, email, password, role, statut_validation)
                VALUES (%s, %s, %s, %s, 'admin', 'approved')
            """, ("Admin", "Soft Learn", "admin@softlearn.com",
                  generate_password_hash("admin123")))

        # ---------- FORMATEUR DEMO ----------
        cur.execute("SELECT id FROM users WHERE email = %s",
                    ("trainer@softlearn.com",))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users(nom, prenom, email, password, role,
                                  statut_validation, diplome, experience)
                VALUES (%s, %s, %s, %s, 'trainer', 'approved', %s, %s)
            """, ("Formateur", "Demo", "trainer@softlearn.com",
                  generate_password_hash("trainer123"),
                  "Master en Informatique",
                  "5 ans d'experience en formation."))

        conn.commit()
        cur.close()
        conn.close()

        return """
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1 style="color: #20a464;">✅ TOUTES les tables creees !</h1>
            <p>13 tables + admin + formateur.</p>
            <p><strong>Admin :</strong> admin@softlearn.com / admin123</p>
            <p><strong>Formateur :</strong> trainer@softlearn.com / trainer123</p>
            <hr>
            <p style="color: #d97706;">
                ⚠️ <strong>IMPORTANT :</strong> Supprimez cette route de <code>app.py</code>
                puis poussez sur GitHub pour raisons de securite.
            </p>
            <p><a href="/">Retour au site</a></p>
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px;">
            <h1 style="color: #e74c3c;">❌ Erreur</h1>
            <pre>{e}</pre>
        </body>
        </html>
        """


# =========================================================
# ROUTE TEMPORAIRE : PEUPLER LA BASE (seed)
# ⚠️ À SUPPRIMER APRÈS UTILISATION
# =========================================================

@app.route("/seed-db-secret-xyz-2026")
def seed_db_secret():
    """Route temporaire pour inserer les donnees initiales."""
    import psycopg2

    if not config.USE_POSTGRES:
        return "❌ Cette route ne fonctionne qu'avec PostgreSQL."

    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cur = conn.cursor()

        # ---------- Recupere le formateur ----------
        cur.execute("SELECT id FROM users WHERE email = %s",
                    ("trainer@softlearn.com",))
        trainer = cur.fetchone()
        if not trainer:
            return "❌ Formateur demo introuvable. Lancez /init-db-secret-xyz-2026 d'abord."
        trainer_id = trainer[0]

        # ---------- Donnees formations ----------
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

        count_formations = 0
        count_niveaux = 0

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
                count_formations += 1

            for n in f["niveaux"]:
                cur.execute("""
                    SELECT id FROM niveaux WHERE formation_id = %s AND numero = %s
                """, (fid, n["numero"]))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO niveaux(formation_id, numero, titre, description, prix)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (fid, n["numero"], n["titre"], n["description"], n["prix"]))
                    count_niveaux += 1

        conn.commit()
        cur.close()
        conn.close()

        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1 style="color: #20a464;">✅ Base peuplee !</h1>
            <p><strong>{count_formations}</strong> nouvelles formations creees</p>
            <p><strong>{count_niveaux}</strong> nouveaux niveaux crees</p>
            <p>Total : 8 formations et 24 niveaux attendus</p>
            <hr>
            <p><a href="/dashboard">Aller au dashboard</a></p>
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px;">
            <h1 style="color: #e74c3c;">❌ Erreur</h1>
            <pre>{e}</pre>
        </body>
        </html>
        """
                
# =========================================================
# LANCEMENT
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)