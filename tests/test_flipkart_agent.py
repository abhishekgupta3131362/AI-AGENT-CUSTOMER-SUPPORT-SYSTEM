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

    def test_flipkart_order_sattus_typo_and_platform_isolation(self):
        """When user asks with typos like 'flipkart order sattus', agent stays 100% on Flipkart and NEVER mentions Amazon."""
        res = self.client.post("/api/chat", json={
            "message": "flipkart order sattus",
            "session_id": "test_flipkart_conv_5",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        self.assertIn("Flipkart", response_text)
        self.assertIn("Ekart", response_text)
        # Strict isolation check: NEVER mention Amazon when asking about Flipkart!
        self.assertNotIn("Amazon", response_text)
        self.assertNotIn("ApexTech", response_text)

    def test_arbitrary_flipkart_order_dynamic_carrier_tracking(self):
        """Any valid Flipkart OD... order ID is tracked via live Ekart simulation dynamically."""
        res = self.client.post("/api/chat", json={
            "message": "Track my Flipkart parcel OD881920194821",
            "session_id": "test_flipkart_conv_6",
            "agent_type": "ecommerce"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        response_text = data["response"]
        self.assertIn("OD881920194821", response_text)
        self.assertIn("Ekart", response_text)
        self.assertNotIn("Amazon", response_text)

    def test_ecommerce_api_endpoints(self):
        """Tests /api/ecommerce/track and /api/ecommerce/platforms REST routes."""
        res1 = self.client.get("/api/ecommerce/platforms")
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertTrue(data1["success"])
        self.assertIn("flipkart", data1["platforms"])

        res2 = self.client.get("/api/ecommerce/track?id=OD409218392100")
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.data)
        self.assertTrue(data2["success"])
        self.assertEqual(data2["platform"], "Flipkart")
        self.assertIn("Nothing Phone", data2["formatted_text"])

if __name__ == "__main__":
    unittest.main()
