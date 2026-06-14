function labelResponsiveTables() {
  document.querySelectorAll("table").forEach((table) => {
    const headers = [...table.querySelectorAll("thead th")].map((header) => header.textContent.trim());
    table.querySelectorAll("tbody tr").forEach((row) => {
      [...row.children].forEach((cell, index) => {
        if (headers[index]) {
          cell.dataset.label = headers[index];
        }
      });
    });
  });
}

let responsiveTableTimer = null;

function scheduleResponsiveTableLabels() {
  window.clearTimeout(responsiveTableTimer);
  responsiveTableTimer = window.setTimeout(labelResponsiveTables, 40);
}

labelResponsiveTables();

new MutationObserver(scheduleResponsiveTableLabels).observe(document.body, {
  childList: true,
  subtree: true,
});

