import json
from flask import Blueprint, jsonify
from backend.database.db import query_db

order_bp = Blueprint("orders", __name__)

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
