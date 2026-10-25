import json
import uuid
from flask import Blueprint, jsonify, request
from backend.database.db import query_db, execute_db

dashboard_bp = Blueprint("dashboards", __name__)

# ==========================================
# 1. E-COMMERCE OPERATIONAL DASHBOARD
# ==========================================
@dashboard_bp.route("/api/dashboard/ecommerce", methods=["GET"])
def get_ecommerce_dashboard():
    orders = query_db(
        """
        SELECT o.*, c.name as customer_name, c.email as customer_email, c.tier as customer_tier
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC
        """
    )
    for o in orders:
        try:
            o["items_parsed"] = json.loads(o["items"])
        except Exception:
            o["items_parsed"] = o["items"]

    total_revenue = sum(o["total_amount"] for o in orders)
    returns_count = sum(1 for o in orders if o["status"] == "Return Initiated")
    in_transit_count = sum(1 for o in orders if o["status"] == "In Transit")
    delivered_count = sum(1 for o in orders if o["status"] == "Delivered")

    carriers = {"Ekart Logistics": 0, "FedEx": 0, "UPS": 0, "DHL": 0, "Other": 0}
    platforms = {"Flipkart": 0, "Amazon": 0, "ApexTech": 0}
    for o in orders:
        c = o.get("shipping_carrier")
        if c in carriers:
            carriers[c] += 1
        elif c:
            carriers["Other"] += 1

        p = o.get("platform", "ApexTech")
        if p in platforms:
            platforms[p] += 1
        elif p:
            platforms["ApexTech"] += 1

    return jsonify({
        "metrics": {
            "total_orders": len(orders),
            "total_revenue": round(total_revenue, 2),
            "returns_count": returns_count,
            "in_transit_count": in_transit_count,
            "delivered_count": delivered_count
        },
        "carrier_breakdown": carriers,
        "platform_breakdown": platforms,
        "orders": orders
    })

# ==========================================
# 2. HOTEL & HOSPITALITY DASHBOARD
# ==========================================
@dashboard_bp.route("/api/dashboard/hotel", methods=["GET"])
def get_hotel_dashboard():
    rooms = query_db("SELECT * FROM hotel_rooms")
    reservations = query_db(
        """
        SELECT res.*, r.room_type, r.price_per_night
        FROM hotel_reservations res
        JOIN hotel_rooms r ON res.room_id = r.id
        ORDER BY res.created_at DESC
        """
    )

    total_capacity = sum(r["available_count"] + 1 for r in rooms) # Total rooms
    available_rooms = sum(r["available_count"] for r in rooms)
    occupied_rooms = total_capacity - available_rooms
    occupancy_rate = round((occupied_rooms / total_capacity * 100), 1) if total_capacity > 0 else 75.0

    return jsonify({
        "metrics": {
            "total_rooms": total_capacity,
            "occupied_rooms": occupied_rooms,
            "available_rooms": available_rooms,
            "occupancy_rate": occupancy_rate,
            "active_reservations": len(reservations)
        },
        "rooms": rooms,
        "reservations": reservations
    })

# ==========================================
# 3. AI VOICE TELEPHONY CALL CENTER DASHBOARD
# ==========================================
@dashboard_bp.route("/api/dashboard/voice", methods=["GET"])
def get_voice_dashboard():
    # Pre-seeded Call Detail Records (CDR)
    call_records = [
        {"id": "CDR-901", "caller": "+1-555-0199", "duration": "02:14", "intent": "Track Order ORD-1002", "sentiment": "Neutral", "status": "COMPLETED", "operator": "ApexVoice AI"},
        {"id": "CDR-902", "caller": "+1-555-0144", "duration": "04:30", "intent": "Escalated - Speak with Human", "sentiment": "Frustrated", "status": "TRANSFERRED", "operator": "Sarah M. (Live)"},
        {"id": "CDR-903", "caller": "+1-555-0182", "duration": "01:45", "intent": "Return Inquiry ORD-1001", "sentiment": "Positive", "status": "COMPLETED", "operator": "ApexVoice AI"},
        {"id": "CDR-904", "caller": "+1-555-0115", "duration": "00:58", "intent": "Store Hours & Locations", "sentiment": "Positive", "status": "COMPLETED", "operator": "ApexVoice AI"}
    ]

    return jsonify({
        "metrics": {
            "total_calls_today": 48,
            "avg_handle_time": "2m 18s",
            "first_call_resolution": "88.5%",
            "transferred_calls": 4,
            "active_telephony_lines": 12
        },
        "operators": [
            {"name": "ApexVoice Bot #1", "status": "In Call (00:45)", "channel": "Line 1"},
            {"name": "ApexVoice Bot #2", "status": "Available", "channel": "Line 2"},
            {"name": "Sarah M. (Supervisor)", "status": "Available", "channel": "Line 3"},
            {"name": "Alex K. (Tier-2)", "status": "Wrap-Up", "channel": "Line 4"}
        ],
        "call_records": call_records
    })

