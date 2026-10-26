from flask import Blueprint, request, jsonify
from backend.config import Config
from backend.llm.factory import LLMFactory

settings_bp = Blueprint("settings", __name__)

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "Not Set" if not key else "********"
    return f"{key[:4]}...{key[-4:]}"

@settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """Returns active settings and provider configurations."""
    active_provider = LLMFactory.get_active_provider_name()
    return jsonify({
        "active_provider": active_provider,
        "available_providers": ["demo", "gemini", "openai", "groq", "ollama"],
        "providers_config": {
            "demo": {
                "name": "Built-in Autonomous Engine",
                "description": "Zero-configuration offline mode. Executes ReAct reasoning and RAG tools immediately without an API key.",
                "configured": True,
                "model": "rule-heuristic-agent"
            },
            "gemini": {
                "name": "Google Gemini",
                "configured": bool(Config.GEMINI_API_KEY),
                "model": Config.GEMINI_MODEL,
                "api_key_masked": mask_key(Config.GEMINI_API_KEY)
            },
            "openai": {
                "name": "OpenAI",
                "configured": bool(Config.OPENAI_API_KEY),
                "model": Config.OPENAI_MODEL,
                "api_key_masked": mask_key(Config.OPENAI_API_KEY)
            },
            "groq": {
                "name": "Groq Cloud (Fast Llama)",
                "configured": bool(Config.GROQ_API_KEY),
                "model": Config.GROQ_MODEL,
                "api_key_masked": mask_key(Config.GROQ_API_KEY)
            },
            "ollama": {
                "name": "Ollama (Local LLM)",
                "configured": True,
                "model": Config.OLLAMA_MODEL,
                "base_url": Config.OLLAMA_BASE_URL
            }
        }
    })

@settings_bp.route("/api/settings", methods=["POST"])
def update_settings():
    """Updates active provider and/or configuration parameters at runtime."""
    data = request.get_json() or {}
    provider = data.get("provider")

    if not provider:
        return jsonify({"error": "Provider name is required"}), 400

    provider = provider.lower()
    if provider not in ["demo", "gemini", "openai", "groq", "ollama"]:
        return jsonify({"error": f"Invalid provider '{provider}'"}), 400

    # Optional runtime overrides
    api_key = data.get("api_key")
    model = data.get("model")
    base_url = data.get("base_url")

    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
        if provider == "gemini":
            Config.GEMINI_API_KEY = api_key
        elif provider == "openai":
            Config.OPENAI_API_KEY = api_key
        elif provider == "groq":
            Config.GROQ_API_KEY = api_key

    if model:
        kwargs["model"] = model
        if provider == "gemini":
            Config.GEMINI_MODEL = model
        elif provider == "openai":
            Config.OPENAI_MODEL = model
        elif provider == "groq":
            Config.GROQ_MODEL = model
        elif provider == "ollama":
            Config.OLLAMA_MODEL = model

    if base_url:
        kwargs["base_url"] = base_url
        if provider == "ollama":
            Config.OLLAMA_BASE_URL = base_url

    LLMFactory.set_active_provider(provider, **kwargs)

    return jsonify({
        "success": True,
        "message": f"Active LLM provider switched to '{provider}'.",
        "active_provider": provider
    })

@settings_bp.route("/api/database/status", methods=["GET"])
def get_database_status():
    """Returns database integrity, schema health, table row counts, and storage metrics."""
    from backend.database.db import get_db_stats, verify_db_integrity
    stats = get_db_stats()
    integrity_details = verify_db_integrity()
    return jsonify({
        "success": True,
        "database": stats,
        "verification": integrity_details
    })

@settings_bp.route("/api/database/optimize", methods=["POST"])
def optimize_database_endpoint():
    """Runs database index optimization, PRAGMA optimize, and VACUUM."""
    from backend.database.db import optimize_db, get_db_stats
    optimize_db()
    stats = get_db_stats()
    return jsonify({
        "success": True,
        "message": "Database optimized successfully",
        "database": stats
    })

@settings_bp.route("/api/database/seed", methods=["POST"])
def reseed_database_endpoint():
    """Refreshes seed datasets across all 5 agent domains."""
    from backend.database.seed_data import seed_database
    from backend.database.db import get_db_stats
    seed_database()
    stats = get_db_stats()
    return jsonify({
        "success": True,
        "message": "Database schema and seed datasets verified successfully",
        "database": stats
    })
