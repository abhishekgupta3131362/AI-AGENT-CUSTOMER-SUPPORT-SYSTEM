import unittest
from backend.agent.support_agent import SupportAgent

class TestAllAgentTypes(unittest.TestCase):
    def setUp(self):
        self.agent = SupportAgent()

    def test_ecommerce_agent(self):
        res = self.agent.run_agent("Where is my order ORD-1002?", session_id="test_ecom", agent_type="ecommerce")
        self.assertIn("ORD-1002", res["response"])
        self.assertIn("UPS", res["response"])

    def test_hotel_agent_availability(self):
        res = self.agent.run_agent("What rooms are available at the hotel?", session_id="test_hotel_1", agent_type="hotel")
        self.assertIn("Ocean View King", res["response"])
        self.assertIn("Grand Apex", res["response"])

    def test_hotel_agent_booking(self):
        res = self.agent.run_agent("I want to book the Deluxe Ocean View King for Nov 1 to Nov 4", session_id="test_hotel_2", agent_type="hotel")
        self.assertIn("RES-", res["response"])
        self.assertIn("Confirmed", res["response"])

    def test_saas_agent_diagnostics(self):
        res = self.agent.run_agent("How do I fix ERR_AUTH_EXPIRED?", session_id="test_saas_1", agent_type="saas")
        self.assertIn("ERR_AUTH_EXPIRED", res["response"])
        self.assertIn("OAuth", res["response"])

    def test_whatsapp_agent_catalog(self):
        res = self.agent.run_agent("Show me your product catalog on WhatsApp", session_id="test_wa_1", agent_type="whatsapp")
        self.assertIn("Headphones", res["response"])
        self.assertIn("₹", res["response"])

    def test_voice_agent_operator(self):
        res = self.agent.run_agent("Can I check my order ORD-1002 over the phone?", session_id="test_voice_1", agent_type="voice")
        self.assertIn("ORD-1002", res["response"])

if __name__ == "__main__":
    unittest.main()
