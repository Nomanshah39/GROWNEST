const form = document.querySelector("#store-form");
const statusPill = document.querySelector("#connection-status");
const toast = document.querySelector("#toast");
const reportButton = document.querySelector("#generate-report");
const topProductSearch = document.querySelector("#top-product-search");
const topProductSearchDropdown = document.querySelector("#top-product-results");
const productNameFilter = document.querySelector("#product-filter-name");
const productFilterForm = document.querySelector("#product-filter-form");
const productFilterReset = document.querySelector("#product-filter-reset");
const productSearchDropdown = document.querySelector("#product-filter-results");
const productModal = document.querySelector("#product-detail-modal");
const productModalCloseButtons = document.querySelectorAll("[data-close-product-modal]");

let latestPayload = {};
let latestAnalysis = null;
let allProducts = [];
let statMode = "income";
let chartResizeTimer = null;
let activeProductSearchInput = null;

const money = new Intl.NumberFormat("en-PK", {
  style: "currency",
  currency: "PKR",
  currencyDisplay: "code",
  maximumFractionDigits: 0,
});

function formPayload() {
  return {
    sellerName: document.querySelector("#seller-name").value,
    platform: document.querySelector("#platform").value,
    monthlyBudget: Number(document.querySelector("#monthly-budget").value || 250000),
    horizonDays: Number(document.querySelector("#horizon-days").value || 84),
  };
}

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function setStatus(label) {
  if (statusPill) statusPill.textContent = label;
}

async function analyzeStore(event) {
  if (event) event.preventDefault();
  latestPayload = formPayload();
  setStatus("Analyzing");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestPayload),
    });

    if (!response.ok) {
      setStatus("Error");
      showToast("Analysis failed");
      return;
    }

    const payload = await response.json();
    renderDashboard(payload);
    setStatus("Connected");
    showToast("Growth analysis ready");
  } catch (error) {
    setStatus("Error");
    showToast("Could not connect to the dashboard API");
  }
}

function renderDashboard(payload) {
  const analysis = payload.analysis;
  const overview = analysis.overview || {};
  const monthly = analysis.monthlyStats || {};

  latestAnalysis = analysis;
  allProducts = analysis.products || [];

  setText("#dashboard-title", `${payload.seller} on ${payload.platform}`);
  setText("#seller-card-name", payload.seller);
  setText(".profile-pill span", payload.seller);
  setMoneyText("#wallet-balance", monthly.revenue || overview.revenue || 0, { compact: true });
  setText("#wallet-platform", payload.platform);
  setText("#wallet-window", `${latestPayload.horizonDays || 84}d`);
  setMoneyText("#cashflow-total", monthly.revenue || overview.revenue || 0);
  setText("#updated-at", `Updated ${new Date(payload.generatedAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`);

  setMetric("#metric-revenue", "#metric-revenue-growth", monthly.revenue || 0, monthly.revenueGrowth || 0);
  setMetric("#metric-profit", "#metric-profit-growth", monthly.profit || 0, monthly.profitGrowth || 0);
  setMoneyText("#metric-roas", monthly.expenses || 0, { compact: true });
  setDelta("#metric-ad-growth", `Expense ${monthly.expenseGrowth || 0}%`, monthly.expenseGrowth || 0);

  renderBudget(overview);
  updateProductFilterOptions(allProducts);
  renderFilteredProducts();
  renderGrowthPlans(allProducts);
  renderStatisticList(monthly);
  renderActivity(analysis);
  renderSeasonalDemand(analysis.seasonalDemand || {});
  redrawCharts();
}

function setText(selector, text) {
  const element = document.querySelector(selector);
  if (element) element.textContent = text;
}

function setMetric(valueSelector, deltaSelector, value, delta) {
  setMoneyText(valueSelector, value, { compact: true });
  setDelta(deltaSelector, `${delta}%`, delta);
}

function setMoneyText(selector, value, options = {}) {
  const element = document.querySelector(selector);
  if (!element) return;

  const fullValue = money.format(value);
  element.textContent = options.compact ? formatCompactMoney(value) : fullValue;
  element.title = fullValue;
  element.setAttribute("aria-label", fullValue);
}

