import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.database.seed_data import seed_database
from backend.routes.chat_routes import chat_bp
from backend.routes.ticket_routes import ticket_bp
from backend.routes.order_routes import order_bp
from backend.routes.knowledge_routes import knowledge_bp
from backend.routes.settings_routes import settings_bp

def create_app():
    # Points static folder to the root 'static' directory
    static_folder = Path(__file__).resolve().parent.parent / "static"
    
    app = Flask(__name__, static_folder=str(static_folder), static_url_path="")
    app.config.from_object(Config)
    
    # Enable CORS for cross-origin development (e.g. Vite frontend)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Auto initialize and seed DB if empty
    seed_database()

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(settings_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "system": "ApexTech AI Customer Support Agent",
            "active_provider": Config.DEFAULT_LLM_PROVIDER
        })

    # Serve Single Page Application frontend
    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(str(static_folder), "index.html")

    @app.route("/<path:path>", methods=["GET"])
    def static_proxy(path):
        file_path = static_folder / path
        if file_path.exists():
            return send_from_directory(str(static_folder), path)
        return send_from_directory(str(static_folder), "index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    print(f"Starting ApexTech Support Agent on http://127.0.0.1:{Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
