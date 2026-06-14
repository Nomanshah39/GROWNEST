import unittest

from growth_agent.agent import ECommerceGrowthAgent
from growth_agent.data_factory import generate_sample_sales


class AgentAnalysisTest(unittest.TestCase):
    def setUp(self):
        sales = generate_sample_sales(platform="Daraz", days=28, monthly_budget=200000)
        self.agent = ECommerceGrowthAgent(sales, "Test Seller", "Daraz")

    def test_analysis_contains_recommendations(self):
        analysis = self.agent.analyze()

        self.assertIn("overview", analysis)
        self.assertGreater(analysis["overview"]["revenue"], 0)
        self.assertGreater(len(analysis["recommendations"]["promotions"]), 0)
        self.assertGreater(len(analysis["recommendations"]["adSpend"]), 0)

    def test_weekly_report_mentions_seller_and_platform(self):
        report = self.agent.weekly_report()

        self.assertIn("Test Seller", report)
        self.assertIn("Daraz", report)
        self.assertIn("Promotion Plan", report)


if __name__ == "__main__":
    unittest.main()

