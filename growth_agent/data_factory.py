from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


CATALOGS = {
    "Daraz": [
        ("Electronics", "Wireless Earbuds", 5200, 3100, 1.15),
        ("Home", "Air Fryer", 23500, 16900, 0.9),
        ("Fashion", "Lawn Suit", 6800, 4100, 1.35),
        ("Beauty", "Skincare Kit", 4200, 2300, 1.05),
        ("Accessories", "Smart Watch Strap", 1600, 720, 1.25),
        ("Kids", "School Backpack", 3600, 2100, 0.85),
        ("Kitchen", "Spice Organizer", 1900, 950, 0.95),
        ("Fitness", "Steel Water Bottle", 2200, 1050, 1.1),
    ],
    "Shopify": [
        ("Beauty", "Vitamin C Serum", 3900, 1750, 1.25),
        ("Apparel", "Oversized Hoodie", 8200, 4700, 0.95),
        ("Accessories", "Minimal Wallet", 3400, 1600, 1.1),
        ("Home", "Scented Candle Set", 5200, 2600, 0.85),
        ("Fitness", "Resistance Band Kit", 4600, 2100, 1.05),
        ("Stationery", "Planner Bundle", 2900, 1100, 1.3),
        ("Skincare", "Hydrating Cleanser", 3300, 1500, 0.9),
        ("Gifts", "Premium Gift Box", 7400, 3800, 0.8),
    ],
    "Foodpanda Vendors": [
        ("Meals", "Chicken Biryani Deal", 650, 380, 1.3),
        ("Meals", "Zinger Combo", 850, 510, 1.15),
        ("Desserts", "Molten Lava Cake", 590, 260, 0.95),
        ("Drinks", "Mint Margarita", 320, 120, 1.25),
        ("Platters", "Family BBQ Platter", 3200, 2050, 0.8),
        ("Breakfast", "Paratha Roll", 360, 170, 1.05),
        ("Fast Food", "Loaded Fries", 530, 260, 1.1),
        ("Deals", "Student Lunch Box", 480, 240, 1.2),
    ],
    "Custom API / CSV": [
        ("Electronics", "Bluetooth Speaker", 7800, 4400, 0.9),
        ("Fashion", "Denim Jacket", 9200, 5100, 0.8),
        ("Beauty", "Hair Care Set", 5600, 2800, 1.05),
        ("Home", "LED Desk Lamp", 4300, 2300, 1.15),
        ("Sports", "Yoga Mat", 3100, 1350, 1.2),
        ("Grocery", "Organic Honey", 2600, 1250, 1.0),
        ("Kids", "Learning Blocks", 3900, 1900, 0.95),
        ("Pets", "Cat Food Pack", 4800, 2850, 0.85),
    ],
}

MARKETING_CHANNELS = ("Search Ads", "Social Ads", "Retargeting", "Organic")
CUSTOMER_SEGMENTS = ("New", "Repeat", "Loyal")


def generate_sample_sales(
    platform: str = "Daraz",
    days: int = 84,
    monthly_budget: float = 250000,
    seed: int = 42,
) -> pd.DataFrame:
    """Create deterministic synthetic seller data for a dashboard demo."""
    rng = np.random.default_rng(seed + sum(ord(ch) for ch in platform))
    catalog = CATALOGS.get(platform, CATALOGS["Custom API / CSV"])
    end = date.today()
    start = end - timedelta(days=days - 1)
    records: list[dict[str, object]] = []
    daily_budget = monthly_budget / 30

    for day_index in range(days):
        current = start + timedelta(days=day_index)
        weekday = current.weekday()
        weekend_boost = 1.18 if weekday in (4, 5, 6) else 0.94
        payday_boost = 1.22 if current.day in range(1, 8) else 1.0
        mid_month_dip = 0.88 if current.day in range(15, 22) else 1.0
        season_tag = _season_tag(current)

        for idx, (category, product, price, cost, popularity) in enumerate(catalog):
            trend = 1 + (day_index / max(days - 1, 1)) * rng.normal(0.14, 0.05)
            seasonal = _seasonal_multiplier(category, season_tag)
            demand = max(2, popularity * 12 * weekend_boost * payday_boost * mid_month_dip * seasonal * trend)
            units = int(max(0, rng.poisson(demand)))
            discount_rate = float(np.clip(rng.normal(0.08 if units < demand else 0.05, 0.025), 0.0, 0.22))
            visitors = int(max(units + 15, rng.normal(units * rng.uniform(9, 15), 35)))
            conversions = units
            channel = MARKETING_CHANNELS[(idx + day_index) % len(MARKETING_CHANNELS)]
            ad_multiplier = 1.35 if channel in ("Search Ads", "Social Ads") else 0.72
            ad_spend = float(max(0, rng.normal(daily_budget / len(catalog) * ad_multiplier, 320)))
            revenue = float(units * price * (1 - discount_rate))
            gross_cost = float(units * cost)
            profit = revenue - gross_cost - ad_spend
            repeat_rate = float(np.clip(rng.normal(0.34 + idx * 0.018, 0.07), 0.09, 0.78))
            new_customers = int(round(units * (1 - repeat_rate)))
            repeat_customers = max(0, units - new_customers)
            stock_remaining = int(max(0, rng.normal(140 - units * 2.4 + idx * 12, 16)))
            rating = float(np.clip(rng.normal(4.35 + popularity / 20, 0.18), 3.6, 4.95))

            records.append(
                {
                    "date": pd.Timestamp(current),
                    "platform": platform,
                    "category": category,
                    "product": product,
                    "units": units,
                    "price": price,
                    "revenue": round(revenue, 2),
                    "cost": round(gross_cost, 2),
                    "profit": round(profit, 2),
                    "discount_rate": round(discount_rate, 4),
                    "ad_spend": round(ad_spend, 2),
                    "visitors": visitors,
                    "conversions": conversions,
                    "repeat_customer_rate": round(repeat_rate, 4),
                    "new_customers": new_customers,
                    "repeat_customers": repeat_customers,
                    "rating": round(rating, 2),
                    "stock_remaining": stock_remaining,
                    "marketing_channel": channel,
                    "customer_segment": CUSTOMER_SEGMENTS[(idx + weekday) % len(CUSTOMER_SEGMENTS)],
                    "season_tag": season_tag,
                }
            )

    return pd.DataFrame.from_records(records)


def _season_tag(day: date) -> str:
    if day.month in (3, 4):
        return "Ramadan/Eid"
    if day.month in (6, 7, 8):
        return "Summer"
    if day.month in (10, 11):
        return "Sale Season"
    if day.month == 12:
        return "Year End"
    return "Regular"


def _seasonal_multiplier(category: str, tag: str) -> float:
    category = category.lower()
    if tag == "Ramadan/Eid" and category in {"fashion", "beauty", "meals", "deals", "desserts"}:
        return 1.28
    if tag == "Summer" and category in {"drinks", "fitness", "beauty", "skincare", "grocery"}:
        return 1.18
    if tag == "Sale Season":
        return 1.16
    if tag == "Year End" and category in {"gifts", "home", "electronics"}:
        return 1.2
    return 1.0