# ==========================================
# 4. WHATSAPP BUSINESS OPERATIONS DASHBOARD
# ==========================================
@dashboard_bp.route("/api/dashboard/whatsapp", methods=["GET"])
def get_whatsapp_dashboard():
    leads = [
        {"id": "WA-LEAD-101", "phone": "+91 98765-43210", "name": "Rahul Verma", "stage": "UPI Payment Link Sent", "item": "Wireless ANC Pro Headphones", "amount": "₹12,499", "updated": "10 mins ago"},
        {"id": "WA-LEAD-102", "phone": "+91 98112-33445", "name": "Priya Sharma", "stage": "Catalog Shared", "item": "Ergonomic Mechanical Keyboard", "amount": "₹6,999", "updated": "25 mins ago"},
        {"id": "WA-LEAD-103", "phone": "+91 97234-88990", "name": "Amit Patel", "stage": "Order Confirmed", "item": "Ultra HD 4K Streaming Cam", "amount": "₹9,499", "updated": "1 hour ago"},
        {"id": "WA-LEAD-104", "phone": "+91 99001-22334", "name": "Sneha Reddy", "stage": "Delivery Tracking Inquiry", "item": "Smart Fitness GPS Watch", "amount": "₹14,999", "updated": "2 hours ago"}
    ]

    catalog = [
        {"id": "WA-PROD-1", "name": "Wireless ANC Pro Headphones", "price": "₹12,499", "stock": "34 In Stock", "status": "Active"},
        {"id": "WA-PROD-2", "name": "Ergonomic RGB Mechanical Keyboard", "price": "₹6,999", "stock": "18 In Stock", "status": "Active"},
        {"id": "WA-PROD-3", "name": "Ultra HD 4K Streaming Cam", "price": "₹9,499", "stock": "12 In Stock", "status": "Active"},
        {"id": "WA-PROD-4", "name": "Smart Fitness GPS Watch", "price": "₹14,999", "stock": "25 In Stock", "status": "Active"}
    ]

    return jsonify({
        "metrics": {
            "total_whatsapp_conversations": 142,
            "delivery_rate": "99.8%",
            "read_rate": "96.4%",
            "quick_orders_generated": 38,
            "conversion_rate": "26.7%"
        },
        "leads": leads,
        "catalog": catalog
    })

# ==========================================
# 5. SAAS PLATFORM & API HEALTH DASHBOARD
# ==========================================
@dashboard_bp.route("/api/dashboard/saas", methods=["GET"])
def get_saas_dashboard():
    error_counts = query_db(
        """
        SELECT code, title, severity, count
        FROM (
            SELECT 'ERR_AUTH_EXPIRED' as code, 'OAuth Token Expired' as title, 'HIGH' as severity, 24 as count
            UNION ALL
            SELECT 'ERR_RATE_LIMIT_429', 'Rate Limit 429', 'MEDIUM', 48
            UNION ALL
            SELECT 'ERR_WEBHOOK_TIMEOUT', 'Webhook 5s Timeout', 'HIGH', 12
            UNION ALL
            SELECT 'ERR_SCHEMA_VALIDATION', 'Payload Validation', 'LOW', 35
        )
        """
    )

    developer_tickets = query_db(
        """
        SELECT * FROM tickets 
        WHERE subject LIKE '%Webcam%' OR subject LIKE '%API%' OR subject LIKE '%Issue%'
        ORDER BY created_at DESC
        """
    )

    return jsonify({
        "metrics": {
            "uptime": "99.98%",
            "avg_latency": "42ms",
            "api_requests_24h": "1.42M",
            "error_rate": "0.08%",
            "active_developer_keys": 684
        },
        "endpoint_health": [
            {"endpoint": "POST /api/v2/chat/completions", "status": "HEALTHY", "latency": "38ms", "uptime": "100%"},
            {"endpoint": "POST /api/v2/embeddings", "status": "HEALTHY", "latency": "22ms", "uptime": "99.99%"},
            {"endpoint": "POST /api/v2/webhooks/dispatch", "status": "HEALTHY", "latency": "65ms", "uptime": "99.95%"},
            {"endpoint": "GET /api/v2/orders/tracking", "status": "HEALTHY", "latency": "18ms", "uptime": "100%"}
        ],
        "error_distribution": error_counts,
        "developer_tickets": developer_tickets
    })
