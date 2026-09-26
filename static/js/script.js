/* =========================================================
   SOFT LEARN — SCRIPT PRINCIPAL
   ========================================================= */

let currentLanguage = localStorage.getItem("softlearn-language") || "fr";

/* =========================================================
   LANGUE
========================================================= */

function toggleLanguage() {
    currentLanguage = currentLanguage === "fr" ? "ar" : "fr";
    localStorage.setItem("softlearn-language", currentLanguage);
    updateLanguage();
}

function updateLanguage() {
    document.documentElement.lang = currentLanguage;
    document.documentElement.dir = currentLanguage === "ar" ? "rtl" : "ltr";

    const icon = document.getElementById("languageIcon");
    const text = document.getElementById("languageText");

    if (currentLanguage === "ar") {
        if (icon) icon.textContent = "🇩🇿";
        if (text) text.textContent = "العربية";
    } else {
        if (icon) icon.textContent = "🇫🇷";
        if (text) text.textContent = "Français";
    }

    document.querySelectorAll("[data-fr][data-ar]").forEach(function (el) {
        const value = el.getAttribute("data-" + currentLanguage);
        if (value !== null) el.textContent = value;
    });

    document.querySelectorAll("[data-placeholder-fr][data-placeholder-ar]").forEach(function (input) {
        input.placeholder = input.getAttribute("data-placeholder-" + currentLanguage);
    });
}

/* =========================================================
   MODE SOMBRE
========================================================= */

function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("softlearn-theme", isDark ? "dark" : "light");
    updateDarkModeButton();
}

function updateDarkModeButton() {
    const btn = document.getElementById("darkModeBtn");
    if (!btn) return;
    const isDark = document.body.classList.contains("dark-mode");
    btn.textContent = isDark ? "☀️" : "🌙";
}

