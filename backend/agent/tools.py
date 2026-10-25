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

    def get_tool_definitions(self) -> str:
        return """
Available Tools:
1. `search_knowledge_base(query: str)`: Use this to search company policies, returns, warranties, shipping, or security rules.
2. `check_order_status(order_id: str)`: Use this to lookup orders (e.g., ORD-1001, ORD-1002, ORD-1003, ORD-1004) and delivery tracking.
3. `process_refund_return(order_id: str, reason: str)`: Use this to check return eligibility (30 days) and initiate returns/refunds.
4. `create_support_ticket(subject: str, description: str, priority: str)`: Use this to file a formal support inquiry for technical/product issues.
5. `escalate_to_human(reason: str, priority: str)`: Use this when the user explicitly asks for a human, representative, agent, or for unresolved conflicts.
"""
