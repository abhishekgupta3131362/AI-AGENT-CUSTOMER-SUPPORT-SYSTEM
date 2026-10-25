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
                f"Thought: I have reviewed the retrieved observation and will present the exact live order and tracking details to the customer step-by-step.\n"
                f"Final Answer: {obs_text}"
            )

        # Isolate the customer's actual utterance to prevent matching words in system instructions
        customer_matches = re.findall(r"Customer:\s*(.*?)(?:\n|$)", prompt, re.IGNORECASE)
        target_text = customer_matches[-1] if customer_matches else prompt
        t_lower = target_text.lower()

        # Multi-Platform Order ID Regex: Flipkart (OD..., FPK-...), Amazon (171-...), ApexTech (ORD-...)
        order_match = re.search(r'\b(OD\d{6,16}|FPK-\d{4,8}|\d{3}-\d{7}-\d{4,7}|ORD-\d{4})\b', target_text, re.IGNORECASE)

        # 1. FLIPKART INTEGRATION & LINKING INTENTS
        if any(w in t_lower for w in ["flipkart se link", "link flipkart", "flipcart se link", "link flipcart", "flipkart connect", "connect flipkart"]):
            return (
                f"Thought: Customer wants to link or verify Flipkart account integration.\n"
                f"Final Answer: ✅ **Flipkart & Ekart Logistics Integration Connected!**\n\n"
                f"Aapka Flipkart account successfully link ho gaya hai. Ab aap kisi bhi Flipkart order ka real-time Ekart tracking status, transit location, delivery OTP aur 7-day replacement window yahan live check kar sakte hain.\n\n"
                f"Kripya apna **Flipkart Order ID** share karein (Jaise sample orders: `OD409218392100` for Nothing Phone 2a, `OD123984729100` for Noise Smartwatch, ya `OD991823746100` for Puma Shoes)."
            )

        # 2. SPECIFIC ORDER ID PROVIDED BY CUSTOMER -> EXECUTE TOOL
        if order_match:
            order_id = order_match.group(1).upper()
            if any(w in t_lower for w in ["refund", "return", "wapas", "replacement", "exchange"]):
                return (
                    f"Thought: The user is requesting a refund or return for order {order_id}. "
                    f"I will verify the 30-day/7-day return policy and process the request via the process_refund_return tool.\n"
                    f"Action: process_refund_return\n"
                    f'Action Input: {{"order_id": "{order_id}", "reason": "Customer return request"}}'
                )
            else:
                return (
                    f"Thought: Customer has provided Order ID {order_id}. I will query the live orders database using check_order_status.\n"
                    f"Action: check_order_status\n"
                    f'Action Input: {{"order_id": "{order_id}"}}'
                )

        # 3. DELIVERY BOY / COURIER CONTACT INTENT
        if any(w in t_lower for w in ["delivery boy", "delivery agent", "courier contact", "driver number", "delivery partner number", "agent number"]):
            return (
                f"Thought: Customer is requesting the delivery executive contact number.\n"
                f"Final Answer: 🚚 **Ekart Logistics Delivery Partner Details:**\n\n"
                f"• Delivery Executive: **Ramesh Kumar**\n"
                f"• Phone Number: **+91 98112-44910**\n"
                f"• Assigned Hub: Ekart Hub Sector 62, Noida\n"
                f"• Status: Out for delivery on route\n"
                f"• Security OTP: **4921** (Kripya parcel receive karte samay delivery hero ko OTP verify karayein)\n\n"
                f"Kya aapko delivery boy ko urgent delivery call lagwana hai?"
            )

        # 4. INVOICE / RECEIPT INTENT (WITHOUT ID)
        if any(w in t_lower for w in ["invoice", "bill", "tax invoice", "receipt", "slip"]):
            return (
                f"Thought: Customer is requesting an invoice but did not provide the order number.\n"
                f"Final Answer: 📄 **Official GST Tax Invoice Download**\n\n"
                f"Invoice download karne ke liye, kripya apna **Order ID** batayein (Jaise Flipkart ka `OD409218392100` ya Amazon ka `171-8839201-9921`).\n\n"
                f"ID provide karte hi main instant PDF download link generate kar doonga!"
            )

        # 5. ORDER STATUS INQUIRY WITHOUT ORDER ID -> STEP-BY-STEP DIALOGUE
        if any(w in t_lower for w in ["order status", "track my order", "where is my order", "my package", "mera order", "order track", "kahan hai", "kab aayega", "delivery status", "order check"]):
            if "flipkart" in t_lower or "flipcart" in t_lower:
                return (
                    f"Thought: Customer wants to track a Flipkart order but has not provided the Order ID yet. I must ask them for their Flipkart Order ID step-by-step.\n"
                    f"Final Answer: Namaste! Zaroor, main aapka **Flipkart order** Ekart Logistics live tracking ke zariye trace kar sakta hoon. 📦\n\n"
                    f"Kripya apna **Flipkart Order ID** share karein:\n"
                    f"• Jaise: `OD409218392100` (Nothing Phone 2a)\n"
                    f"• Jaise: `OD123984729100` (Noise Smartwatch)\n"
                    f"• Jaise: `OD991823746100` (Puma Shoes)\n\n"
                    f"Aap apna Order ID type karein, main turant live location, expected delivery date aur OTP details screen par show kar doonga!"
                )
            elif "amazon" in t_lower:
                return (
                    f"Thought: Customer wants to track an Amazon order but has not provided the Order ID yet.\n"
                    f"Final Answer: Zaroor! Amazon order track karne ke liye, kripya apna **Amazon Order ID** share karein (Jaise sample: `171-8839201-9921`). Main Amazon ATS logistics se live status nikaal doonga!"
                )
            else:
                return (
                    f"Thought: Customer is inquiring about order tracking but has not specified an Order ID or platform. I must interact step-by-step and ask them which platform they ordered from and their Order ID.\n"
                    f"Final Answer: Zaroor! Main aapke order ki live tracking aur delivery status nikaal sakta hoon. Kripya step-by-step confirm karein:\n\n"
                    f"1️⃣ **Aap kis platform ka order track karna chahte hain?**\n"
                    f"   • 🛍️ **Flipkart** (e.g. Order ID: `OD409218392100`)\n"
                    f"   • 📦 **Amazon** (e.g. Order ID: `171-8839201-9921`)\n"
                    f"   • 🛒 **ApexTech Store** (e.g. Order ID: `ORD-1002`)\n\n"
                    f"2️⃣ **Aapka Order ID kya hai?**\n\n"
                    f"Aap Order ID enter karein, main turant Ekart / courier live tracking se status fetch karke batata hoon!"
                )

        # 6. REFUND / RETURN INTENT WITHOUT ORDER ID
        if any(w in t_lower for w in ["refund", "return item", "return my", "send back", "exchange", "wapas karna"]):
            return (
                f"Thought: Customer is asking about returns or refunds without providing an Order ID.\n"
                f"Final Answer: Zaroor! Main aapka return ya refund request initiate kar sakta hoon. Kripya batayein:\n\n"
                f"1️⃣ **Aapka Order ID kya hai?** (Jaise Flipkart ka `OD123984729100` ya `ORD-1001`)\n"
                f"2️⃣ **Return ya replacement ka reason kya hai?** (Jaise: Size issue, defective product, ya package damage)\n\n"
                f"Order ID share karte hi main return eligibility verify karke instant RMA pickup schedule kar doonga!"
            )

        # 7. HUMAN ESCALATION INTENT
        if any(w in t_lower for w in ["human", "representative", "speak to someone", "agent", "supervisor", "escalate", "real person", "insan se baat", "manager"]):
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
