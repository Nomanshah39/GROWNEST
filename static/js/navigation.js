document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector(".sidebar");
  const toggle = document.querySelector(".mobile-menu-toggle");
  const nav = document.querySelector("#primary-navigation");
  const mobileQuery = window.matchMedia("(max-width: 820px)");

  if (!sidebar || !toggle || !nav) return;

  function setMenuState(isOpen) {
    sidebar.classList.toggle("nav-open", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
    toggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
  }

  toggle.addEventListener("click", () => {
    setMenuState(!sidebar.classList.contains("nav-open"));
  });

  nav.addEventListener("click", (event) => {
    if (mobileQuery.matches && event.target.closest("a")) {
      setMenuState(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sidebar.classList.contains("nav-open")) {
      setMenuState(false);
      toggle.focus();
    }
  });

  mobileQuery.addEventListener("change", (event) => {
    if (!event.matches) setMenuState(false);
  });
});
