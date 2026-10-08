(() => {
  const form = document.getElementById("registration-form");
  if (!form) return;
  const button = document.getElementById("register-button");
  const error = document.getElementById("registration-error");
  const password = document.getElementById("new-password");
  const confirmation = document.getElementById("password-confirmation");
  let submitting = false;

  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (submitting || !form.reportValidity()) return;
    submitting = true;
    button.disabled = true;
    button.querySelector(".button-label").hidden = true;
    button.querySelector(".button-loading").hidden = false;
    error.hidden = true;
    const payload = {
      workshop_code: document.getElementById("workshop-code").value,
      password: password.value,
      password_confirmation: confirmation.value,
      participant: {
        language: document.getElementById("language").value,
        age_group: document.getElementById("age-group").value,
        gender: document.getElementById("gender").value,
        region: document.getElementById("region").value,
        consent_obtained: document.getElementById("consent").checked
      }
    };
    try {
      const response = await fetch("/api/auth/participant-registration", {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": document.getElementById("csrf-token").value},
        body: JSON.stringify(payload)
      });
      const contentType = response.headers.get("content-type") || "";
      const rawBody = await response.text();
      let body = null;
      if (contentType.includes("application/json")) {
        try {
          body = rawBody ? JSON.parse(rawBody) : {};
        } catch (_) {
          throw new Error(`Le serveur a retourné une réponse JSON invalide (${response.status}).`);
        }
      } else if (!response.ok) {
        throw new Error("Le service d’inscription est temporairement indisponible.");
      } else {
        throw new Error("Le serveur a retourné une réponse inattendue.");
      }
      if (!response.ok) throw new Error(body.detail || "Inscription impossible. Veuillez réessayer.");
      password.value = "";
      confirmation.value = "";
      document.getElementById("created-login-id").textContent = body.login_id;
      document.getElementById("registration-panel").hidden = true;
      const success = document.getElementById("registration-success");
      success.hidden = false;
      success.focus();
    } catch (problem) {
      password.value = "";
      confirmation.value = "";
      error.textContent = problem.message || "Inscription impossible. Veuillez réessayer.";
      error.hidden = false;
      password.focus();
    } finally {
      submitting = false;
      button.disabled = false;
      button.querySelector(".button-label").hidden = false;
      button.querySelector(".button-loading").hidden = true;
    }
  });

  document.getElementById("copy-login-id").addEventListener("click", async () => {
    const value = document.getElementById("created-login-id").textContent;
    try {
      await navigator.clipboard.writeText(value);
      document.getElementById("copy-status").textContent = "Identifiant copié.";
    } catch (_) {
      document.getElementById("copy-status").textContent = `Copiez cet identifiant : ${value}`;
    }
  });
})();
