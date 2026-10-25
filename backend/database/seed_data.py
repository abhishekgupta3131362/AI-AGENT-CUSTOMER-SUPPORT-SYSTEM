import json
from datetime import datetime
from backend.database.db import init_db, execute_db, query_db
from backend.rag.default_knowledge import DEFAULT_ARTICLES
from backend.rag.vector_store import VectorStore

def seed_database():
    """Seeds the database with realistic customers, orders, support tickets, and knowledge articles."""
    init_db()
    
    # 1. Seed Customers if empty
    existing_customers = query_db("SELECT COUNT(*) as cnt FROM customers", one=True)
    if existing_customers and existing_customers["cnt"] == 0:
        customers = [
            ("CUST-101", "Alice Johnson", "alice@example.com", "+1-555-0101", "VIP"),
            ("CUST-102", "Bob Smith", "bob@example.com", "+1-555-0102", "Standard"),
            ("CUST-103", "Charlie Davis", "charlie@example.com", "+1-555-0103", "Standard"),
            ("CUST-104", "Diana Prince", "diana@example.com", "+1-555-0104", "VIP"),
        ]
        for c in customers:
            execute_db(
                "INSERT INTO customers (id, name, email, phone, tier) VALUES (?, ?, ?, ?, ?)",
                c
            )
        print(f"[Seed] Added {len(customers)} customers.")

    # 2. Seed Orders if empty
    existing_orders = query_db("SELECT COUNT(*) as cnt FROM orders", one=True)
    if existing_orders and existing_orders["cnt"] == 0:
        orders = [
            (
                "ORD-1001",
                "CUST-101",
                json.dumps([{"item": "Wireless Noise-Canceling Headphones", "qty": 1, "price": 149.99}]),
                149.99,
                "USD",
                "Delivered",
                "FedEx",
                "FDX-7749102",
                "2026-10-20",
                "2026-10-15",
                1
            ),
            (
                "ORD-1002",
                "CUST-102",
                json.dumps([{"item": "Ergonomic Mechanical Keyboard", "qty": 1, "price": 89.50}]),
                89.50,
                "USD",
                "In Transit",
                "UPS",
                "UPS-9941235",
                "2026-10-26 (Tomorrow)",
                "2026-10-22",
                1
            ),
            (
                "ORD-1003",
                "CUST-103",
                json.dumps([{"item": "Ultra HD 4K Streaming Webcam", "qty": 1, "price": 119.00}]),
                119.00,
                "USD",
                "Delivered",
                "DHL",
                "DHL-4401829",
                "2026-08-15",
                "2026-08-10",
                0 # Exceeded 30-day return policy
            ),
            (
                "ORD-1004",
                "CUST-104",
                json.dumps([
                    {"item": "Smart Fitness Watch", "qty": 1, "price": 199.99},
                    {"item": "Silicone Sport Band", "qty": 1, "price": 24.99}
                ]),
                224.98,
                "USD",
                "Processing",
                None,
                None,
                "2026-10-29",
                "2026-10-25",
                1
            )
        ]
        for o in orders:
            execute_db(
                """
                INSERT INTO orders (id, customer_id, items, total_amount, currency, status, shipping_carrier, tracking_number, estimated_delivery, order_date, is_refundable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                o
            )
        print(f"[Seed] Added {len(orders)} mock orders.")

    # 3. Seed Support Tickets if empty
    existing_tickets = query_db("SELECT COUNT(*) as cnt FROM tickets", one=True)
    if existing_tickets and existing_tickets["cnt"] == 0:
        tickets = [
            (
                "TCK-101",
                "CUST-103",
                "charlie@example.com",
                "Webcam microphone audio distortion",
                "Customer reported crackling noises during video conference calls.",
                "MEDIUM",
                "OPEN",
                "AI Agent",
                None
            ),
            (
                "TCK-102",
                "CUST-102",
                "bob@example.com",
                "Address modification for in-transit order ORD-1002",
                "Customer requested to verify if package can be held at local UPS depot.",
                "HIGH",
                "IN_PROGRESS",
                "Human Specialist (Sarah M.)",
                "Contacted courier dispatch to place destination hold."
            ),
            (
                "TCK-103",
                "CUST-101",
                "alice@example.com",
                "VIP loyalty discount not applied at checkout",
                "VIP member requested review of 15% discount code error.",
                "LOW",
                "RESOLVED",
                "AI Agent",
                "Applied $22.50 store credit directly to customer account balance."
            )
        ]
        for t in tickets:
            execute_db(
                """
                INSERT INTO tickets (id, customer_id, customer_email, subject, description, priority, status, assigned_agent, resolution_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                t
            )
        print(f"[Seed] Added {len(tickets)} support tickets.")

    # 4. Seed Knowledge Base Vector Store
    vector_store = VectorStore()
    existing_docs = query_db("SELECT COUNT(*) as cnt FROM knowledge_documents", one=True)
    if existing_docs and existing_docs["cnt"] == 0:
        for article in DEFAULT_ARTICLES:
            vector_store.add_document(
                title=article["title"],
                category=article["category"],
                content=article["content"],
                doc_id=article["id"]
            )
        print(f"[Seed] Indexed {len(DEFAULT_ARTICLES)} knowledge base articles into vector store.")

if __name__ == "__main__":
    seed_database()
    print("Database initialization and seeding completed successfully!")
