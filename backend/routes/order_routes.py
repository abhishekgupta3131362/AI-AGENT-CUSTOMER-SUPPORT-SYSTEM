import json
from flask import Blueprint, jsonify, request
from backend.database.db import query_db
from backend.services.ecommerce_api import EcommerceAPIService

order_bp = Blueprint("orders", __name__)

@order_bp.route("/api/ecommerce/track", methods=["GET", "POST"])
def track_ecommerce_order():
    """
    Real-time multi-platform tracking API endpoint.
    Accepts Order ID or Phone number with optional platform hint.
    Returns live carrier telemetry from Ekart, ATS, or standard carriers.
    """
    if request.method == "POST":
        data = request.get_json() or {}
        identifier = data.get("order_id") or data.get("id") or data.get("tracking_number") or data.get("phone", "")
        platform_hint = data.get("platform")
    else:
        identifier = request.args.get("order_id") or request.args.get("id") or request.args.get("phone", "")
        platform_hint = request.args.get("platform")

    if not identifier:
        return jsonify({
            "success": False,
            "error": "Missing 'order_id' or 'id' parameter. Provide an order ID like 'OD409218392100' or '171-8839201-9921'."
        }), 400

    tracking_data = EcommerceAPIService.track_order_realtime(str(identifier), platform_hint)
    formatted_msg = EcommerceAPIService.format_tracking_response(tracking_data)

    return jsonify({
        "success": True,
        "identifier": identifier,
        "platform": tracking_data.get("platform", "Unknown"),
        "found": tracking_data.get("found", False),
        "data": tracking_data,
        "formatted_text": formatted_msg
    })

@order_bp.route("/api/ecommerce/platforms", methods=["GET"])
def get_supported_platforms():
    """Returns list of supported multi-platform e-commerce stores and carriers."""
    return jsonify({
        "success": True,
        "platforms": EcommerceAPIService.SUPPORTED_PLATFORMS
    })

@order_bp.route("/api/orders", methods=["GET"])
def get_orders():
    """Lists all mock orders with customer names."""
    rows = query_db(
        """
        SELECT o.*, c.name as customer_name, c.email as customer_email, c.tier as customer_tier
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC
        """
    )
    for r in rows:
        try:
            r["items_parsed"] = json.loads(r["items"])
        except Exception:
            r["items_parsed"] = r["items"]
    return jsonify({"orders": rows})

@order_bp.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Fetches details for a single order."""
    row = query_db(
        """
        SELECT o.*, c.name as customer_name, c.email as customer_email, c.tier as customer_tier
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.id = ?
        """,
        (order_id.upper(),),
        one=True
    )
    if not row:
        return jsonify({"error": f"Order {order_id} not found"}), 404
    try:
        row["items_parsed"] = json.loads(row["items"])
    except Exception:
        row["items_parsed"] = row["items"]
    return jsonify({"order": row})

@order_bp.route("/api/customers", methods=["GET"])
def get_customers():
    """Lists customers."""
    customers = query_db("SELECT * FROM customers ORDER BY created_at DESC")
    return jsonify({"customers": customers})
