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
