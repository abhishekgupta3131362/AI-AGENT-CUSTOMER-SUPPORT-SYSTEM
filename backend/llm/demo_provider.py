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
            obs_match = re.search(r"observation:\s*(.*?)(?:\nThought:|\Z)", prompt, re.DOTALL | re.IGNORECASE)
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

        # 1. HOTEL AGENT INTENTS
        if any(w in t_lower for w in ["hotel", "room", "suite", "check in", "check-in", "checkout", "balcony", "resort", "king", "queen", "deluxe", "amenit", "towel", "stay"]):
            if any(w in t_lower for w in ["book", "reserve", "reservation"]):
                return (
                    f"Thought: Guest wants to make a hotel reservation. I will call book_room_reservation.\n"
                    f"Action: book_room_reservation\n"
                    f'Action Input: {{"guest_name": "Valued Guest", "room_type": "Deluxe Ocean View King", "check_in": "2026-11-01", "check_out": "2026-11-04", "special_requests": "Ocean view balcony"}}'
                )
            elif any(w in t_lower for w in ["towel", "housekeeping", "amenit", "cleaning", "pillows", "shampoo"]):
                return (
                    f"Thought: Guest is requesting housekeeping amenities. I will dispatch request_housekeeping_amenity.\n"
                    f"Action: request_housekeeping_amenity\n"
                    f'Action Input: {{"room_or_res": "Room 304", "item": "{target_text[:60].replace(chr(34), chr(39))}"}}'
                )
            else:
                return (
                    f"Thought: Guest is checking hotel room availability. I will query check_room_availability.\n"
                    f"Action: check_room_availability\n"
                    f'Action Input: {{}}'
                )

        # 2. SAAS DEVELOPER INTENTS
        if any(w in t_lower for w in ["err_", "error code", "status 429", "rate limit", "token", "oauth", "webhook", "api doc", "endpoint", "sdk"]):
            err_match = re.search(r'\b(ERR_[A-Z0-9_]+)\b', target_text, re.IGNORECASE)
            if err_match:
                code = err_match.group(1).upper()
                return (
                    f"Thought: Developer reported error code {code}. I will diagnose it using diagnose_error_code.\n"
                    f"Action: diagnose_error_code\n"
                    f'Action Input: {{"error_code": "{code}"}}'
                )
            elif any(w in t_lower for w in ["429", "rate"]):
                return (
                    f"Thought: Developer hit rate limits. I will diagnose ERR_RATE_LIMIT_429.\n"
                    f"Action: diagnose_error_code\n"
                    f'Action Input: {{"error_code": "ERR_RATE_LIMIT_429"}}'
                )
            elif any(w in t_lower for w in ["webhook", "timeout"]):
                return (
                    f"Thought: Webhook timeout diagnostic needed. I will diagnose ERR_WEBHOOK_TIMEOUT.\n"
                    f"Action: diagnose_error_code\n"
                    f'Action Input: {{"error_code": "ERR_WEBHOOK_TIMEOUT"}}'
                )
            else:
                return (
                    f"Thought: Technical documentation inquiry. I will search API reference using search_api_docs.\n"
                    f"Action: search_api_docs\n"
                    f'Action Input: {{"query": "{target_text[:60].replace(chr(34), chr(39))}"}}'
                )

        # 3. WHATSAPP BUSINESS INTENTS
        if any(w in t_lower for w in ["catalog", "whatsapp", "storefront", "products for sale", "buy headphone", "buy keyboard", "whatsapp order"]):
            if any(w in t_lower for w in ["buy", "order"]):
                return (
                    f"Thought: Customer wants to order via WhatsApp. I will invoke whatsapp_quick_order.\n"
                    f"Action: whatsapp_quick_order\n"
                    f'Action Input: {{"product_name": "{target_text[:50].replace(chr(34), chr(39))}", "customer_phone": "+91 98765-43210"}}'
                )
            else:
                return (
                    f"Thought: Customer requested WhatsApp product catalog. I will invoke get_whatsapp_catalog.\n"
                    f"Action: get_whatsapp_catalog\n"
                    f'Action Input: {{}}'
                )

        # 4. VOICE TELEPHONE CALL INTENTS
        if any(w in t_lower for w in ["call", "operator", "telephone", "phone", "transfer call"]):
            return (
                f"Thought: Telephone caller command received. I will invoke voice_call_action.\n"
                f"Action: voice_call_action\n"
                f'Action Input: {{"action": "transfer", "customer_phone": "Live Telephone Call"}}'
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
