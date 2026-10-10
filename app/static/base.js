function cookieValue(name) {
  return document.cookie.split("; ").find(value => value.startsWith(name + "="))?.split("=").slice(1).join("=") || "";
}

document.querySelectorAll("form[method=post]").forEach(form => {
  if (!form.querySelector("input[name=csrf_token]")) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "csrf_token";
    input.value = decodeURIComponent(cookieValue("csrf_token"));
    form.prepend(input);
  }
});

document.querySelectorAll(".auto-submit").forEach(control => {
  control.addEventListener("change", () => control.form?.submit());
});

document.querySelectorAll("form.confirm-delete").forEach(form => {
  form.addEventListener("submit", event => {
    if (!window.confirm(form.dataset.confirm || "Confirmer la suppression ?")) event.preventDefault();
  });
});
