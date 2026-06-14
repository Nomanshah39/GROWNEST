from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / abs(previous)) * 100, 2)


def _money(value: float) -> str:
    return f"PKR {value:,.0f}"


@dataclass
class ECommerceGrowthAgent:
    sales: pd.DataFrame
    seller_name: str = "Demo Seller"
    platform: str = "Daraz"

    def analyze(self) -> dict[str, object]:
        sales = self.sales.copy()
        sales["date"] = pd.to_datetime(sales["date"])
        max_date = sales["date"].max()
        week_start = max_date - pd.Timedelta(days=6)
        previous_start = week_start - pd.Timedelta(days=7)
        this_week = sales[sales["date"] >= week_start]
        previous_week = sales[(sales["date"] >= previous_start) & (sales["date"] < week_start)]

        overview = self._overview(this_week, previous_week)
        product_table = self._product_table(sales)
        category_table = self._category_table(sales)
        channel_table = self._channel_table(sales)
        monthly_stats = self._monthly_stats(sales, max_date)
        seasonal_demand = self._seasonal_demand(sales, product_table, max_date)
        simple_insights = self._simple_insights(product_table, monthly_stats, seasonal_demand)

        return {
            "overview": overview,
            "monthlyStats": monthly_stats,
            "simpleInsights": simple_insights,
            "dailyRevenue": self._daily_revenue(sales),
            "products": product_table,
            "categories": category_table,
            "channels": channel_table,
            "customerBehavior": self._customer_behavior(sales),
            "seasonalTrends": self._seasonal_trends(sales),
            "seasonalDemand": seasonal_demand,
            "recommendations": {
                "promotions": self._promotion_recommendations(product_table),
                "bundles": self._bundle_recommendations(product_table, category_table),
                "adSpend": self._ad_spend_recommendations(channel_table, overview),
            },
            "agentSteps": [
                {"label": "Store API connected", "status": "Complete"},
                {"label": "Sales, behavior, and seasonality analyzed", "status": "Complete"},
                {"label": "Promotions, bundles, and ad strategy prepared", "status": "Complete"},
                {"label": "Weekly growth report ready", "status": "Ready"},
            ],
        }

    def weekly_report(self) -> str:
        analysis = self.analyze()
        overview = analysis["overview"]
        recommendations = analysis["recommendations"]
        top_products = analysis["products"][:5]

        lines = [
            f"# Weekly Growth Report - {self.seller_name}",
            "",
            f"Platform: {self.platform}",
            f"Generated: {date.today().isoformat()}",
            "",
            "## Simple Summary",
            "",
            f"- Revenue this week: {_money(overview['revenue'])} ({overview['revenueGrowth']}% vs previous week).",
            f"- Profit this week: {_money(overview['profit'])}.",
            f"- ROAS: {overview['roas']}x.",
            f"- Conversion rate: {overview['conversionRate']}%.",
            "",
            "## Top Products",
            "",
        ]

        for product in top_products:
            lines.append(
                f"- {product['product']}: {_money(product['revenue'])}, "
                f"{product['units']} units, {product['margin']}% margin."
            )

        lines.extend(["", "## Promotion Plan", ""])
        for item in recommendations["promotions"]:
            lines.append(f"- {item['title']}: {item['action']}")

        lines.extend(["", "## Bundle Plan", ""])
        for item in recommendations["bundles"]:
            lines.append(f"- {item['title']}: {item['action']}")

        lines.extend(["", "## Ad Spend Plan", ""])
        for item in recommendations["adSpend"]:
            lines.append(f"- {item['title']}: {item['action']}")

        return "\n".join(lines) + "\n"

    def _overview(self, this_week: pd.DataFrame, previous_week: pd.DataFrame) -> dict[str, float]:
        revenue = float(this_week["revenue"].sum())
        previous_revenue = float(previous_week["revenue"].sum())
        ad_spend = float(this_week["ad_spend"].sum())
        visitors = float(this_week["visitors"].sum())
        conversions = float(this_week["conversions"].sum())
        profit = float(this_week["profit"].sum())
        units = int(this_week["units"].sum())
        orders = max(1, int(this_week.groupby(["date", "product"]).ngroups))
        repeat_customers = float(this_week["repeat_customers"].sum())
        total_customers = float(this_week["new_customers"].sum() + repeat_customers)

        return {
            "revenue": round(revenue, 2),
            "profit": round(profit, 2),
            "units": units,
            "adSpend": round(ad_spend, 2),
            "roas": round(revenue / ad_spend, 2) if ad_spend else 0,
            "conversionRate": round((conversions / visitors) * 100, 2) if visitors else 0,
            "repeatRate": round((repeat_customers / total_customers) * 100, 2) if total_customers else 0,
            "avgOrderValue": round(revenue / orders, 2),
            "revenueGrowth": _pct_change(revenue, previous_revenue),
            "profitGrowth": _pct_change(profit, float(previous_week["profit"].sum())),
            "adSpendGrowth": _pct_change(ad_spend, float(previous_week["ad_spend"].sum())),
        }

    def _daily_revenue(self, sales: pd.DataFrame) -> list[dict[str, object]]:
        daily = (
            sales.groupby("date", as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
                adSpend=("ad_spend", "sum"),
                cost=("cost", "sum"),
                units=("units", "sum"),
            )
            .tail(28)
        )
        return [
            {
                "date": row.date.strftime("%b %d"),
                "revenue": round(float(row.revenue), 2),
                "profit": round(float(row.profit), 2),
                "adSpend": round(float(row.adSpend), 2),
                "expense": round(float(row.cost + row.adSpend), 2),
                "units": int(row.units),
            }
            for row in daily.itertuples(index=False)
        ]

    def _product_table(self, sales: pd.DataFrame) -> list[dict[str, object]]:
        max_date = sales["date"].max()
        recent_start = max_date - pd.Timedelta(days=13)
        previous_start = recent_start - pd.Timedelta(days=14)
        recent = sales[sales["date"] >= recent_start]
        previous = sales[(sales["date"] >= previous_start) & (sales["date"] < recent_start)]
        recent_units = recent.groupby("product")["units"].sum()
        previous_units = previous.groupby("product")["units"].sum()

        grouped = (
            sales.groupby(["product", "category"], as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                units=("units", "sum"),
                price=("price", "mean"),
                expense=("cost", "sum"),
                profit=("profit", "sum"),
                adSpend=("ad_spend", "sum"),
                stock=("stock_remaining", "mean"),
                rating=("rating", "mean"),
                visitors=("visitors", "sum"),
                conversions=("conversions", "sum"),
            )
            .sort_values("revenue", ascending=False)
        )
        grouped["expense"] = grouped["expense"] + grouped["adSpend"]
        grouped["margin"] = grouped.apply(lambda row: (row.profit / row.revenue) * 100 if row.revenue else 0, axis=1)
        grouped["roas"] = grouped.apply(lambda row: row.revenue / row.adSpend if row.adSpend else 0, axis=1)
        grouped["conversionRate"] = grouped.apply(
            lambda row: (row.conversions / row.visitors) * 100 if row.visitors else 0, axis=1
        )
        grouped["recentUnits"] = grouped["product"].map(recent_units).fillna(0).astype(int)
        grouped["previousUnits"] = grouped["product"].map(previous_units).fillna(0).astype(int)

        high_units = float(grouped["recentUnits"].quantile(0.66)) if not grouped.empty else 0
        medium_units = float(grouped["recentUnits"].quantile(0.33)) if not grouped.empty else 0

        products: list[dict[str, object]] = []
        for row in grouped.itertuples(index=False):
            recent_count = int(row.recentUnits)
            previous_count = int(row.previousUnits)
            trend_percent = _pct_change(recent_count, previous_count)
            demand_level = self._demand_level(recent_count, high_units, medium_units)
            stock_status = self._stock_status(float(row.stock))
            demand_trend = self._demand_trend(trend_percent)
            suggestion = self._product_suggestion(row.product, stock_status, demand_level, demand_trend)

            products.append(
                {
                "product": row.product,
                "category": row.category,
                "price": round(float(row.price), 2),
                "revenue": round(float(row.revenue), 2),
                "units": int(row.units),
                "expense": round(float(row.expense), 2),
                "profit": round(float(row.profit), 2),
                "margin": round(float(row.margin), 2),
                "roas": round(float(row.roas), 2),
                "stock": int(round(float(row.stock))),
                "stockStatus": stock_status,
                "rating": round(float(row.rating), 2),
                "conversionRate": round(float(row.conversionRate), 2),
                "recentUnits": recent_count,
                "previousUnits": previous_count,
                "trendPercent": trend_percent,
                "demandLevel": demand_level,
                "demandTrend": demand_trend,
                "suggestion": suggestion,
            }
            )
        return products

    def _category_table(self, sales: pd.DataFrame) -> list[dict[str, object]]:
        grouped = (
            sales.groupby("category", as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
                units=("units", "sum"),
                cost=("cost", "sum"),
                adSpend=("ad_spend", "sum"),
            )
            .sort_values("revenue", ascending=False)
        )
        grouped["share"] = grouped["revenue"] / grouped["revenue"].sum() * 100
        grouped["expense"] = grouped["cost"] + grouped["adSpend"]
        return [
            {
                "category": row.category,
                "revenue": round(float(row.revenue), 2),
                "expense": round(float(row.expense), 2),
                "profit": round(float(row.profit), 2),
                "units": int(row.units),
                "share": round(float(row.share), 2),
            }
            for row in grouped.itertuples(index=False)
        ]

    def _channel_table(self, sales: pd.DataFrame) -> list[dict[str, object]]:
        grouped = (
            sales.groupby("marketing_channel", as_index=False)
            .agg(revenue=("revenue", "sum"), adSpend=("ad_spend", "sum"), conversions=("conversions", "sum"))
            .sort_values("revenue", ascending=False)
        )
        grouped["roas"] = grouped.apply(lambda row: row.revenue / row.adSpend if row.adSpend else 0, axis=1)
        grouped["cpa"] = grouped.apply(lambda row: row.adSpend / row.conversions if row.conversions else 0, axis=1)
        return [
            {
                "channel": row.marketing_channel,
                "revenue": round(float(row.revenue), 2),
                "adSpend": round(float(row.adSpend), 2),
                "roas": round(float(row.roas), 2),
                "cpa": round(float(row.cpa), 2),
                "conversions": int(row.conversions),
            }
            for row in grouped.itertuples(index=False)
        ]

    def _customer_behavior(self, sales: pd.DataFrame) -> dict[str, object]:
        segment = (
            sales.groupby("customer_segment", as_index=False)
            .agg(revenue=("revenue", "sum"), customers=("conversions", "sum"))
            .sort_values("revenue", ascending=False)
        )
        total_revenue = float(segment["revenue"].sum())
        leading = segment.iloc[0]
        repeat_rate = (
            sales["repeat_customers"].sum() / max(1, sales["new_customers"].sum() + sales["repeat_customers"].sum())
        ) * 100
        return {
            "leadingSegment": str(leading.customer_segment),
            "leadingShare": round(float(leading.revenue) / total_revenue * 100, 2) if total_revenue else 0,
            "repeatRate": round(float(repeat_rate), 2),
            "segments": [
                {
                    "segment": row.customer_segment,
                    "revenue": round(float(row.revenue), 2),
                    "customers": int(row.customers),
                    "share": round(float(row.revenue) / total_revenue * 100, 2) if total_revenue else 0,
                }
                for row in segment.itertuples(index=False)
            ],
        }

    def _seasonal_trends(self, sales: pd.DataFrame) -> dict[str, object]:
        grouped = (
            sales.groupby("season_tag", as_index=False)
            .agg(revenue=("revenue", "sum"), units=("units", "sum"), profit=("profit", "sum"))
            .sort_values("revenue", ascending=False)
        )
        strongest = grouped.iloc[0]
        return {
            "currentSeason": str(sales.sort_values("date").iloc[-1].season_tag),
            "strongestSeason": str(strongest.season_tag),
            "strongestRevenue": round(float(strongest.revenue), 2),
            "trends": [
                {
                    "season": row.season_tag,
                    "revenue": round(float(row.revenue), 2),
                    "units": int(row.units),
                    "profit": round(float(row.profit), 2),
                }
                for row in grouped.itertuples(index=False)
            ],
        }

    def _monthly_stats(self, sales: pd.DataFrame, max_date: pd.Timestamp) -> dict[str, object]:
        month_start = max_date.replace(day=1).normalize()
        previous_month_start = (month_start - pd.DateOffset(months=1)).normalize()
        this_month = sales[sales["date"] >= month_start]
        previous_month = sales[(sales["date"] >= previous_month_start) & (sales["date"] < month_start)]

        revenue = float(this_month["revenue"].sum())
        expenses = float(this_month["cost"].sum() + this_month["ad_spend"].sum())
        profit = float(this_month["profit"].sum())
        units = int(this_month["units"].sum())
        previous_revenue = float(previous_month["revenue"].sum())
        previous_expenses = float(previous_month["cost"].sum() + previous_month["ad_spend"].sum())
        previous_profit = float(previous_month["profit"].sum())

        return {
            "label": max_date.strftime("%B %Y"),
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "profit": round(profit, 2),
            "units": units,
            "profitStatus": "Profit" if profit >= 0 else "Loss",
            "revenueGrowth": _pct_change(revenue, previous_revenue),
            "expenseGrowth": _pct_change(expenses, previous_expenses),
            "profitGrowth": _pct_change(profit, previous_profit),
            "incomeByCategory": self._monthly_category_values(this_month, "revenue"),
            "expenseByCategory": self._monthly_category_values(this_month, "expense"),
        }

    def _monthly_category_values(self, sales: pd.DataFrame, mode: str) -> list[dict[str, object]]:
        if sales.empty:
            return []

        monthly = sales.copy()
        monthly["expense"] = monthly["cost"] + monthly["ad_spend"]
        grouped = (
            monthly.groupby("category", as_index=False)
            .agg(value=(mode, "sum"), units=("units", "sum"))
            .sort_values("value", ascending=False)
        )
        total = float(grouped["value"].sum())

        return [
            {
                "category": row.category,
                "value": round(float(row.value), 2),
                "units": int(row.units),
                "share": round((float(row.value) / total) * 100, 2) if total else 0,
            }
            for row in grouped.itertuples(index=False)
        ]

    def _simple_insights(
        self,
        products: list[dict[str, object]],
        monthly_stats: dict[str, object],
        seasonal_demand: dict[str, object],
    ) -> list[dict[str, str]]:
        if not products:
            return []

        best_seller = max(products, key=lambda item: item["units"])
        low_stock = min(products, key=lambda item: item["stock"])
        increasing = next((item for item in products if item["demandTrend"] == "Demand increasing"), products[0])
        decreasing = next(
            (item for item in sorted(products, key=lambda item: item["trendPercent"]) if item["demandTrend"] == "Demand decreasing"),
            products[-1],
        )
        seasonal_products = seasonal_demand.get("products", [])
        seasonal_pick = seasonal_products[0] if seasonal_products else products[0]
        profit_status = str(monthly_stats["profitStatus"]).lower()

        return [
            {
                "title": "Best selling product",
                "value": str(best_seller["product"]),
                "detail": f"{best_seller['units']} units sold. This product is selling well.",
                "tone": "good",
            },
            {
                "title": "Low stock product",
                "value": str(low_stock["product"]),
                "detail": f"Only about {low_stock['stock']} left. Restock this item soon.",
                "tone": "warning",
            },
            {
                "title": "Sales this month",
                "value": _money(float(monthly_stats["revenue"])),
                "detail": f"{monthly_stats['units']} items sold in {monthly_stats['label']}.",
                "tone": "good",
            },
            {
                "title": "Expenses this month",
                "value": _money(float(monthly_stats["expenses"])),
                "detail": "This includes product cost and ad spend.",
                "tone": "neutral",
            },
            {
                "title": f"Monthly {monthly_stats['profitStatus']}",
                "value": _money(abs(float(monthly_stats["profit"]))),
                "detail": f"The store is currently in {profit_status} for this month.",
                "tone": "good" if monthly_stats["profitStatus"] == "Profit" else "warning",
            },
            {
                "title": "Demand increasing",
                "value": str(increasing["product"]),
                "detail": f"Recent sales are {increasing['trendPercent']}% higher than before.",
                "tone": "good",
            },
            {
                "title": "Demand decreasing",
                "value": str(decreasing["product"]),
                "detail": f"Recent sales are {abs(float(decreasing['trendPercent']))}% lower than before.",
                "tone": "warning",
            },
            {
                "title": "Seasonal suggestion",
                "value": str(seasonal_pick["product"]),
                "detail": str(seasonal_pick["recommendation"]),
                "tone": "good" if seasonal_pick["demandLevel"] == "High demand" else "neutral",
            },
        ]

    def _seasonal_demand(
        self,
        sales: pd.DataFrame,
        products: list[dict[str, object]],
        max_date: pd.Timestamp,
    ) -> dict[str, object]:
        current_season = str(sales.sort_values("date").iloc[-1].season_tag)
        seasonal_sales = sales[sales["season_tag"] == current_season]
        if seasonal_sales.empty:
            seasonal_sales = sales

        product_lookup = {str(item["product"]): item for item in products}
        grouped = (
            seasonal_sales.groupby(["product", "category"], as_index=False)
            .agg(units=("units", "sum"), revenue=("revenue", "sum"), stock=("stock_remaining", "mean"))
            .sort_values("units", ascending=False)
        )

        predictions: list[dict[str, object]] = []
        high_units = float(grouped["units"].quantile(0.66)) if not grouped.empty else 0
        medium_units = float(grouped["units"].quantile(0.33)) if not grouped.empty else 0

        for row in grouped.itertuples(index=False):
            product = product_lookup.get(str(row.product), {})
            recent_units = int(product.get("recentUnits", 0))
            previous_units = int(product.get("previousUnits", 0))
            trend_percent = float(product.get("trendPercent", 0))
            demand_level = self._demand_level(int(row.units), high_units, medium_units)
            trend = self._demand_trend(trend_percent)
            stock_status = self._stock_status(float(row.stock))
            should_restock = stock_status == "Low stock" and demand_level in {"High demand", "Medium demand"}
            if should_restock:
                recommendation = "Recommended to restock because demand is strong and stock is low."
            elif demand_level == "High demand":
                recommendation = "This product is selling well this season."
            elif trend == "Demand decreasing":
                recommendation = "Demand is decreasing. Avoid buying too much stock."
            else:
                recommendation = "Watch this product and restock only if sales improve."

            predictions.append(
                {
                    "product": row.product,
                    "category": row.category,
                    "season": current_season,
                    "units": int(row.units),
                    "recentUnits": recent_units,
                    "previousUnits": previous_units,
                    "revenue": round(float(row.revenue), 2),
                    "stock": int(round(float(row.stock))),
                    "stockStatus": stock_status,
                    "demandLevel": demand_level,
                    "trend": trend,
                    "trendPercent": round(trend_percent, 2),
                    "restock": "Recommended to restock" if should_restock else "No urgent restock",
                    "recommendation": recommendation,
                }
            )

        tracking_note = (
            "Demand is tracked by comparing recent sales, previous sales, current stock, "
            "and categories that usually sell more in this season."
        )

        return {
            "currentSeason": current_season,
            "asOf": max_date.strftime("%b %d, %Y"),
            "trackingNote": tracking_note,
            "products": predictions[:8],
        }

    def _stock_status(self, stock: float) -> str:
        if stock <= 35:
            return "Low stock"
        if stock >= 115:
            return "Overstocked"
        return "Healthy stock"

    def _demand_level(self, units: int, high_threshold: float, medium_threshold: float) -> str:
        if units >= high_threshold:
            return "High demand"
        if units >= medium_threshold:
            return "Medium demand"
        return "Low demand"

    def _demand_trend(self, trend_percent: float) -> str:
        if trend_percent >= 8:
            return "Demand increasing"
        if trend_percent <= -8:
            return "Demand decreasing"
        return "Demand steady"

    def _product_suggestion(self, product: object, stock_status: str, demand_level: str, demand_trend: str) -> str:
        if stock_status == "Low stock" and demand_level in {"High demand", "Medium demand"}:
            return f"Restock {product} soon."
        if demand_level == "High demand" and demand_trend == "Demand increasing":
            return "This product is selling well."
        if demand_trend == "Demand decreasing":
            return "Demand is slowing down. Do not overstock."
        if stock_status == "Overstocked":
            return "Try a small discount to move extra stock."
        return "Keep watching sales this week."

    def _promotion_recommendations(self, products: list[dict[str, object]]) -> list[dict[str, str]]:
        high_stock = sorted(products, key=lambda item: (item["stock"], item["margin"]), reverse=True)[:2]
        high_roas = sorted(products, key=lambda item: item["roas"], reverse=True)[:1]
        low_conversion = sorted(products, key=lambda item: item["conversionRate"])[:1]

        recommendations: list[dict[str, str]] = []
        for item in high_stock:
            recommendations.append(
                {
                    "title": f"{item['product']} stock push",
                    "impact": "Inventory",
                    "action": f"Run a 10-12% weekend offer while keeping margin near {item['margin']}%.",
                }
            )
        for item in high_roas:
            recommendations.append(
                {
                    "title": f"{item['product']} scale campaign",
                    "impact": "Revenue",
                    "action": f"Increase visibility because ROAS is {item['roas']}x and conversion is {item['conversionRate']}%.",
                }
            )
        for item in low_conversion:
            recommendations.append(
                {
                    "title": f"{item['product']} checkout incentive",
                    "impact": "Conversion",
                    "action": "Test free delivery or a cart coupon before increasing ad spend.",
                }
            )
        return recommendations[:4]

    def _bundle_recommendations(
        self,
        products: list[dict[str, object]],
        categories: list[dict[str, object]],
    ) -> list[dict[str, str]]:
        top = products[:4]
        if len(top) < 4:
            return []
        strongest_category = categories[0]["category"]
        return [
            {
                "title": f"{top[0]['product']} + {top[2]['product']}",
                "impact": "Average order value",
                "action": "Create a 2-item bundle at 6-8% off to lift weekly basket size.",
            },
            {
                "title": f"{top[1]['product']} starter pack",
                "impact": "Repeat customers",
                "action": f"Pair with a lower-priced add-on from {strongest_category} for loyal customers.",
            },
            {
                "title": f"{top[3]['product']} clearance combo",
                "impact": "Cash flow",
                "action": "Bundle with a fast seller to move slow inventory without a deep single-product discount.",
            },
        ]

    def _ad_spend_recommendations(
        self,
        channels: list[dict[str, object]],
        overview: dict[str, float],
    ) -> list[dict[str, str]]:
        if not channels:
            return []
        best = max(channels, key=lambda item: item["roas"])
        worst = min(channels, key=lambda item: item["roas"])
        move_budget = max(2500, overview["adSpend"] * 0.12)
        return [
            {
                "title": f"Move budget to {best['channel']}",
                "impact": "ROAS",
                "action": f"Shift {_money(move_budget)} from {worst['channel']} to {best['channel']} for the next 7 days.",
            },
            {
                "title": "Retarget recent visitors",
                "impact": "Conversion",
                "action": "Use cart-view and product-view audiences with a capped frequency of 3 impressions per day.",
            },
            {
                "title": "Protect organic winners",
                "impact": "Profit",
                "action": "Keep profitable organic products visible in store collections before buying more traffic.",
            },
        ]
