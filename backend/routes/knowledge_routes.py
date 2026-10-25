from flask import Blueprint, request, jsonify
from backend.rag.vector_store import VectorStore

knowledge_bp = Blueprint("knowledge", __name__)
vector_store = VectorStore()

@knowledge_bp.route("/api/knowledge", methods=["GET"])
def get_documents():
    """Returns all primary knowledge base documents."""
    docs = vector_store.list_documents()
    return jsonify({"documents": docs})

@knowledge_bp.route("/api/knowledge", methods=["POST"])
def add_document():
    """Adds a new document to the knowledge base and indexes it into the vector store."""
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    category = data.get("category", "General").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    doc_id = vector_store.add_document(title=title, category=category, content=content)
    return jsonify({"success": True, "doc_id": doc_id, "message": "Document indexed successfully."}), 201

@knowledge_bp.route("/api/knowledge/search", methods=["POST"])
def search_knowledge():
    """Performs semantic vector search on the knowledge base."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    top_k = int(data.get("top_k", 3))

    if not query:
        return jsonify({"error": "Query string is required"}), 400

    results = vector_store.search(query=query, top_k=top_k)
    return jsonify({"query": query, "results": results})

@knowledge_bp.route("/api/knowledge/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Deletes a knowledge base document."""
    vector_store.delete_document(doc_id)
    return jsonify({"success": True, "message": f"Document {doc_id} deleted."})

@knowledge_bp.route("/api/knowledge/reindex", methods=["POST"])
def reindex_knowledge():
    """Reindexes all documents."""
    vector_store.reindex_all()
    return jsonify({"success": True, "message": "Knowledge base reindexed successfully."})
