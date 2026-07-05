from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from datetime import timedelta
from .config import Config

mongo = PyMongo()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=['http://localhost:5173'])
    mongo.init_app(app)

    # JWT Authentication
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=Config.JWT_ACCESS_TOKEN_HOURS)
    jwt.init_app(app)

    # ─── Register Blueprints (route modules) ──────────────────────────
    from .routes.resume_routes import resume_bp
    from .routes.gap_routes import gap_bp
    from .routes.roadmap_routes import roadmap_bp
    from .routes.prediction_routes import prediction_bp
    from .routes.auth_routes import auth_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.chat_routes import chat_bp

    app.register_blueprint(resume_bp,     url_prefix="/api/resume")
    app.register_blueprint(gap_bp,        url_prefix="/api/gap")
    app.register_blueprint(roadmap_bp,    url_prefix="/api/roadmap")
    app.register_blueprint(prediction_bp, url_prefix="/api/predict")
    app.register_blueprint(auth_bp,       url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/api/dashboard")
    app.register_blueprint(chat_bp,       url_prefix="/api/chat")

    # ─── Health check route ───────────────────────────────────────────
    @app.route("/api/health")
    def health():
        return {"status": "OK", "message": "AI Career Navigator API is running"}, 200

    return app