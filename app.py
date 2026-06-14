from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from growth_agent.agent import ECommerceGrowthAgent
from growth_agent.data_factory import generate_sample_sales


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

NAV_ITEMS = [
    {"endpoint": "index", "label": "Dashboard", "icon": "grid"},
    {"endpoint": "connectors", "label": "Connectors", "icon": "plug"},
    {"endpoint": "insights", "label": "Insights", "icon": "bars"},
    {"endpoint": "campaigns", "label": "Campaigns", "icon": "target"},
    {"endpoint": "reports_page", "label": "Reports", "icon": "file"},
]

CONNECTOR_CARDS = [
    {
        "name": "Daraz",
        "status": "Connected",
        "sync": "Orders, products, stock, vouchers",
        "cadence": "Every 15 minutes",
        "health": "98%",
    },
    {
        "name": "Shopify",
        "status": "Ready",
        "sync": "Orders, customers, products, campaigns",
        "cadence": "Every 30 minutes",
        "health": "95%",
    },
    {
        "name": "Foodpanda Vendors",
        "status": "Ready",
        "sync": "Menu items, orders, ratings, delivery zones",
        "cadence": "Hourly",
        "health": "92%",
    },
    {
        "name": "Custom API / CSV",
        "status": "Configured",
        "sync": "CSV upload, REST API, spreadsheet export",
        "cadence": "Manual or daily",
        "health": "100%",
    },
]


def _payload() -> dict[str, Any]:
    data = request.get_json(silent=True) or {}
    return {
        "platform": str(data.get("platform") or "Daraz"),
        "seller_name": str(data.get("sellerName") or "Demo Seller").strip() or "Demo Seller",
        "monthly_budget": float(data.get("monthlyBudget") or 250000),
        "horizon_days": int(data.get("horizonDays") or 84),
    }


def _build_agent() -> tuple[ECommerceGrowthAgent, dict[str, Any]]:
    payload = _payload()
    sales = generate_sample_sales(
        platform=payload["platform"],
        days=payload["horizon_days"],
        monthly_budget=payload["monthly_budget"],
    )
    return ECommerceGrowthAgent(sales, payload["seller_name"], payload["platform"]), payload


def _report_files() -> list[dict[str, object]]:
    files = []
    for path in sorted(REPORTS_DIR.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        stat = path.stat()
        files.append(
            {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "updated": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y %I:%M %p"),
            }
        )
    return files


def _page_context(active_page: str) -> dict[str, Any]:
    agent, payload = _build_agent()
    analysis = agent.analyze()
    return {
        "active_page": active_page,
        "seller": payload["seller_name"],
        "platform": payload["platform"],
        "monthly_budget": payload["monthly_budget"],
        "horizon_days": payload["horizon_days"],
        "analysis": analysis,
        "generated_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "report_preview": agent.weekly_report(),
        "report_files": _report_files(),
    }


@app.context_processor
def inject_navigation() -> dict[str, object]:
    return {"nav_items": NAV_ITEMS}


@app.template_filter("money")
def money_filter(value: object) -> str:
    return f"PKR {float(value):,.0f}"


@app.get("/")
def index() -> str:
    return render_template(
        "index.html",
        active_page="index",
        page_title="Autonomous Growth Dashboard",
        status_label="Ready",
    )


@app.get("/connectors")
def connectors() -> str:
    context = _page_context("connectors")
    return render_template("connectors.html", connectors=CONNECTOR_CARDS, **context)


@app.get("/insights")
def insights() -> str:
    return render_template("insights.html", **_page_context("insights"))


@app.get("/campaigns")
def campaigns() -> str:
    return render_template("campaigns.html", **_page_context("campaigns"))


@app.get("/reports")
def reports_page() -> str:
    return render_template("reports.html", **_page_context("reports_page"))


@app.post("/api/analyze")
def analyze():
    agent, payload = _build_agent()
    return jsonify(
        {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "seller": payload["seller_name"],
            "platform": payload["platform"],
            "analysis": agent.analyze(),
        }
    )


@app.post("/api/report")
def report():
    agent, payload = _build_agent()
    report_text = agent.weekly_report()
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in payload["seller_name"]).strip("-")
    slug = slug or "demo-seller"
    report_path = REPORTS_DIR / f"weekly-growth-report-{slug}.md"
    report_path.write_text(report_text, encoding="utf-8")
    return jsonify(
        {
            "saved": True,
            "path": str(report_path),
            "report": report_text,
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