function moneyMarkup(value, options = {}) {
  const fullValue = money.format(value);
  const displayValue = options.compact ? formatCompactMoney(value) : fullValue;
  return `<strong title="${escapeHtml(fullValue)}" aria-label="${escapeHtml(fullValue)}">${escapeHtml(displayValue)}</strong>`;
}

function setDelta(selector, text, delta) {
  const element = document.querySelector(selector);
  if (!element) return;
  element.textContent = text;
  element.classList.toggle("negative", Number(delta) < 0);
}

function renderBudget(overview) {
  const total = Number(latestPayload.monthlyBudget || 250000);
  const spent = Number(overview.adSpend || 0);
  const share = Math.min(100, Math.max(0, (spent / Math.max(1, total)) * 100));
  setText("#budget-used", money.format(spent));
  setText("#budget-total", money.format(total));
  setText("#budget-share", `${share.toFixed(1)}%`);
  const bar = document.querySelector("#budget-bar");
  if (bar) bar.style.width = `${share}%`;
}

function updateProductFilterOptions(products) {
  const categorySelect = document.querySelector("#product-filter-category");
  if (!categorySelect) return;

  const selected = categorySelect.value;
  const categories = [...new Set(products.map((item) => item.category).filter(Boolean))].sort();
  categorySelect.innerHTML = [
    '<option value="">All categories</option>',
    ...categories.map((category) => `<option>${escapeHtml(category)}</option>`),
  ].join("");
  categorySelect.value = categories.includes(selected) ? selected : "";
}

function renderFilteredProducts(options = {}) {
  const filtered = applyProductFilters(allProducts);
  renderProducts(filtered);
  setText("#filter-count", `${filtered.length} product${filtered.length === 1 ? "" : "s"}`);

  if (options.showDropdown !== false) {
    renderProductSearchDropdown(filtered, options.targetInput || activeProductSearchInput);
  }
}

