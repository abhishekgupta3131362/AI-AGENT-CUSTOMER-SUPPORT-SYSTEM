import uuid
from flask import Blueprint, request, jsonify
from backend.database.db import query_db, execute_db

ticket_bp = Blueprint("tickets", __name__)

@ticket_bp.route("/api/tickets", methods=["GET"])
def get_tickets():
    """Lists support tickets, optionally filtered by status."""
    status_filter = request.args.get("status")
    if status_filter:
        tickets = query_db(
            "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC",
            (status_filter.upper(),)
        )
    else:
        tickets = query_db("SELECT * FROM tickets ORDER BY created_at DESC")
    return jsonify({"tickets": tickets})

@ticket_bp.route("/api/tickets", methods=["POST"])
def create_ticket():
    """Manually creates a support ticket."""
    data = request.get_json() or {}
    subject = data.get("subject", "").strip()
    description = data.get("description", "").strip()
    customer_email = data.get("customer_email", "support@apextech.com").strip()
    priority = data.get("priority", "MEDIUM").upper()

    if not subject or not description:
        return jsonify({"error": "Subject and description are required"}), 400

    ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    execute_db(
        """
        INSERT INTO tickets (id, customer_email, subject, description, priority, status, assigned_agent)
        VALUES (?, ?, ?, ?, ?, 'OPEN', 'Human Support')
        """,
        (ticket_id, customer_email, subject, description, priority)
    )

    created = query_db("SELECT * FROM tickets WHERE id = ?", (ticket_id,), one=True)
    return jsonify({"success": True, "ticket": created}), 201

@ticket_bp.route("/api/tickets/<ticket_id>", methods=["PATCH"])
def update_ticket(ticket_id):
    """Updates ticket status or resolution notes."""
    data = request.get_json() or {}
    status = data.get("status")
    resolution_notes = data.get("resolution_notes")
    assigned_agent = data.get("assigned_agent")

    existing = query_db("SELECT * FROM tickets WHERE id = ?", (ticket_id,), one=True)
    if not existing:
        return jsonify({"error": f"Ticket {ticket_id} not found"}), 404

    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status.upper())
    if resolution_notes is not None:
        updates.append("resolution_notes = ?")
        params.append(resolution_notes)
    if assigned_agent:
        updates.append("assigned_agent = ?")
        params.append(assigned_agent)

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(ticket_id)

    query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?"
    execute_db(query, tuple(params))

    updated = query_db("SELECT * FROM tickets WHERE id = ?", (ticket_id,), one=True)
    return jsonify({"success": True, "ticket": updated})

@ticket_bp.route("/api/tickets/<ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    """Deletes a ticket."""
    execute_db("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    return jsonify({"success": True, "message": f"Ticket {ticket_id} deleted."})
