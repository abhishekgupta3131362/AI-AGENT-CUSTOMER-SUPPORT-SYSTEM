import unittest
import json
from backend.app import create_app

class EvaluationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_evaluation_benchmarks_endpoint(self):
        """Tests that /api/evaluation/benchmarks returns metadata, KPIs, baseline comparisons, and objectives."""
        res = self.client.get("/api/evaluation/benchmarks")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        
        self.assertIn("kpis", data)
        self.assertIn("baseline_comparison", data)
        self.assertIn("objective_evaluation", data)
        self.assertIn("test_suite_summary", data)
        self.assertIn("areas_for_improvement", data)

        self.assertGreater(data["kpis"]["autonomous_resolution_rate"], 85.0)
        self.assertEqual(len(data["baseline_comparison"]), 7)
        self.assertEqual(len(data["objective_evaluation"]), 5)

    def test_live_benchmark_trials_runner(self):
        """Tests that /api/evaluation/run-live executes live inference probes across all 5 agent domains."""
        res = self.client.post("/api/evaluation/run-live")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertTrue(data["success"])
        self.assertEqual(data["total_trials"], 5)
        self.assertTrue(data["all_passed"])
        self.assertGreater(len(data["trials"]), 0)

        # Check Flipkart trial
        fk_trial = next(t for t in data["trials"] if "Flipkart" in t["domain"])
        self.assertIn("OD409218392100", fk_trial["query"])
        self.assertEqual(fk_trial["status"], "PASS")

if __name__ == "__main__":
    unittest.main()
