import unittest
import json
from backend.app import create_app
from backend.database.db import init_db
from backend.database.seed_data import seed_database

class AgentforceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_get_agentforce_topics(self):
        res = self.client.get("/api/agentforce/topics")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("topics", data)
        self.assertGreater(len(data["topics"]), 0)
        topic = data["topics"][0]
        self.assertIn("id", topic)
        self.assertIn("name", topic)
        self.assertIn("actions", topic)

    def test_trust_layer_endpoints(self):
        # 1. GET
        res = self.client.get("/api/agentforce/trust-layer")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("config", data)
        self.assertTrue(data["config"]["pii_masking"])

        # 2. POST Update
        res_post = self.client.post("/api/agentforce/trust-layer", json={
            "pii_masking": False,
            "confidence_threshold": 90
        })
        self.assertEqual(res_post.status_code, 200)
        updated = json.loads(res_post.data)
        self.assertFalse(updated["config"]["pii_masking"])
        self.assertEqual(updated["config"]["confidence_threshold"], 90)

    def test_roi_calculator(self):
        res = self.client.post("/api/agentforce/roi-calculator", json={
            "monthly_tickets": 20000,
            "human_cost_per_ticket": 12.0,
            "deflection_rate": 80.0
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["monthly_tickets"], 20000)
        self.assertGreater(data["monthly_savings"], 0)
        self.assertGreater(data["annual_savings"], 0)
        self.assertGreater(data["roi_percent"], 0)

    def test_chat_returns_atlas_reasoning_trail(self):
        res = self.client.post("/api/chat", json={
            "message": "Where is order ORD-1002?",
            "session_id": "test_sf_atlas_1",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("response", data)
        self.assertIn("atlas_reasoning_trail", data)
        trail = data["atlas_reasoning_trail"]
        self.assertIn("engine", trail)
        self.assertIn("grounded_in", trail)
        self.assertIn("trust_layer", trail)
        self.assertIn("steps", trail)

if __name__ == "__main__":
    unittest.main()
