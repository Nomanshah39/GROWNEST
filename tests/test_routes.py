import unittest
from pathlib import Path

from app import REPORTS_DIR, app


class PageRoutesTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_pages_render(self):
        cases = [
            ("/", "Autonomous Growth Dashboard"),
            ("/connectors", "Connectors"),
            ("/insights", "Insights"),
            ("/campaigns", "Campaigns"),
            ("/reports", "Reports"),
        ]

        for route, expected in cases:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected.encode(), response.data)

    def test_report_api_returns_markdown(self):
        response = self.client.post(
            "/api/report",
            json={"sellerName": "Route Seller", "platform": "Shopify", "monthlyBudget": 150000, "horizonDays": 28},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["saved"])
        self.assertIn("Route Seller", payload["report"])
        self.assertIn("Promotion Plan", payload["report"])

        generated_path = Path(payload["path"])
        if generated_path.parent == REPORTS_DIR and generated_path.name.startswith("weekly-growth-report-route-seller"):
            generated_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
