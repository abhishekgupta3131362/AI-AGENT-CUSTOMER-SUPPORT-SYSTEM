import json
from flask import Blueprint, jsonify, request
from backend.database.db import query_db, execute_db

agentforce_bp = Blueprint("agentforce", __name__)

DEFAULT_TOPICS = [
    {
        "id": "TOPIC-01",
        "name": "Order Logistics & Fulfillment",
        "description": "Handles package tracking, delivery date inquiries, carrier status (FedEx, UPS, DHL), and shipping address updates.",
        "agent": "E-Commerce Agentforce",
        "status": "Active",
        "actions": ["check_order_status", "search_knowledge_base"],
        "confidence_threshold": "85%",
        "auto_resolution_rate": "94.2%"
    },
    {
        "id": "TOPIC-02",
        "name": "Returns, Refunds & RMA Generation",
        "description": "Evaluates return eligibility within the 30-day warranty window, generates RMA numbers, and triggers payment refunds.",
        "agent": "E-Commerce Agentforce",
        "status": "Active",
        "actions": ["process_refund_return", "create_support_ticket"],
        "confidence_threshold": "90%",
        "auto_resolution_rate": "89.5%"
    },
    {
        "id": "TOPIC-03",
        "name": "Resort Reservations & Amenities",
        "description": "Checks live room inventory, quotes rates per night, books guest reservations, and dispatches housekeeping amenities.",
        "agent": "Hospitality Agentforce",
        "status": "Active",
        "actions": ["check_room_availability", "book_room_reservation", "request_housekeeping_amenity"],
        "confidence_threshold": "88%",
        "auto_resolution_rate": "96.1%"
    },
    {
        "id": "TOPIC-04",
        "name": "Telephony Voice IVR & Call Routing",
        "description": "Understands spoken customer inquiries via Web Speech STT, replies verbally with TTS, and performs warm transfer to human staff.",
        "agent": "Voice Agentforce",
        "status": "Active",
        "actions": ["voice_call_action", "escalate_to_human"],
        "confidence_threshold": "80%",
        "auto_resolution_rate": "88.5%"
    },
    {
        "id": "TOPIC-05",
        "name": "WhatsApp Commerce & Fast Checkout",
        "description": "Presents product catalog, generates instant UPI payment links, and captures verified customer leads on WhatsApp.",
        "agent": "WhatsApp Agentforce",
        "status": "Active",
        "actions": ["get_whatsapp_catalog", "whatsapp_quick_order"],
        "confidence_threshold": "85%",
        "auto_resolution_rate": "91.0%"
    },
    {
        "id": "TOPIC-06",
        "name": "API & Webhook Diagnostic Engineering",
        "description": "Diagnoses platform error codes (ERR_AUTH_EXPIRED, ERR_RATE_LIMIT_429), pulls developer documentation, and files engineering tickets.",
        "agent": "SaaS Fin Agentforce",
        "status": "Active",
        "actions": ["diagnose_error_code", "search_api_docs", "create_support_ticket"],
        "confidence_threshold": "92%",
        "auto_resolution_rate": "93.4%"
    }
]

TRUST_LAYER_CONFIG = {
    "pii_masking": True,
    "toxicity_filter": True,
    "hallucination_prevention": True,
    "zero_retention_guarantee": True,
    "prompt_injection_shield": True,
    "confidence_threshold": 85,
    "total_shielded_requests": 14280,
    "pii_entities_masked_today": 328,
    "injections_blocked_today": 14
}

@agentforce_bp.route("/api/agentforce/topics", methods=["GET"])
def get_topics():
    return jsonify({
        "status": "success",
        "topics": DEFAULT_TOPICS,
        "total_active_topics": len(DEFAULT_TOPICS)
    })

@agentforce_bp.route("/api/agentforce/trust-layer", methods=["GET", "POST"])
def trust_layer_handler():
    global TRUST_LAYER_CONFIG
    if request.method == "POST":
        data = request.get_json() or {}
        for k in ["pii_masking", "toxicity_filter", "hallucination_prevention", "prompt_injection_shield"]:
            if k in data:
                TRUST_LAYER_CONFIG[k] = bool(data[k])
        if "confidence_threshold" in data:
            TRUST_LAYER_CONFIG["confidence_threshold"] = int(data["confidence_threshold"])
        return jsonify({"status": "updated", "config": TRUST_LAYER_CONFIG})
    
    return jsonify({
        "status": "success",
        "config": TRUST_LAYER_CONFIG
    })

@agentforce_bp.route("/api/agentforce/roi-calculator", methods=["POST"])
def calculate_roi():
    data = request.get_json() or {}
    monthly_tickets = int(data.get("monthly_tickets", 25000))
    human_cost_per_ticket = float(data.get("human_cost_per_ticket", 10.0))
    deflection_rate = float(data.get("deflection_rate", 80.0)) / 100.0
    agentforce_cost_per_resolution = 2.00 # Salesforce Agentforce standard

    resolved_by_ai = round(monthly_tickets * deflection_rate)
    escalated_to_human = monthly_tickets - resolved_by_ai

    traditional_cost = monthly_tickets * human_cost_per_ticket
    agentforce_cost = (resolved_by_ai * agentforce_cost_per_resolution) + (escalated_to_human * human_cost_per_ticket)
    monthly_savings = max(0.0, traditional_cost - agentforce_cost)
    annual_savings = monthly_savings * 12
    roi_percent = round((monthly_savings / (resolved_by_ai * agentforce_cost_per_resolution) * 100), 1) if (resolved_by_ai * agentforce_cost_per_resolution) > 0 else 0

    return jsonify({
        "monthly_tickets": monthly_tickets,
        "deflection_rate_percent": round(deflection_rate * 100, 1),
        "resolved_by_ai": resolved_by_ai,
        "escalated_to_human": escalated_to_human,
        "traditional_monthly_cost": round(traditional_cost, 2),
        "agentforce_monthly_cost": round(agentforce_cost, 2),
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "roi_percent": roi_percent
    })
