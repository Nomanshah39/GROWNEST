# Smart E-Commerce Growth Agent

A local FYP prototype that simulates an autonomous growth agent for online sellers on Daraz, Shopify, Foodpanda-style stores, or a custom API/CSV source.

The app generates realistic sample sales data, analyzes product sales, customer behavior, seasonal trends, ad spend, and stock movement, then recommends promotions, bundles, ad budget changes, and a weekly seller report.

## Run

```powershell
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Pages

- `/` - autonomous growth dashboard
- `/connectors` - store API and data pipeline view
- `/insights` - product, customer, category, and seasonality analysis
- `/campaigns` - promotions, bundles, and ad spend planner
- `/reports` - weekly seller report preview and saved report list

## What It Includes

- Store connection simulation
- Sales and profit trend analysis
- Product, category, and marketing-channel diagnostics
- Promotion, bundle, and ad spend strategy recommendations
- Weekly growth report generation
- Local report save flow in `reports/`

## Project Structure

```text
app.py
growth_agent/
  agent.py
  data_factory.py
static/
  css/styles.css
  js/app.js
templates/
  index.html
tests/
  test_agent.py
```
