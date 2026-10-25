import re
import time
from typing import Generator, Optional
from backend.llm.base import BaseLLMProvider

class DemoProvider(BaseLLMProvider):
    """
    Intelligent simulated agent engine for zero-configuration offline demonstration.
    Executes ReAct reasoning steps, tool activations, and natural language responses.
    """
    @property
    def provider_name(self) -> str:
        return "demo"

    def _determine_react_action(self, prompt: str) -> str:
        p_lower = prompt.lower()
        
        # Check if an observation is already provided in the prompt
        if "observation:" in p_lower and "final answer:" not in p_lower:
            # Observation was provided, synthesize final answer
            obs_match = re.search(r"observation:\s*(.*?)(?:\n\n|\Z)", prompt, re.DOTALL | re.IGNORECASE)
            obs_text = obs_match.group(1).strip() if obs_match else "Information verified."
            
            return (
                f"Thought: I have reviewed the retrieved observation and can now provide a clear, helpful response to the customer.\n"
                f"Final Answer: Thank you for your inquiry. Based on our system records:\n\n{obs_text}\n\n"
                f"Please let me know if you would like me to assist you with anything else!"
            )

        # Isolate the customer's actual utterance to prevent matching words in system instructions
        customer_matches = re.findall(r"Customer:\s*(.*?)(?:\n|$)", prompt, re.IGNORECASE)
        target_text = customer_matches[-1] if customer_matches else prompt
        t_lower = target_text.lower()

        # Detect order lookup intent (ORD-XXXX)
        order_match = re.search(r'\b(ORD-\d{4})\b', target_text, re.IGNORECASE)
        if order_match or any(w in t_lower for w in ["order status", "track my order", "where is my order", "my package"]):
            order_id = order_match.group(1).upper() if order_match else "ORD-1002"
            return (
                f"Thought: The customer is inquiring about the delivery status of order {order_id}. "
                f"I will query the order database using the check_order_status tool.\n"
                f"Action: check_order_status\n"
                f'Action Input: {{"order_id": "{order_id}"}}'
            )

        # Detect refund / return intent
        if any(w in t_lower for w in ["refund", "return item", "return my", "send back", "exchange"]):
            order_id = order_match.group(1).upper() if order_match else "ORD-1001"
            return (
                f"Thought: The user is requesting a refund or return for order {order_id}. "
                f"I will verify the 30-day return policy and process the request via the process_refund_return tool.\n"
                f"Action: process_refund_return\n"
                f'Action Input: {{"order_id": "{order_id}", "reason": "Customer return request"}}'
            )

        # Detect human escalation intent
        if any(w in t_lower for w in ["human", "representative", "speak to someone", "agent", "supervisor", "escalate", "real person"]):
            return (
                f"Thought: The customer has explicitly requested a human specialist. "
                f"According to company policy, I must promptly escalate the session.\n"
                f"Action: escalate_to_human\n"
                f'Action Input: {{"reason": "Customer requested live representative", "priority": "HIGH"}}'
            )

        # Detect ticket creation intent
        if any(w in t_lower for w in ["open ticket", "file ticket", "complaint", "issue", "bug", "damaged", "broken"]):
            return (
                f"Thought: The user is reporting an issue that requires support tracking. "
                f"I will create a support ticket.\n"
                f"Action: create_support_ticket\n"
                f'Action Input: {{"subject": "Customer Issue Report", "description": "{target_text[:120].replace(chr(34), chr(39))}", "priority": "MEDIUM"}}'
            )

        # Default: Search knowledge base
        return (
            f"Thought: The user has asked a general support question. "
            f"I will consult our company knowledge base using search_knowledge_base to retrieve accurate policy information.\n"
            f"Action: search_knowledge_base\n"
            f'Action Input: {{"query": "{target_text[:80].replace(chr(34), chr(39))}"}}'
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return self._determine_react_action(prompt)

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        full_text = self._determine_react_action(prompt)
        # Yield words in chunks to simulate token streaming
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            time.sleep(0.015)
