/* SkillForge — helpers communs (Tache prio #2 : 1 JS partage, Ch5 static).
   postIA(url, data) : POST JSON + CSRF, gere erreurs reseau + JSON.
   Refonte : theme clair/sombre, burger mobile, toasts messages Django.
   postIA / showBox / csrfToken conserves intacts. */
(function () {
  "use strict";

  function csrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  }

  async function postIA(url, data, btn) {
    // Etat de chargement optionnel : passez le bouton declencheur en 3e arg.
    var label = null;
    if (btn) {
      label = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Génération…";
    }
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify(data || {}),
      });
      let payload = {};
      try {
        payload = await resp.json();
      } catch (e) {
        throw new Error("Réponse IA illisible (" + resp.status + ").");
      }
      if (!resp.ok) {
        throw new Error(payload.error || ("Erreur IA (" + resp.status + ")."));
      }
      return payload;
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = label;
      }
    }
  }

  function showBox(id, text) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.classList.remove("d-none");
  }

  /* ----- Theme clair / sombre (persistant) ----- */
  function initTheme() {
    const toggle = document.getElementById("sf-theme-toggle");
    if (!toggle) return;
    const root = document.documentElement;
    const paint = () => {
      toggle.textContent = root.dataset.theme === "dark" ? "☀" : "◐";
    };
    paint();
    toggle.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      try {
        localStorage.setItem("sf-theme", root.dataset.theme);
      } catch (e) {}
      paint();
    });
  }

  /* ----- Burger mobile (JS pur, remplace data-bs-toggle) ----- */
  function initBurger() {
    const burger = document.getElementById("sf-burger");
    const nav = document.getElementById("sf-nav");
    if (!burger || !nav) return;
    burger.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Ferme le menu quand on suit un lien (mobile).
    nav.addEventListener("click", (e) => {
      if (e.target.closest("a") && window.innerWidth < 992) {
        nav.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ----- Toasts : affiche les messages Django en haut a droite ----- */
  function toast(text, tags) {
    const box = document.getElementById("sf-toasts");
    if (!box) return;
    const el = document.createElement("div");
    el.className = "sf-toast " + (tags || "info");
    el.textContent = text;
    box.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.3s ease";
      setTimeout(() => el.remove(), 320);
    }, 4200);
  }

  function initToasts() {
    const src = document.getElementById("sf-django-messages");
    if (!src) return;
    src.querySelectorAll("div[data-tags]").forEach((d) => {
      toast(d.textContent.trim(), d.getAttribute("data-tags"));
    });
    src.remove();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initBurger();
    initToasts();
  });

  window.SkillForge = {
    postIA: postIA,
    showBox: showBox,
    csrfToken: csrfToken,
    toast: toast,
  };
})();
