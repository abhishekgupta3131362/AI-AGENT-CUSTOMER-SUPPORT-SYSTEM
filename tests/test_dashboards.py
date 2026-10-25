import unittest
import json
from backend.app import create_app
from backend.database.db import init_db
from backend.database.seed_data import seed_database

class DashboardTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_ecommerce_dashboard(self):
        res = self.client.get("/api/dashboard/ecommerce")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("carrier_breakdown", data)
        self.assertIn("orders", data)
        self.assertGreater(data["metrics"]["total_orders"], 0)
        self.assertGreater(data["metrics"]["total_revenue"], 0)

    def test_hotel_dashboard(self):
        res = self.client.get("/api/dashboard/hotel")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("rooms", data)
        self.assertIn("reservations", data)
        self.assertIn("occupancy_rate", data["metrics"])
        self.assertGreater(len(data["rooms"]), 0)

    def test_voice_dashboard(self):
        res = self.client.get("/api/dashboard/voice")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("operators", data)
        self.assertIn("call_records", data)
        self.assertIn("total_calls_today", data["metrics"])
        self.assertGreater(len(data["call_records"]), 0)

    def test_whatsapp_dashboard(self):
        res = self.client.get("/api/dashboard/whatsapp")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("leads", data)
        self.assertIn("catalog", data)
        self.assertIn("delivery_rate", data["metrics"])
        self.assertGreater(len(data["leads"]), 0)

    def test_saas_dashboard(self):
        res = self.client.get("/api/dashboard/saas")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("endpoint_health", data)
        self.assertIn("error_distribution", data)
        self.assertIn("developer_tickets", data)
        self.assertIn("uptime", data["metrics"])
        self.assertGreater(len(data["endpoint_health"]), 0)

if __name__ == "__main__":
    unittest.main()
