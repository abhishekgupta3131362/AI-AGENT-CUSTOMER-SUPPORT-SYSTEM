import unittest
import json
from backend.app import create_app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_chat_endpoint(self):
        payload = {"message": "Where is order ORD-1002?", "session_id": "test_api_sess"}
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        self.assertIn("ORD-1002", data["response"])

    def test_get_orders(self):
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(len(data["orders"]) >= 4)

    def test_get_and_create_ticket(self):
        # Create
        new_ticket = {
            "subject": "Unit Test Issue",
            "description": "Created from test suite",
            "customer_email": "tester@example.com",
            "priority": "LOW"
        }
        res_create = self.client.post("/api/tickets", json=new_ticket)
        self.assertEqual(res_create.status_code, 201)
        created_data = res_create.get_json()
        ticket_id = created_data["ticket"]["id"]

        # List
        res_list = self.client.get("/api/tickets")
        self.assertEqual(res_list.status_code, 200)
        tickets = res_list.get_json()["tickets"]
        self.assertTrue(any(t["id"] == ticket_id for t in tickets))

        # Update
        res_patch = self.client.patch(f"/api/tickets/{ticket_id}", json={"status": "RESOLVED"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.get_json()["ticket"]["status"], "RESOLVED")

    def test_knowledge_search(self):
        payload = {"query": "warranty claims", "top_k": 2}
        res = self.client.post("/api/knowledge/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue("results" in data)

    def test_settings_get_and_update(self):
        res_get = self.client.get("/api/settings")
        self.assertEqual(res_get.status_code, 200)
        settings = res_get.get_json()
        self.assertIn("active_provider", settings)

        # Switch provider
        res_post = self.client.post("/api/settings", json={"provider": "demo"})
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(res_post.get_json()["active_provider"], "demo")

if __name__ == "__main__":
    unittest.main()
