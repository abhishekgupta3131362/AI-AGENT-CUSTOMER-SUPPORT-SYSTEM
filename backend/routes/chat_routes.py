import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.agent.support_agent import SupportAgent
from backend.database.db import query_db, execute_db

chat_bp = Blueprint("chat", __name__)
agent = SupportAgent()

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """Synchronous chat endpoint."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default_session").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Fetch last 4 messages from history
    history = query_db(
        "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT 6",
        (session_id,)
    )
    history = list(reversed(history)) if history else []

    result = agent.run_agent(message, session_id=session_id, chat_history=history)
    return jsonify(result)

@chat_bp.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Server-Sent Events (SSE) streaming chat endpoint."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default_session").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Fetch history
    history = query_db(
        "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT 6",
        (session_id,)
    )
    history = list(reversed(history)) if history else []

    def event_stream():
        for event in agent.run_agent_stream(message, session_id=session_id, chat_history=history):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

@chat_bp.route("/api/chat/history/<session_id>", methods=["GET"])
def get_history(session_id):
    """Fetches full chat history for a session."""
    messages = query_db(
        "SELECT id, session_id, role, content, tool_calls, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    for m in messages:
        if m.get("tool_calls"):
            try:
                m["tool_calls"] = json.loads(m["tool_calls"])
            except Exception:
                pass
    return jsonify({"session_id": session_id, "messages": messages})

@chat_bp.route("/api/chat/session/<session_id>", methods=["DELETE"])
def clear_session(session_id):
    """Clears messages for a session."""
    execute_db("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    return jsonify({"success": True, "message": f"Session {session_id} cleared."})

@chat_bp.route("/api/chat/csat", methods=["POST"])
def submit_csat():
    """Records customer satisfaction rating (1 to 5 stars) and feedback."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    rating = int(data.get("rating", 5))
    feedback = data.get("feedback", "").strip()

    if not session_id:
        return jsonify({"error": "Session ID required"}), 400

    execute_db(
        "UPDATE chat_sessions SET csat_rating = ?, csat_feedback = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
        (rating, feedback, session_id)
    )
    return jsonify({"success": True, "message": "Thank you for your feedback!"})

@chat_bp.route("/api/chat/takeover", methods=["POST"])
def toggle_human_takeover():
    """Allows a human support specialist in the CRM to take over a session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    is_takeover = int(bool(data.get("takeover", True)))
    agent_name = data.get("agent_name", "Sarah M. (Live Specialist)").strip()

    if not session_id:
        return jsonify({"error": "Session ID required"}), 400

    execute_db(
        "INSERT OR IGNORE INTO chat_sessions (session_id, customer_id, customer_name) VALUES (?, 'guest', 'Valued Customer')",
        (session_id,)
    )

    execute_db(
        "UPDATE chat_sessions SET is_human_takeover = ?, active_human_agent = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
        (is_takeover, agent_name if is_takeover else None, session_id)
    )

    # Insert a system transition message in chat
    transition_msg = f"🔔 {agent_name} has joined the conversation as your live support representative." if is_takeover else "🤖 Human representative has concluded the live session. AI assistant is back online."
    execute_db(
        "INSERT INTO chat_messages (session_id, role, sender_name, content) VALUES (?, 'assistant', 'System Notice', ?)",
        (session_id, transition_msg)
    )

    return jsonify({"success": True, "is_human_takeover": is_takeover, "agent_name": agent_name})

@chat_bp.route("/api/chat/human-reply", methods=["POST"])
def send_human_reply():
    """Allows a human agent to send a message directly to the customer."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    message = data.get("message", "").strip()
    agent_name = data.get("agent_name", "Human Support Specialist").strip()

    if not session_id or not message:
        return jsonify({"error": "Session ID and message required"}), 400

    execute_db(
        "INSERT OR IGNORE INTO chat_sessions (session_id, customer_id, customer_name) VALUES (?, 'guest', 'Valued Customer')",
        (session_id,)
    )

    execute_db(
        "INSERT INTO chat_messages (session_id, role, sender_name, content) VALUES (?, 'assistant', ?, ?)",
        (session_id, agent_name, message)
    )

    return jsonify({"success": True, "message": message, "sender": agent_name})

@chat_bp.route("/api/chat/session/<session_id>/status", methods=["GET"])
def get_session_status(session_id):
    """Retrieves session metadata, takeover status, and sentiment."""
    session = query_db(
        "SELECT session_id, customer_name, sentiment_score, sentiment_label, csat_rating, is_human_takeover, active_human_agent FROM chat_sessions WHERE session_id = ?",
        (session_id,),
        one=True
    )
    if not session:
        return jsonify({"session_id": session_id, "is_human_takeover": 0, "sentiment_label": "Neutral"})
    return jsonify(session)