function loadTheme() {
    if (localStorage.getItem("softlearn-theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
    updateDarkModeButton();
}

/* =========================================================
   MENU PROFIL
========================================================= */

function toggleProfileMenu() {
    const menu = document.getElementById("profileMenu");
    if (menu) menu.classList.toggle("show");
}

document.addEventListener("click", function (e) {
    const container = document.querySelector(".profile-container");
    const menu = document.getElementById("profileMenu");
    if (container && menu && !container.contains(e.target)) {
        menu.classList.remove("show");
    }
});

/* =========================================================
   NAVIGATION DASHBOARD (avec persistance)
========================================================= */

function showSection(name) {
    document.querySelectorAll(".dashboard-section").forEach(function (s) {
        s.classList.remove("active-section");
    });

    const section = document.getElementById("section-" + name);
    if (section) section.classList.add("active-section");

    document.querySelectorAll(".sidebar-link").forEach(function (link) {
        link.classList.remove("active");
        const onclick = link.getAttribute("onclick") || "";
        if (onclick.includes("'" + name + "'")) link.classList.add("active");
    });

    const profileMenu = document.getElementById("profileMenu");
    if (profileMenu) profileMenu.classList.remove("show");

    // Sauvegarder la section active
    localStorage.setItem("softlearn-last-section", name);

    window.scrollTo({ top: 0, behavior: "smooth" });
}

/* =========================================================
   VALIDATION QCM
========================================================= */

function validateQcm(form) {
    const questions = form.querySelectorAll(".app-qcm-question");
    let toutesRepondues = true;

    questions.forEach(function(q) {
        const radio = q.querySelector('input[type="radio"]:checked');
        if (!radio) {
            toutesRepondues = false;
            q.style.borderLeft = "4px solid #ef4444";
        } else {
            q.style.borderLeft = "none";
        }
    });

    if (!toutesRepondues) {
        alert(currentLanguage === "ar"
            ? "الرجاء الإجابة على جميع الأسئلة."
            : "Veuillez répondre à toutes les questions.");
        return false;
    }
    return true;
}

/* =========================================================
   VALIDATION INSCRIPTION
========================================================= */

function validateRegisterForm() {
    const pwd = document.getElementById("register-password");
    const confirm = document.getElementById("confirm-password");
    if (!pwd || !confirm) return true;

    if (pwd.value.length < 6) {
        alert(currentLanguage === "ar"
            ? "يجب أن تحتوي كلمة المرور على 6 أحرف على الأقل."
            : "Le mot de passe doit contenir au moins 6 caractères.");
        return false;
    }

    if (pwd.value !== confirm.value) {
        alert(currentLanguage === "ar"
            ? "كلمتا المرور غير متطابقتين."
            : "Les deux mots de passe ne correspondent pas.");
        return false;
    }

    return true;
}

/* =========================================================
   MODAL : SUPPRESSION DE COMPTE
========================================================= */

function confirmDeleteAccount() {
    const modal = document.getElementById("deleteAccountModal");
    if (modal) modal.classList.add("show");
}

function closeDeleteModal() {
    const modal = document.getElementById("deleteAccountModal");
    if (modal) modal.classList.remove("show");
}

/* =========================================================
   AFFICHER LES CHAMPS FORMATEUR
========================================================= */

function toggleTrainerFields() {
    const roleRadios = document.querySelectorAll('input[name="role"]');
    const trainerFields = document.getElementById("trainerFields");

    if (!trainerFields) return;

    roleRadios.forEach(function(radio) {
        radio.addEventListener("change", function() {
            if (this.value === "trainer" && this.checked) {
                trainerFields.style.display = "flex";
                document.getElementById("diplome").required = true;
                document.getElementById("experience").required = true;
                document.getElementById("cv").required = true;
                document.getElementById("diplome_file").required = true;
            } else if (this.value === "student" && this.checked) {
                trainerFields.style.display = "none";
                document.getElementById("diplome").required = false;
                document.getElementById("experience").required = false;
                document.getElementById("cv").required = false;
                document.getElementById("diplome_file").required = false;
            }
        });
    });
}

/* =========================================================
   MODAL REFUS FORMATEUR
========================================================= */

function openRejectModal(trainerId) {
    const modal = document.getElementById("rejectTrainerModal");
    const form = document.getElementById("rejectTrainerForm");
    if (modal && form) {
        form.action = "/admin/trainer/" + trainerId + "/reject";
        modal.classList.add("show");
    }
}

function closeRejectModal() {
    const modal = document.getElementById("rejectTrainerModal");
    if (modal) modal.classList.remove("show");
}

/* =========================================================
   CONFIRMATION SUPPRESSION
========================================================= */

function confirmDelete(msg) {
    return confirm(msg || "Êtes-vous sûr ?");
}

/* =========================================================
   AJOUT DE QUESTION PRÉ-TEST (formateur)
========================================================= */

let questionCount = 0;

function addQuestion() {
    const container = document.getElementById("questionsContainer");
    if (!container) return;

    const i = questionCount++;
    const html = `
        <div class="pretest-question-block" id="qblock_${i}">
            <div class="form-group">
                <label>Question ${i + 1}</label>
                <input name="question_${i}" placeholder="Énoncé de la question" required>
            </div>
            <div class="form-row">
                <input name="q${i}_opt0" placeholder="Option A" required>
                <input name="q${i}_opt1" placeholder="Option B" required>
            </div>
            <div class="form-row">
                <input name="q${i}_opt2" placeholder="Option C (optionnel)">
                <input name="q${i}_opt3" placeholder="Option D (optionnel)">
            </div>
            <div class="form-group">
                <label>Réponse correcte (0=A, 1=B, 2=C, 3=D)</label>
                <input type="number" name="q${i}_bonne" min="0" max="3" value="0" required>
            </div>
            <button type="button" class="dashboard-btn danger small"
                    onclick="document.getElementById('qblock_${i}').remove()">
                🗑️ Supprimer
            </button>
        </div>
    `;
    container.insertAdjacentHTML("beforeend", html);
}

/* =========================================================
   NOTIFICATIONS FLASH — AUTO-DISMISS + FERMETURE
========================================================= */

function initFlashMessages() {
    const flashes = document.querySelectorAll(".flash-message, .flash");

    flashes.forEach(function (flash) {
        // Ajouter un bouton de fermeture s'il n'existe pas
        if (!flash.querySelector(".flash-close")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "flash-close";
            btn.innerHTML = "×";
            btn.setAttribute("aria-label", "Fermer");
            btn.addEventListener("click", function () {
                closeFlash(flash);
            });
            flash.appendChild(btn);
        } else {
            // Brancher le bouton existant
            const existingBtn = flash.querySelector(".flash-close");
            existingBtn.addEventListener("click", function () {
                closeFlash(flash);
            });
        }

        // Auto-disparition apres 5 secondes
        setTimeout(function () {
            closeFlash(flash);
        }, 5000);
    });
}

function closeFlash(flash) {
    if (!flash) return;
    flash.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    flash.style.opacity = "0";
    flash.style.transform = "translateX(30px)";

    setTimeout(function () {
        if (flash.parentNode) {
            flash.parentNode.removeChild(flash);
        }
    }, 300);
}

/* =========================================================
   INITIALISATION AU CHARGEMENT
========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    loadTheme();
    updateLanguage();
    toggleTrainerFields();
    initFlashMessages();

    // --- Restaurer la section active (hash > localStorage) ---
    const hash = window.location.hash;
    let sectionName = null;

    if (hash && hash.startsWith("#section-")) {
        sectionName = hash.replace("#section-", "");
    } else {
        const last = localStorage.getItem("softlearn-last-section");
        if (last && document.getElementById("section-" + last)) {
            sectionName = last;
        }
    }

    if (sectionName && document.getElementById("section-" + sectionName)) {
        showSection(sectionName);
    }

    // --- Scroll fluide pour les ancres ---
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
        link.addEventListener("click", function (e) {
            const targetId = this.getAttribute("href");
            if (targetId && targetId !== "#" && !targetId.startsWith("#section-")) {
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }
        });
    });
});

/* =========================================================
   FERMER LES MODALES AVEC ESC
========================================================= */

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        closeDeleteModal();
        closeRejectModal();
    }
});

document.addEventListener("click", function (e) {
    const modalDelete = document.getElementById("deleteAccountModal");
    if (modalDelete && e.target === modalDelete) closeDeleteModal();

    const modalReject = document.getElementById("rejectTrainerModal");
    if (modalReject && e.target === modalReject) closeRejectModal();
});