import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from backend.database.db import query_db, execute_db
from backend.rag.vector_store import VectorStore

class SupportTools:
    def __init__(self):
        self.vector_store = VectorStore()

    def search_knowledge_base(self, query: str) -> str:
        """
        Searches the company knowledge base for policy information, warranties, shipping, and FAQs.
        """
        results = self.vector_store.search(query, top_k=2, min_similarity=0.10)
        if not results:
            return "No directly matching knowledge base articles found. Proceed with standard customer service protocol."
        
        snippets = []
        for r in results:
            snippets.append(
                f"[Doc: {r['title']} (Category: {r['category']}, Relevance: {int(r['similarity']*100)}%)]\n"
                f"{r['content']}"
            )
        return "\n\n".join(snippets)

    def check_order_status(self, order_id: str) -> str:
        """
        Retrieves real-time status, tracking numbers, and delivery timeline for an order ID (e.g., ORD-1002).
        """
        order_clean = order_id.strip().upper()
        row = query_db(
            """
            SELECT o.*, c.name as customer_name, c.email as customer_email, c.tier as customer_tier
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
            """,
            (order_clean,),
            one=True
        )
        
        if not row:
            # Fallback search by tracking number
            row = query_db(
                """
                SELECT o.*, c.name as customer_name, c.email as customer_email, c.tier as customer_tier
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.tracking_number = ?
                """,
                (order_clean,),
                one=True
            )

        if not row:
            return f"Order '{order_clean}' was not found in our order records. Please confirm the order number."

        try:
            items = json.loads(row["items"])
            items_desc = ", ".join([f"{it.get('qty', 1)}x {it.get('item', 'Item')} (${it.get('price', 0.0)})" for it in items])
        except Exception:
            items_desc = row["items"]

        tracking_info = f"Carrier: {row['shipping_carrier']}, Tracking #: {row['tracking_number']}" if row['tracking_number'] else "Tracking not yet assigned."
        
        return (
            f"Order Details for {row['id']}:\n"
            f"- Customer: {row['customer_name']} ({row['customer_tier']} Tier)\n"
            f"- Status: {row['status']}\n"
            f"- Items: {items_desc}\n"
            f"- Total: ${row['total_amount']:.2f} {row['currency']}\n"
            f"- Order Date: {row['order_date']}\n"
            f"- Estimated Delivery: {row['estimated_delivery'] or 'TBD'}\n"
            f"- Shipping: {tracking_info}\n"
            f"- 30-Day Return Window Active: {'Yes (Eligible)' if row['is_refundable'] else 'No (Expired - 1-Year Warranty Applies)'}"
        )

    def process_refund_return(self, order_id: str, reason: str = "Customer requested return") -> str:
        """
        Validates return eligibility (30-day window) and creates a return authorization or refund record.
        """
        order_clean = order_id.strip().upper()
        order = query_db("SELECT * FROM orders WHERE id = ?", (order_clean,), one=True)
        
        if not order:
            return f"Order {order_clean} not found. Cannot process refund."

        if not order["is_refundable"] or order["status"] == "Cancelled":
            if not order["is_refundable"]:
                return (
                    f"Return Request Denied: Order {order_clean} exceeds the 30-calendar-day return window. "
                    f"However, if the item has a technical defect, the customer can submit a 1-Year Manufacturer Warranty claim."
                )
            return f"Order {order_clean} is already marked as {order['status']}."

        # Process return: Update order status to 'Return Initiated'
        execute_db("UPDATE orders SET status = 'Return Initiated' WHERE id = ?", (order_clean,))

        # Create linked support ticket
        ticket_id = f"RET-{uuid.uuid4().hex[:6].upper()}"
        execute_db(
            """
            INSERT INTO tickets (id, customer_id, customer_email, subject, description, priority, status, assigned_agent, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                order["customer_id"],
                "support@apextech.com",
                f"Return Authorization for {order_clean}",
                f"Return processed for order {order_clean}. Reason: {reason}",
                "MEDIUM",
                "IN_PROGRESS",
                "Automated Returns Bot",
                f"Return merchandise authorization created. Prepaid label generated."
            )
        )

        return (
            f"Return Authorization Approved for {order_clean}!\n"
            f"- Return Reference ID: {ticket_id}\n"
            f"- Refund Amount: ${order['total_amount']:.2f} {order['currency']}\n"
            f"- Instructions: A prepaid shipping return label has been emailed to the customer. "
            f"Once our warehouse receives and inspects the item, the refund will be credited back in 3-5 business days."
        )

    def create_support_ticket(self, subject: str, description: str, priority: str = "MEDIUM", customer_email: Optional[str] = None, customer_id: Optional[str] = None) -> str:
        """
        Creates a new support ticket in the database.
        """
        ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
        priority_clean = priority.upper() if priority.upper() in ["LOW", "MEDIUM", "HIGH", "URGENT"] else "MEDIUM"
        
        execute_db(
            """
            INSERT INTO tickets (id, customer_id, customer_email, subject, description, priority, status, assigned_agent)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 'AI Agent')
            """,
            (ticket_id, customer_id, customer_email or "guest@customer.com", subject, description, priority_clean)
        )

        return (
            f"Support ticket successfully opened:\n"
            f"- Ticket ID: {ticket_id}\n"
            f"- Subject: {subject}\n"
            f"- Priority: {priority_clean}\n"
            f"- Status: OPEN (Our team has been notified)"
        )

    def escalate_to_human(self, reason: str = "Customer requested live representative", priority: str = "HIGH", customer_id: Optional[str] = None) -> str:
        """
        Escalates the current issue to a human support specialist in the CRM dashboard.
        """
        ticket_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
        execute_db(
            """
            INSERT INTO tickets (id, customer_id, customer_email, subject, description, priority, status, assigned_agent)
            VALUES (?, ?, 'customer@support.com', 'Human Agent Escalation Request', ?, ?, 'ESCALATED', 'Human Specialist Queue')
            """,
            (ticket_id, customer_id, f"Escalation Trigger: {reason}", priority.upper())
        )

        return (
            f"Session successfully escalated to Human Support:\n"
            f"- Escalation Ticket ID: {ticket_id}\n"
            f"- Priority: {priority.upper()}\n"
            f"- Queue Status: Assigned to Tier-2 Support Specialists\n"
            f"- Expected Response Time: Under 15 minutes during business hours (8 AM - 8 PM EST)."
        )

    # ==========================================
    # 2. HOTEL & HOSPITALITY AGENT TOOLS
    # ==========================================

    def check_room_availability(self, room_type: Optional[str] = None) -> str:
        """Checks available hotel rooms, pricing per night, and amenities."""
        if room_type:
            rows = query_db("SELECT * FROM hotel_rooms WHERE room_type LIKE ?", (f"%{room_type}%",))
        else:
            rows = query_db("SELECT * FROM hotel_rooms WHERE available_count > 0")

        if not rows:
            return "No rooms matching that category are currently available."

        output = ["🏨 Grand Apex Resort & Hotel - Live Room Availability:"]
        for r in rows:
            output.append(
                f"- **{r['room_type']}** (${r['price_per_night']:.2f}/night, Max {r['max_guests']} Guests)\n"
                f"  Available: {r['available_count']} rooms\n"
                f"  Amenities: {r['amenities']}\n"
                f"  Overview: {r['description']}"
            )
        return "\n\n".join(output)

    def book_room_reservation(self, guest_name: str, room_type: str, check_in: str, check_out: str, special_requests: Optional[str] = None) -> str:
        """Books a hotel reservation and returns a confirmation code."""
        room = query_db("SELECT * FROM hotel_rooms WHERE room_type LIKE ?", (f"%{room_type}%",), one=True)
        if not room:
            # Fallback to any room
            room = query_db("SELECT * FROM hotel_rooms LIMIT 1", one=True)

        if not room:
            return f"Sorry, '{room_type}' is fully booked for those dates. Please select another room category."

        # Keep room count available (replenish if reached 0)
        curr_avail = room.get("available_count", 5)
        new_avail = max(1, curr_avail - 1) if curr_avail > 1 else 4
        execute_db("UPDATE hotel_rooms SET available_count = ? WHERE id = ?", (new_avail, room["id"]))

        res_id = f"RES-{uuid.uuid4().hex[:6].upper()}"
        execute_db(
            """
            INSERT INTO hotel_reservations (id, guest_name, room_id, check_in, check_out, special_requests)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (res_id, guest_name, room["id"], check_in, check_out, special_requests or "Standard stay")
        )

        return (
            f"🎉 Hotel Reservation Confirmed!\n"
            f"- Booking Code: {res_id}\n"
            f"- Guest: {guest_name}\n"
            f"- Room: {room['room_type']} (${room['price_per_night']:.2f}/night)\n"
            f"- Dates: {check_in} to {check_out}\n"
            f"- Special Requests: {special_requests or 'None'}\n"
            f"- Check-In Time: 3:00 PM (Complimentary luggage storage available earlier)"
        )

    def request_housekeeping_amenity(self, room_or_res: str, item: str) -> str:
        """Dispatches a housekeeping or room service request."""
        req_id = f"HK-{uuid.uuid4().hex[:5].upper()}"
        return (
            f"Housekeeping & Concierge Request #{req_id} Dispatched:\n"
            f"- Target: Room/Reservation {room_or_res}\n"
            f"- Requested Service: {item}\n"
            f"- Delivery SLA: Staff will deliver to your door within 10-15 minutes."
        )

    # ==========================================
    # 3. SAAS DEVELOPER & TECHNICAL AGENT TOOLS
    # ==========================================

    def diagnose_error_code(self, error_code: str) -> str:
        """Looks up a developer API error code, root cause, code sample, and resolution."""
        code_clean = error_code.strip().upper()
        row = query_db("SELECT * FROM saas_error_docs WHERE code = ? OR code LIKE ?", (code_clean, f"%{code_clean}%"), one=True)
        if not row:
            return f"Error code '{code_clean}' not found in standard API documentation. Please check spelling or submit a developer ticket."

        return (
            f"Developer Diagnostic Report for `{row['code']}`:\n"
            f"- Title: {row['title']}\n"
            f"- Severity: {row['severity']}\n"
            f"- Root Cause: {row['cause']}\n"
            f"- Solution: {row['solution']}\n"
            f"- Code Sample:\n```javascript\n{row['code_sample']}\n```"
        )

    def search_api_docs(self, query: str) -> str:
        """Searches technical API reference documentation."""
        q = query.lower()
        if "rate" in q or "limit" in q or "429" in q:
            return self.diagnose_error_code("ERR_RATE_LIMIT_429")
        elif "token" in q or "auth" in q or "jwt" in q or "oauth" in q:
            return self.diagnose_error_code("ERR_AUTH_EXPIRED")
        elif "webhook" in q or "timeout" in q or "event" in q:
            return self.diagnose_error_code("ERR_WEBHOOK_TIMEOUT")
        elif "validation" in q or "schema" in q or "payload" in q:
            return self.diagnose_error_code("ERR_SCHEMA_VALIDATION")
        else:
            return (
                "ApexTech Developer API v2.4 Reference:\n"
                "- Base URL: `https://api.apextech.com/v2`\n"
                "- Authentication: Bearer Token in `Authorization` header\n"
                "- Rate Limit: 120 req/min for Standard Tier, 10,000 req/min for Enterprise\n"
                "- Webhooks: HMAC SHA-256 signed events with 5s timeout\n"
                "- SDKs: Python (`pip install apextech-sdk`), Node.js (`npm i @apextech/client`)"
            )

    # ==========================================
    # 4. WHATSAPP BUSINESS AGENT TOOLS
    # ==========================================

    def get_whatsapp_catalog(self) -> str:
        """Retrieves verified WhatsApp Product Catalog with quick checkout actions."""
        return (
            "📱 ApexTech WhatsApp Business Storefront:\n\n"
            "1. 🎧 Wireless ANC Pro Headphones - ₹12,499 [In Stock]\n"
            "   High-res audio, 40h battery, Active Noise Cancellation\n\n"
            "2. ⌨️ Ergonomic RGB Mechanical Keyboard - ₹6,999 [In Stock]\n"
            "   Hot-swappable tactile switches, Bluetooth & 2.4GHz wireless\n\n"
            "3. 📹 Ultra HD 4K Streaming Cam - ₹9,499 [In Stock]\n"
            "   Dual stereo mic, AI auto-framing, HDR low-light sensor\n\n"
            "4. ⌚ Smart Fitness GPS Watch - ₹14,999 [In Stock]\n"
            "   AMOLED display, SpO2 & Heart Rate monitor, 14-day battery\n\n"
            "💬 Reply with 'Buy [Item Name]' or tap an item to place a quick WhatsApp order!"
        )

    def whatsapp_quick_order(self, product_name: str, customer_phone: str = "+91 98765-43210") -> str:
        """Creates a pending WhatsApp order draft."""
        order_ref = f"WA-{uuid.uuid4().hex[:6].upper()}"
        return (
            f"✅ WhatsApp Order Draft Generated!\n"
            f"- Order Ref: {order_ref}\n"
            f"- Item: {product_name}\n"
            f"- Customer Phone: {customer_phone}\n"
            f"- Payment Mode: UPI / Cash on Delivery (COD) / Net Banking\n"
            f"- Delivery: Express Delivery in 2-3 days via Delhivery/BlueDart.\n"
            f"Payment link sent to your WhatsApp number. Tap link to complete payment."
        )

    # ==========================================
    # 5. VOICE TELEPHONE AGENT TOOLS
    # ==========================================

    def voice_call_action(self, action: str, customer_phone: str = "Spoken Call") -> str:
        """Handles telephone voice operator tasks and transfer."""
        act = action.lower()
        if "transfer" in act or "human" in act or "operator" in act:
            call_id = f"CALL-XFER-{uuid.uuid4().hex[:4].upper()}"
            return f"Voice Call Transfer Initiated (Ref: {call_id}). Connecting caller to Senior Support Supervisor. Hold music started."
        elif "order" in act:
            return self.check_order_status("ORD-1002")
        else:
            return "Telephone Voice Assistant: I have transcribed and confirmed your verbal request. How else may I assist you over this call?"

    def get_tool_definitions(self, agent_type: str = "ecommerce") -> str:
        agent_type = (agent_type or "ecommerce").lower()

        if agent_type == "hotel":
            return """
Available Hotel Tools:
1. `check_room_availability(room_type: str)`: Check available room types, rates per night, amenities, and photos.
2. `book_room_reservation(guest_name: str, room_type: str, check_in: str, check_out: str, special_requests: str)`: Confirm a hotel reservation with booking code.
3. `request_housekeeping_amenity(room_or_res: str, item: str)`: Dispatch towels, room service, late checkout, or maintenance.
4. `escalate_to_human(reason: str, priority: str)`: Connect to the front desk manager.
"""
        elif agent_type == "saas":
            return """
Available SaaS Technical Tools:
1. `diagnose_error_code(error_code: str)`: Lookup developer error codes (e.g., ERR_AUTH_EXPIRED, ERR_RATE_LIMIT_429, ERR_WEBHOOK_TIMEOUT, ERR_SCHEMA_VALIDATION) for root cause and code fixes.
2. `search_api_docs(query: str)`: Search API endpoints, authentication guides, webhook timeouts, and SDK syntax.
3. `create_support_ticket(subject: str, description: str, priority: str)`: File a GitHub/Jira engineering bug ticket.
4. `escalate_to_human(reason: str, priority: str)`: Escalate to a tier-3 technical solutions architect.
"""
        elif agent_type == "whatsapp":
            return """
Available WhatsApp Tools:
1. `get_whatsapp_catalog()`: Share current product catalog with pricing and item specs.
2. `whatsapp_quick_order(product_name: str, customer_phone: str)`: Generate a 1-click WhatsApp order draft with UPI payment link.
3. `check_order_status(order_id: str)`: Track delivery status for orders like ORD-1002.
4. `escalate_to_human(reason: str, priority: str)`: Route chat to a human WhatsApp sales executive.
"""
        elif agent_type == "voice":
            return """
Available Voice Agent Tools:
1. `voice_call_action(action: str, customer_phone: str)`: Handle telephone call commands, verbal order checks, or hold music.
2. `check_order_status(order_id: str)`: Lookup delivery status for verbal order inquiry.
3. `escalate_to_human(reason: str, priority: str)`: Transfer telephone call to live call center supervisor.
"""
        else: # ecommerce
            return """
Available E-commerce Tools:
1. `search_knowledge_base(query: str)`: Search company return policies, warranty rules, shipping, and FAQs.
2. `check_order_status(order_id: str)`: Lookup orders (ORD-1001, ORD-1002, ORD-1003, ORD-1004) and delivery tracking.
3. `process_refund_return(order_id: str, reason: str)`: Check return eligibility (30 days) and initiate refund RMA.
4. `create_support_ticket(subject: str, description: str, priority: str)`: Open formal support ticket.
5. `escalate_to_human(reason: str, priority: str)`: Escalate to live tier-2 representative.
"""