function applyProductFilters(products) {
  const name = readFilterValue("#product-filter-name").toLowerCase();
  const category = readFilterValue("#product-filter-category");
  const stock = readFilterValue("#product-filter-stock");
  const demand = readFilterValue("#product-filter-demand");
  const minPriceValue = readFilterValue("#product-filter-min-price");
  const maxPriceValue = readFilterValue("#product-filter-max-price");
  const minPrice = minPriceValue === "" ? null : Number(minPriceValue);
  const maxPrice = maxPriceValue === "" ? null : Number(maxPriceValue);

  return products.filter((item) => {
    const price = Number(item.price || 0);
    const searchableText = [
      item.product,
      item.category,
      item.stockStatus,
      item.demandLevel,
      item.demandTrend,
      item.suggestion,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesName = !name || searchableText.includes(name);
    const matchesCategory = !category || item.category === category;
    const matchesStock = !stock || item.stockStatus === stock;
    const matchesDemand = !demand || item.demandLevel === demand;
    const matchesMin = minPrice === null || Number.isNaN(minPrice) || price >= minPrice;
    const matchesMax = maxPrice === null || Number.isNaN(maxPrice) || price <= maxPrice;
    return matchesName && matchesCategory && matchesStock && matchesDemand && matchesMin && matchesMax;
  });
}

function readFilterValue(selector) {
  const element = document.querySelector(selector);
  return element ? element.value.trim() : "";
}

function hasActiveProductFilters() {
  return [
    "#product-filter-name",
    "#product-filter-category",
    "#product-filter-stock",
    "#product-filter-demand",
    "#product-filter-min-price",
    "#product-filter-max-price",
  ].some((selector) => readFilterValue(selector) !== "");
}

function getProductSearchTarget(targetInput = null) {
  const input = targetInput || activeProductSearchInput || document.activeElement;

  if (input === topProductSearch && topProductSearchDropdown) {
    return { input: topProductSearch, dropdown: topProductSearchDropdown };
  }

  if (productNameFilter && productSearchDropdown) {
    return { input: productNameFilter, dropdown: productSearchDropdown };
  }

  if (topProductSearch && topProductSearchDropdown) {
    return { input: topProductSearch, dropdown: topProductSearchDropdown };
  }

  return null;
}

function getProductSearchDropdowns() {
  return [productSearchDropdown, topProductSearchDropdown].filter(Boolean);
}

function renderProductSearchDropdown(products, targetInput = null) {
  const target = getProductSearchTarget(targetInput);
  if (!target) return;

  const { input, dropdown } = target;
  const hasFilters = hasActiveProductFilters();
  if (!hasFilters) {
    hideProductSearchDropdown();
    return;
  }

  const safeProducts = Array.isArray(products) ? products : applyProductFilters(allProducts);

  if (safeProducts.length === 0) {
    dropdown.innerHTML = `<div class="product-search-empty">No products found</div>`;
    showProductSearchDropdown(target);
    return;
  }

  const shownProducts = safeProducts.slice(0, 8);
  const remaining = safeProducts.length - shownProducts.length;
  dropdown.innerHTML = [
    ...shownProducts.map((item) => {
      const index = allProducts.indexOf(item);
      return `
        <button class="product-search-result" type="button" role="option" data-product-index="${index}">
          <span>
            <strong>${escapeHtml(item.product)}</strong>
            <small>${escapeHtml(item.category)} • ${money.format(item.price || 0)} • ${Number(item.stock || 0)} left</small>
          </span>
          <b class="status-badge ${badgeClass(item.demandLevel)}">${escapeHtml(item.demandLevel)}</b>
        </button>
      `;
    }),
    remaining > 0 ? `<div class="product-search-more">+${remaining} more product${remaining === 1 ? "" : "s"}</div>` : "",
  ].join("");

  showProductSearchDropdown(target);
  input.setAttribute("aria-activedescendant", "");
}

function showProductSearchDropdown(target = null) {
  const activeTarget = target || getProductSearchTarget();
  if (!activeTarget) return;

  getProductSearchDropdowns().forEach((dropdown) => {
    if (dropdown !== activeTarget.dropdown) dropdown.hidden = true;
  });

  [productNameFilter, topProductSearch].filter(Boolean).forEach((input) => {
    input.setAttribute("aria-expanded", String(input === activeTarget.input));
  });

  activeTarget.dropdown.hidden = false;
}

function hideProductSearchDropdown(target = null) {
  if (target) {
    target.dropdown.hidden = true;
    target.input.setAttribute("aria-expanded", "false");
    return;
  }

  getProductSearchDropdowns().forEach((dropdown) => {
    dropdown.hidden = true;
  });

  [productNameFilter, topProductSearch].filter(Boolean).forEach((input) => {
    input.setAttribute("aria-expanded", "false");
  });
}

function openProductFromIndex(index) {
  const product = allProducts[Number(index)];
  if (product) openProductModal(product);
}

function openProductModal(product) {
  if (!productModal) return;

  setText("#product-modal-title", product.product || "Product Details");
  setText("#product-modal-category", product.category || "Product");
  setText("#product-modal-trend", product.demandTrend || "");
  setText("#product-modal-price", money.format(product.price || 0));
  setText("#product-modal-stock", `${Number(product.stock || 0)} left • ${product.stockStatus || "Stock"}`);
  setText("#product-modal-demand", product.demandLevel || "Demand");
  setText("#product-modal-units", Number(product.units || 0).toLocaleString("en-PK"));
  setText("#product-modal-suggestion", product.suggestion || "No suggestion available.");

  productModal.hidden = false;
  document.body.classList.add("modal-open");
  hideProductSearchDropdown();

  const closeButton = productModal.querySelector(".product-modal-close");
  if (closeButton) closeButton.focus();
}

function closeProductModal() {
  if (!productModal) return;
  productModal.hidden = true;
  document.body.classList.remove("modal-open");
}

function renderProducts(products) {
  const table = document.querySelector("#product-table");
  if (!table) return;

  if (products.length === 0) {
    table.innerHTML = `
      <tr>
        <td colspan="6">
          <strong>No products found</strong><br>
          <span class="page-subtitle">Try changing the filters.</span>
        </td>
      </tr>
    `;
    return;
  }

  table.innerHTML = products
    .map(
      (item) => `
        <tr class="product-table-row" data-product-index="${allProducts.indexOf(item)}" tabindex="0" aria-label="View details for ${escapeHtml(item.product)}">
          <td>${escapeHtml(item.product)}<br><span class="page-subtitle">${escapeHtml(item.demandTrend)}</span></td>
          <td>${escapeHtml(item.category)}</td>
          <td>${money.format(item.price || 0)}</td>
          <td>
            <span class="status-badge ${badgeClass(item.stockStatus)}">${escapeHtml(item.stockStatus)}</span>
            <br><span class="page-subtitle">${Number(item.stock || 0)} left</span>
          </td>
          <td>
            <span class="status-badge ${badgeClass(item.demandLevel)}">${escapeHtml(item.demandLevel)}</span>
            <br><span class="page-subtitle">${Number(item.units || 0).toLocaleString("en-PK")} units</span>
          </td>
          <td>${escapeHtml(item.suggestion)}</td>
        </tr>
      `
    )
    .join("");
}

function renderGrowthPlans(products) {
  const target = document.querySelector("#growth-plans");
  if (!target) return;
  target.innerHTML = products
    .slice(0, 3)
    .map((item) => {
      const progress = item.demandLevel === "High demand" ? 88 : item.demandLevel === "Medium demand" ? 58 : 32;
      const initials = item.product
        .split(" ")
        .map((word) => word[0])
        .join("")
        .slice(0, 2);
      return `
        <div class="plan-card">
          <div class="plan-card-header">
            <div class="plan-icon">${escapeHtml(initials)}</div>
            <strong>${escapeHtml(item.product)}</strong>
            <span class="mini-pill">${escapeHtml(item.demandLevel)}</span>
          </div>
          <div class="progress-track"><span style="width: ${progress}%"></span></div>
          <div class="plan-meta">
            <span>${escapeHtml(item.stockStatus)}</span>
            <span>${escapeHtml(item.suggestion)}</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderStatisticList(monthly) {
  const rows = statMode === "income" ? monthly.incomeByCategory || [] : monthly.expenseByCategory || [];
  const total = statMode === "income" ? Number(monthly.revenue || 0) : Number(monthly.expenses || 0);
  const label = statMode === "income" ? "Income" : "Expense";
  setText("#stat-label", label);
  setMoneyText("#stat-total", total, { compact: true });
  updateStatisticTabs();

  const ring = document.querySelector("#stat-ring");
  const target = document.querySelector("#statistic-list");
  if (!target) return;

  const top = rows.slice(0, 5);
  const topShare = top.reduce((sum, item) => sum + Number(item.share || 0), 0);
  if (ring) {
    const degrees = Math.min(360, Math.round((topShare / 100) * 360));
    const primary = statMode === "income" ? "var(--deep)" : "var(--amber)";
    const secondary = statMode === "income" ? "var(--lime)" : "var(--blue)";
    ring.style.background = `conic-gradient(${primary} 0 ${degrees}deg, ${secondary} ${degrees}deg ${Math.min(
      360,
      degrees + 58
    )}deg, #e6ebe5 ${Math.min(360, degrees + 58)}deg 338deg, #f3f5f3 338deg 360deg)`;
  }

  target.innerHTML = top
    .map(
      (item) => `
        <div class="category-item">
          <b>${Number(item.share || 0).toFixed(0)}%</b>
          <span>${escapeHtml(item.category)}</span>
          ${moneyMarkup(item.value || 0, { compact: true })}
        </div>
      `
    )
    .join("");
}

function updateStatisticTabs() {
  document.querySelectorAll("[data-stat-mode]").forEach((button) => {
    const isActive = button.dataset.statMode === statMode;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function renderActivity(analysis) {
  const target = document.querySelector("#activity-list");
  if (!target) return;
  const items = (analysis.simpleInsights || []).slice(0, 5);

  target.innerHTML = items
    .map((item) => {
      const initials = item.title
        .split(" ")
        .map((word) => word[0])
        .join("")
        .slice(0, 2);
      return `
        <div class="activity-item">
          <div class="activity-avatar">${escapeHtml(initials)}</div>
          <div>
            <strong>${escapeHtml(item.value)}</strong>
            <p>${escapeHtml(item.detail)}</p>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderSeasonalDemand(seasonalDemand) {
  const products = seasonalDemand.products || [];
  setText("#seasonal-season", `${seasonalDemand.currentSeason || "Current season"} demand`);
  setText("#seasonal-tracking-note", seasonalDemand.trackingNote || "");
  renderSeasonalDemandList(products);
}

function renderSeasonalDemandList(products) {
  const target = document.querySelector("#seasonal-demand-list");
  if (!target) return;

  target.innerHTML = products
    .slice(0, 4)
    .map(
      (item) => `
        <div class="seasonal-item">
          <div>
            <strong>${escapeHtml(item.product)}</strong>
            <span>${escapeHtml(item.trend)} - ${escapeHtml(item.restock)}</span>
          </div>
          <b class="${badgeClass(item.demandLevel)}">${escapeHtml(item.demandLevel)}</b>
        </div>
      `
    )
    .join("");
}

function redrawCharts() {
  if (!latestAnalysis) return;
  renderSalesOverviewChart(latestAnalysis.dailyRevenue || []);
  renderProductDemandChart(allProducts);
  renderSeasonalDemandChart((latestAnalysis.seasonalDemand || {}).products || []);
}

function renderSalesOverviewChart(points) {
  const prepared = prepareCanvas("#revenue-chart");
  if (!prepared) return;
  const { ctx, width, height } = prepared;
  const data = compactChartPoints(points, width < 540 ? 7 : 14);
  const max = Math.max(...data.flatMap((point) => [point.revenue, point.expense, Math.abs(point.profit)]), 1);
  const left = width < 520 ? 42 : 58;
  const right = 18;
  const top = 34;
  const bottom = 48;
  const plotWidth = Math.max(1, width - left - right);
  const plotHeight = Math.max(1, height - top - bottom);
  const baseY = top + plotHeight;
  const groupWidth = plotWidth / Math.max(1, data.length);
  const barWidth = Math.max(7, Math.min(22, groupWidth * 0.26));

  clearCanvas(ctx, width, height);
  drawGrid(ctx, width, left, right, top, plotHeight, max);

  const profitPoints = [];
  data.forEach((point, index) => {
    const x = left + index * groupWidth + groupWidth / 2;
    const incomeHeight = (plotHeight * point.revenue) / max;
    const expenseHeight = (plotHeight * point.expense) / max;
    const profitY = baseY - (plotHeight * Math.max(0, point.profit)) / max;

    roundRect(ctx, x - barWidth - 2, baseY - incomeHeight, barWidth, incomeHeight, 5, "#1f5147");
    roundRect(ctx, x + 2, baseY - expenseHeight, barWidth, expenseHeight, 5, "#f1b84b");
    profitPoints.push([x, profitY]);

    ctx.fillStyle = "#737d79";
    ctx.font = "700 11px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(point.label, x, height - 20);
  });

  drawLine(ctx, profitPoints, "#5e9a91");
  drawLegend(ctx, [
    ["Income", "#1f5147"],
    ["Expense", "#f1b84b"],
    ["Profit", "#5e9a91"],
  ]);
}

function renderProductDemandChart(products) {
  const prepared = prepareCanvas("#product-demand-chart");
  if (!prepared) return;
  const { ctx, width, height } = prepared;
  const data = [...products].sort((a, b) => Number(b.units || 0) - Number(a.units || 0)).slice(0, width < 540 ? 5 : 7);
  const max = Math.max(...data.map((item) => Number(item.units || 0)), 1);
  const left = width < 540 ? 120 : 170;
  const right = 24;
  const top = 24;
  const rowHeight = Math.max(28, (height - top - 28) / Math.max(1, data.length));

  clearCanvas(ctx, width, height);
  data.forEach((item, index) => {
    const y = top + index * rowHeight;
    const barWidth = ((width - left - right) * Number(item.units || 0)) / max;
    ctx.fillStyle = "#31403d";
    ctx.font = "800 12px system-ui";
    ctx.textAlign = "right";
    ctx.fillText(shorten(item.product, width < 540 ? 16 : 24), left - 12, y + 17);
    roundRect(ctx, left, y + 4, Math.max(4, barWidth), 18, 6, demandColor(item.demandLevel));
    ctx.fillStyle = "#737d79";
    ctx.font = "700 11px system-ui";
    ctx.textAlign = "left";
    ctx.fillText(`${Number(item.units || 0).toLocaleString("en-PK")} units`, left + Math.max(8, barWidth) + 8, y + 17);
  });
}

function renderSeasonalDemandChart(products) {
  const prepared = prepareCanvas("#seasonal-demand-chart");
  if (!prepared) return;
  const { ctx, width, height } = prepared;
  const data = products.slice(0, 5);
  const max = Math.max(...data.map((item) => Number(item.units || 0)), 1);
  const left = width < 320 ? 96 : 126;
  const right = 14;
  const top = 22;
  const rowHeight = Math.max(28, (height - top - 18) / Math.max(1, data.length));

  clearCanvas(ctx, width, height);
  data.forEach((item, index) => {
    const y = top + index * rowHeight;
    const barWidth = ((width - left - right) * Number(item.units || 0)) / max;
    ctx.fillStyle = "#31403d";
    ctx.font = "800 11px system-ui";
    ctx.textAlign = "right";
    ctx.fillText(shorten(item.product, width < 330 ? 12 : 17), left - 10, y + 16);
    roundRect(ctx, left, y + 4, Math.max(5, barWidth), 17, 6, demandColor(item.demandLevel));
  });
}

function compactChartPoints(points, targetCount) {
  if (points.length <= targetCount) return points;
  const size = Math.ceil(points.length / targetCount);
  const buckets = [];
  for (let index = 0; index < points.length; index += size) {
    const bucket = points.slice(index, index + size);
    const last = bucket[bucket.length - 1];
    buckets.push({
      label: last.date,
      revenue: sum(bucket, "revenue"),
      expense: sum(bucket, "expense"),
      profit: sum(bucket, "profit"),
    });
  }
  return buckets;
}

function sum(items, key) {
  return items.reduce((total, item) => total + Number(item[key] || 0), 0);
}

function prepareCanvas(selector) {
  const canvas = document.querySelector(selector);
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(240, Math.floor(rect.width || canvas.width));
  const height = Math.max(180, Math.floor(rect.height || canvas.height));
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { canvas, ctx, width, height };
}

function clearCanvas(ctx, width, height) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
}

function drawGrid(ctx, width, left, right, top, plotHeight, max) {
  ctx.strokeStyle = "#e6ebe6";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#737d79";
  ctx.font = "700 11px system-ui";
  ctx.textAlign = "right";

  for (let index = 0; index <= 4; index += 1) {
    const y = top + (plotHeight / 4) * index;
    const value = max - (max / 4) * index;
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(width - right, y);
    ctx.stroke();
    ctx.fillText(formatShortMoney(value), left - 8, y + 4);
  }
}

function drawLine(ctx, points, color) {
  if (points.length === 0) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach(([x, y], index) => {
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  points.forEach(([x, y]) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawLegend(ctx, items) {
  let x = 18;
  items.forEach(([label, color]) => {
    ctx.fillStyle = color;
    ctx.fillRect(x, 14, 11, 11);
    ctx.fillStyle = "#31403d";
    ctx.font = "800 12px system-ui";
    ctx.textAlign = "left";
    ctx.fillText(label, x + 17, 24);
    x += label.length * 8 + 44;
  });
}

function roundRect(ctx, x, y, width, height, radius, color) {
  const safeHeight = Math.max(0, height);
  const safeWidth = Math.max(0, width);
  const safeRadius = Math.min(radius, safeHeight / 2, safeWidth / 2);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x + safeRadius, y);
  ctx.lineTo(x + safeWidth - safeRadius, y);
  ctx.quadraticCurveTo(x + safeWidth, y, x + safeWidth, y + safeRadius);
  ctx.lineTo(x + safeWidth, y + safeHeight - safeRadius);
  ctx.quadraticCurveTo(x + safeWidth, y + safeHeight, x + safeWidth - safeRadius, y + safeHeight);
  ctx.lineTo(x + safeRadius, y + safeHeight);
  ctx.quadraticCurveTo(x, y + safeHeight, x, y + safeHeight - safeRadius);
  ctx.lineTo(x, y + safeRadius);
  ctx.quadraticCurveTo(x, y, x + safeRadius, y);
  ctx.fill();
}

function badgeClass(value) {
  return String(value || "")
    .toLowerCase()
    .replaceAll(" ", "-");
}

function demandColor(level) {
  if (level === "High demand") return "#1f5147";
  if (level === "Medium demand") return "#5e9a91";
  return "#f1b84b";
}

function formatShortMoney(value) {
  if (value >= 1000000) return `${Math.round(value / 1000000)}M`;
  if (value >= 1000) return `${Math.round(value / 1000)}K`;
  return `${Math.round(value)}`;
}

function formatCompactMoney(value) {
  const number = Number(value || 0);
  const amount = Math.abs(number);
  const sign = number < 0 ? "-" : "";
  const suffixes = [
    [1000000000, "B"],
    [1000000, "M"],
    [1000, "K"],
  ];

  for (const [threshold, suffix] of suffixes) {
    if (amount >= threshold) {
      const scaled = amount / threshold;
      const precision = scaled >= 100 ? 0 : 1;
      return `${sign}PKR ${scaled.toFixed(precision).replace(/\.0$/, "")}${suffix}`;
    }
  }

  return money.format(number);
}

function shorten(value, length) {
  const text = String(value);
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}.` : text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

if (reportButton) {
  reportButton.addEventListener("click", async () => {
    reportButton.disabled = true;
    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(latestPayload.platform ? latestPayload : formPayload()),
      });
      const payload = await response.json();
      showToast(response.ok ? `Report saved to ${payload.path}` : "Report generation failed");
    } catch (error) {
      showToast("Report generation failed");
    }
    reportButton.disabled = false;
  });
}

if (form) {
  form.addEventListener("submit", analyzeStore);
  analyzeStore();
}

if (productFilterForm) {
  const handleProductFilterChange = (event) => {
    activeProductSearchInput = productNameFilter;
    if (event && event.target === productNameFilter && topProductSearch) {
      topProductSearch.value = productNameFilter.value;
    }
    renderFilteredProducts({ targetInput: productNameFilter });
  };

  productFilterForm.addEventListener("submit", (event) => event.preventDefault());
  productFilterForm.addEventListener("input", handleProductFilterChange);
  productFilterForm.addEventListener("change", handleProductFilterChange);
  productFilterForm.addEventListener("focusin", () => {
    activeProductSearchInput = productNameFilter;
    renderProductSearchDropdown(applyProductFilters(allProducts), productNameFilter);
  });
}

getProductSearchDropdowns().forEach((dropdown) => {
  dropdown.addEventListener("click", (event) => {
    const option = event.target.closest("[data-product-index]");
    if (!option) return;
    openProductFromIndex(option.dataset.productIndex);
  });
});

const productTable = document.querySelector("#product-table");
if (productTable) {
  productTable.addEventListener("click", (event) => {
    const row = event.target.closest("[data-product-index]");
    if (row) openProductFromIndex(row.dataset.productIndex);
  });
  productTable.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const row = event.target.closest("[data-product-index]");
    if (!row) return;
    event.preventDefault();
    openProductFromIndex(row.dataset.productIndex);
  });
}

productModalCloseButtons.forEach((button) => {
  button.addEventListener("click", closeProductModal);
});

document.addEventListener("click", (event) => {
  const clickedInsideFilter = productFilterForm && productFilterForm.contains(event.target);
  const clickedInsideTopSearch = topProductSearch && topProductSearch.closest(".top-product-search-wrap")?.contains(event.target);
  const clickedInsideDropdown = getProductSearchDropdowns().some((dropdown) => dropdown.contains(event.target));

  if (!clickedInsideFilter && !clickedInsideTopSearch && !clickedInsideDropdown) {
    hideProductSearchDropdown();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  hideProductSearchDropdown();
  closeProductModal();
});

if (topProductSearch && productNameFilter) {
  topProductSearch.addEventListener("input", () => {
    activeProductSearchInput = topProductSearch;
    productNameFilter.value = topProductSearch.value;
    renderFilteredProducts({ targetInput: topProductSearch });
  });

  topProductSearch.addEventListener("focus", () => {
    activeProductSearchInput = topProductSearch;
    renderProductSearchDropdown(applyProductFilters(allProducts), topProductSearch);
  });
}

if (productFilterReset) {
  productFilterReset.addEventListener("click", () => {
    productFilterForm.reset();
    if (topProductSearch) topProductSearch.value = "";
    renderFilteredProducts();
  });
}

document.querySelectorAll("[data-stat-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    statMode = button.dataset.statMode || "income";
    if (latestAnalysis) renderStatisticList(latestAnalysis.monthlyStats || {});
  });
});

window.addEventListener("resize", () => {
  window.clearTimeout(chartResizeTimer);
  chartResizeTimer = window.setTimeout(redrawCharts, 120);
});
