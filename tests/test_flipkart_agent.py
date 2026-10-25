import unittest
import json
from backend.app import create_app
from backend.database.db import init_db
from backend.database.seed_data import seed_database

class FlipkartAgentTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_step_by_step_no_order_id(self):
        """When user asks for order status without ID, agent must ask for platform and ID step-by-step."""
        res = self.client.post("/api/chat", json={
            "message": "Mera order status dekhna hai",
            "session_id": "test_flipkart_conv_1",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        
        # Verify it does NOT blindly return ORD-1002 order details
        self.assertNotIn("Order Details for ORD-1002", response_text)
        self.assertNotIn("Ergonomic Mechanical Keyboard", response_text)
        # Verify it asks for platform and Order ID step-by-step
        self.assertTrue("Flipkart" in response_text)
        self.assertTrue("Order ID" in response_text)

    def test_flipkart_link_intent(self):
        """When user asks to link with Flipkart, agent confirms integration and requests Flipkart Order ID."""
        res = self.client.post("/api/chat", json={
            "message": "Flipkart se link karo ise",
            "session_id": "test_flipkart_conv_2",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        self.assertIn("Flipkart", response_text)
        self.assertIn("Ekart", response_text)
        self.assertIn("OD409218392100", response_text)

    def test_flipkart_order_status_tracking(self):
        """When user provides Flipkart Order ID, agent executes tool and returns live Ekart Logistics details."""
        res = self.client.post("/api/chat", json={
            "message": "Where is my Flipkart order OD409218392100?",
            "session_id": "test_flipkart_conv_3",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        self.assertIn("OD409218392100", response_text)
        self.assertIn("Nothing Phone", response_text)
        self.assertIn("Ekart", response_text)
        self.assertIn("Out for Delivery", response_text)
        self.assertIn("Next Steps", response_text)

    def test_delivery_boy_contact(self):
        """When user asks for delivery boy number, agent returns the Ekart courier details."""
        res = self.client.post("/api/chat", json={
            "message": "Ekart delivery boy ka contact number do",
            "session_id": "test_flipkart_conv_4",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        self.assertIn("Ramesh Kumar", response_text)
        self.assertIn("98112", response_text)
        self.assertIn("4921", response_text) # Security OTP

if __name__ == "__main__":
    unittest.main()
