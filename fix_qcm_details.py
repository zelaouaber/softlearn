import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=" * 60)
print("DIAGNOSTIC ET CORRECTION DES QCM SANS DETAILS")
print("=" * 60)

# 1. Verifier la colonne details
cols = [r[1] for r in conn.execute("PRAGMA table_info(soumissions)").fetchall()]
print(f"\n[INFO] Colonnes de 'soumissions' : {cols}")

if "details" not in cols:
    conn.execute("ALTER TABLE soumissions ADD COLUMN details TEXT")
    print("[OK] Colonne 'details' ajoutee.")
    conn.commit()

# 2. Trouver les soumissions QCM sans details
subs = conn.execute("""
    SELECT s.id, s.exercice_id, s.contenu, s.note,
           e.qcm_data, e.titre, e.niveau_id
    FROM soumissions s
    JOIN exercices e ON e.id = s.exercice_id
    WHERE e.type = 'qcm'
      AND (s.details IS NULL OR s.details = '')
""").fetchall()

print(f"\n[INFO] {len(subs)} soumission(s) QCM sans details trouvee(s).")

for s in subs:
    try:
        qcm_data = json.loads(s["qcm_data"] or "[]")
        reponses = json.loads(s["contenu"] or "[]")
    except (json.JSONDecodeError, TypeError):
        print(f"[SKIP] Soumission {s['id']} : donnees invalides")
        continue

    details = []
    for i, q in enumerate(qcm_data):
        rep = reponses[i] if i < len(reponses) else None
        try:
            est_correcte = rep is not None and int(rep) == q["bonne"]
        except (ValueError, TypeError):
            est_correcte = False

        details.append({
            "question": q["question"],
            "options": q["options"],
            "votre_reponse": int(rep) if rep is not None and str(rep).isdigit() else None,
            "bonne_reponse": q["bonne"],
            "correcte": est_correcte
        })

    conn.execute("""
        UPDATE soumissions SET details = ? WHERE id = ?
    """, (json.dumps(details), s["id"]))
    print(f"[OK] Soumission {s['id']} ({s['titre']}) mise a jour.")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("TERMINE")
print("=" * 60)