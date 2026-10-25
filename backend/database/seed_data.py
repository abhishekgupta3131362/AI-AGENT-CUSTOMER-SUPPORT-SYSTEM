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

    # 2b. Seed / Ensure Flipkart and Multi-Platform Orders Exist
    multi_platform_orders = [
        (
            "OD409218392100",
            "CUST-101",
            json.dumps([{"item": "Nothing Phone (2a) 5G (Black, 128 GB)", "qty": 1, "price": 23999.0}]),
            23999.0,
            "INR",
            "Out for Delivery",
            "Ekart Logistics",
            "FMPC0948218",
            "Today by 7:00 PM (Delivery OTP: 4921)",
            "2026-10-23",
            1,
            "Flipkart",
            "Ekart Delivery Hub - Sector 62 Noida (Out for delivery by Ramesh Kumar +91-98112-44910)",
            "Prepaid via UPI PhonePe"
        ),
        (
            "OD123984729100",
            "CUST-102",
            json.dumps([{"item": "Noise ColorFit Pro 5 Smartwatch (Jet Black)", "qty": 1, "price": 3499.0}]),
            3499.0,
            "INR",
            "Delivered",
            "Ekart Logistics",
            "FMPC0112948",
            "2026-10-21 (Delivered)",
            "2026-10-18",
            1,
            "Flipkart",
            "Delivered at Customer Address Bengaluru (7 Days Replacement Window Active)",
            "Cash on Delivery (₹3,499 paid)"
        ),
        (
            "OD991823746100",
            "CUST-103",
            json.dumps([{"item": "Puma Smashic Casual Sneakers (White & Blue, Size 9)", "qty": 1, "price": 1899.0}]),
            1899.0,
            "INR",
            "In Transit",
            "Ekart Logistics",
            "FMPC0773912",
            "Tomorrow by 2:00 PM",
            "2026-10-24",
            1,
            "Flipkart",
            "Ekart Mother Hub Bilaspur (In Transit to Delivery Station)",
            "Flipkart Pay Later"
        ),
        (
            "171-8839201-9921",
            "CUST-104",
            json.dumps([{"item": "Echo Dot (5th Gen) Smart Speaker with Alexa", "qty": 1, "price": 4499.0}]),
            4499.0,
            "INR",
            "In Transit",
            "Amazon Transportation Services (ATS)",
            "ATS-IN-994821",
            "Tomorrow by 11:00 AM",
            "2026-10-24",
            1,
            "Amazon",
            "Amazon Fulfilment Centre DEL4",
            "Amazon Pay ICICI Credit Card"
        )
    ]
    for mpo in multi_platform_orders:
        execute_db(
            """
            INSERT OR REPLACE INTO orders 
            (id, customer_id, items, total_amount, currency, status, shipping_carrier, tracking_number, estimated_delivery, order_date, is_refundable, platform, courier_hub, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            mpo
        )

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

    # 5. Seed Hotel Rooms if empty
    existing_rooms = query_db("SELECT COUNT(*) as cnt FROM hotel_rooms", one=True)
    if existing_rooms and existing_rooms["cnt"] == 0:
        rooms = [
            (
                "ROOM-101",
                "Deluxe Ocean View King",
                189.00,
                2,
                4,
                "King Bed, Private Balcony, High-Speed WiFi, Mini-Bar, Oceanfront view",
                "Luxurious oceanfront room featuring panoramic sunrise views and plush bedding."
            ),
            (
                "ROOM-102",
                "Executive Family Suite",
                279.00,
                4,
                2,
                "2 Queen Beds, Separate Living Room, Nespresso Machine, Whirlpool Tub, City Skyline",
                "Spacious multi-room suite ideal for families or extended business stays."
            ),
            (
                "ROOM-103",
                "Standard Cozy Queen",
                119.00,
                2,
                7,
                "Queen Bed, Ergonomic Work Desk, Rain Shower, Free Breakfast Buffet included",
                "Quiet, comfortable room designed for solo travelers and couples."
            )
        ]
        for r in rooms:
            execute_db(
                "INSERT INTO hotel_rooms (id, room_type, price_per_night, max_guests, available_count, amenities, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                r
            )
        print(f"[Seed] Added {len(rooms)} hotel rooms.")

        # Seed sample reservation
        execute_db(
            "INSERT INTO hotel_reservations (id, guest_name, room_id, check_in, check_out, status, special_requests) VALUES ('RES-701', 'John Doe', 'ROOM-101', '2026-11-01', '2026-11-05', 'CONFIRMED', 'Late check-in requested at 9:00 PM')",
        )
        print("[Seed] Added sample hotel reservation RES-701.")

    # 6. Seed SaaS Error Troubleshooting Docs
    existing_saas = query_db("SELECT COUNT(*) as cnt FROM saas_error_docs", one=True)
    if existing_saas and existing_saas["cnt"] == 0:
        saas_errors = [
            (
                "ERR_AUTH_EXPIRED",
                "OAuth 2.0 Access Token Expired",
                "HIGH",
                "Bearer access token has exceeded its 3600-second lifespan.",
                "Call POST /api/v2/oauth/token with grant_type='refresh_token' to exchange for a new token without forcing re-login.",
                "const newToken = await authClient.refreshToken(storedRefreshToken);"
            ),
            (
                "ERR_RATE_LIMIT_429",
                "HTTP 429 Too Many Requests Quota Exceeded",
                "MEDIUM",
                "Client sent more than 120 requests/minute on the Standard Tier API key.",
                "Implement exponential backoff jitter or batch queries via the /api/v2/batch endpoint.",
                "time.sleep(int(response.headers.get('Retry-After', 2)))"
            ),
            (
                "ERR_WEBHOOK_TIMEOUT",
                "Webhook Delivery Acknowledgment Timeout (>5000ms)",
                "HIGH",
                "Your destination endpoint failed to return HTTP 200 within the 5.0s webhook SLA.",
                "Acknowledge webhook deliveries instantly with HTTP 200, and offload business logic to an asynchronous background worker queue.",
                "app.post('/webhook', (req, res) => { workerQueue.add(req.body); res.sendStatus(200); });"
            ),
            (
                "ERR_SCHEMA_VALIDATION",
                "Malformed JSON Body or Missing Required Fields",
                "LOW",
                "Request payload failed Pydantic schema validation. Missing 'id' or 'amount'.",
                "Verify your request payload matches the OpenAPI 3.1 specification before sending.",
                "curl -X POST /api/v2/charges -H 'Content-Type: application/json' -d '{\"customer_id\": \"c_101\", \"amount\": 49.99}'"
            )
        ]
        for se in saas_errors:
            execute_db(
                "INSERT INTO saas_error_docs (code, title, severity, cause, solution, code_sample) VALUES (?, ?, ?, ?, ?, ?)",
                se
            )
        print(f"[Seed] Added {len(saas_errors)} SaaS developer error guides.")

    # 4. Seed Knowledge Base Vector Store
    vector_store = VectorStore()
    added_docs = 0
    for article in DEFAULT_ARTICLES:
        existing = query_db("SELECT id FROM knowledge_documents WHERE id = ?", (article["id"],), one=True)
        if not existing:
            vector_store.add_document(
                title=article["title"],
                category=article["category"],
                content=article["content"],
                doc_id=article["id"]
            )
            added_docs += 1
    if added_docs > 0:
        print(f"[Seed] Indexed {added_docs} new knowledge base articles into vector store.")

if __name__ == "__main__":
    seed_database()
    print("Database initialization and seeding completed successfully!")
