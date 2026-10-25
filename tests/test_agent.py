import unittest
from backend.agent.tools import SupportTools
from backend.agent.support_agent import SupportAgent

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.tools = SupportTools()
        self.agent = SupportAgent()

    def test_tool_check_order_status(self):
        status = self.tools.check_order_status("ORD-1002")
        self.assertIn("In Transit", status)
        self.assertIn("UPS-9941235", status)
        self.assertIn("Bob Smith", status)

    def test_tool_search_knowledge_base(self):
        res = self.tools.search_knowledge_base("How long do I have to return an item?")
        self.assertIn("30-day", res.lower())

    def test_tool_escalate_to_human(self):
        res = self.tools.escalate_to_human(reason="Test escalation from unit test", priority="HIGH")
        self.assertIn("Tier-2", res)
        self.assertIn("ESC-", res)

    def test_agent_order_query_loop(self):
        res = self.agent.run_agent("Where is my order ORD-1002?", session_id="test_sess_01")
        self.assertIn("ORD-1002", res["response"])
        self.assertTrue(len(res["tool_calls"]) > 0)
        self.assertEqual(res["tool_calls"][0]["tool"], "check_order_status")

    def test_agent_return_policy_loop(self):
        res = self.agent.run_agent("What is your refund policy?", session_id="test_sess_02")
        self.assertTrue(len(res["response"]) > 20)

if __name__ == "__main__":
    unittest.main()
