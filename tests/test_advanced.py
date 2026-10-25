import unittest
import io
import json
from backend.agent.sentiment import SentimentAnalyzer
from backend.app import create_app

class TestAdvancedFeatures(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.analyzer = SentimentAnalyzer()

    def test_sentiment_positive(self):
        res = self.analyzer.analyze("Thank you so much! This was super helpful and solved my problem quickly.")
        self.assertEqual(res["label"], "Positive")
        self.assertGreater(res["score"], 0.2)
        self.assertFalse(res["is_frustrated"])

    def test_sentiment_frustrated_and_urgent(self):
        res = self.analyzer.analyze("THIS IS RIDICULOUS YOUR SERVICE SUCKS I WANT A REFUND RIGHT NOW OR I SUE!")
        self.assertEqual(res["label"], "Frustrated")
        self.assertTrue(res["is_frustrated"])
        self.assertTrue(res["is_urgent"])
        self.assertLess(res["score"], -0.3)

    def test_csat_submission(self):
        payload = {"session_id": "test_adv_sess", "rating": 5, "feedback": "Amazing agent!"}
        res = self.client.post("/api/chat/csat", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

    def test_analytics_endpoint(self):
        res = self.client.get("/api/analytics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("avg_csat", data)
        self.assertIn("resolution_rate", data)
        self.assertIn("sentiment_counts", data)
        self.assertIn("tool_counts", data)

    def test_human_takeover_and_reply(self):
        sess_id = "test_takeover_sess"
        # Takeover
        res_takeover = self.client.post("/api/chat/takeover", json={"session_id": sess_id, "takeover": True, "agent_name": "Test Agent"})
        self.assertEqual(res_takeover.status_code, 200)
        self.assertEqual(res_takeover.get_json()["is_human_takeover"], 1)

        # Human reply
        res_reply = self.client.post("/api/chat/human-reply", json={"session_id": sess_id, "message": "Hello from human support!", "agent_name": "Test Agent"})
        self.assertEqual(res_reply.status_code, 200)
        self.assertEqual(res_reply.get_json()["sender"], "Test Agent")

    def test_knowledge_file_upload(self):
        file_content = b"Special Express Delivery Guidelines\nExpress deliveries require signature on receipt."
        data = {
            "file": (io.BytesIO(file_content), "special_delivery.txt"),
            "title": "Special Delivery Guidelines",
            "category": "Shipping"
        }
        res = self.client.post("/api/knowledge/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.get_json()["success"])

    def test_ai_ticket_summary(self):
        res = self.client.post("/api/tickets/TCK-101/ai-summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("ai_summary", data)

if __name__ == "__main__":
    unittest.main()
