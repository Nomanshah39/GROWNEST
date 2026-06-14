const pageReportButton = document.querySelector("#generate-page-report");
const pageReportOutput = document.querySelector("#report-output");
const pageReportStatus = document.querySelector("#report-status");
const pageToast = document.querySelector("#toast");

function showPageToast(message) {
  if (!pageToast) return;
  pageToast.textContent = message;
  pageToast.classList.add("show");
  window.setTimeout(() => pageToast.classList.remove("show"), 2600);
}

if (pageReportButton) {
  pageReportButton.addEventListener("click", async () => {
    pageReportButton.disabled = true;
    pageReportButton.textContent = "Generating";

    const payload = {
      sellerName: pageReportButton.dataset.seller,
      platform: pageReportButton.dataset.platform,
      monthlyBudget: Number(pageReportButton.dataset.budget || 250000),
      horizonDays: Number(pageReportButton.dataset.days || 84),
    };

    const response = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      pageReportButton.disabled = false;
      pageReportButton.textContent = "Generate Report";
      showPageToast("Report generation failed");
      return;
    }

    const result = await response.json();
    pageReportOutput.textContent = result.report;
    pageReportStatus.textContent = `Saved ${new Date(result.generatedAt).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
    pageReportButton.disabled = false;
    pageReportButton.textContent = "Generate Report";
    showPageToast(`Report saved to ${result.path}`);
  });
}

