"""
Shop Manager SaaS — Flask Application Factory
"""
from __future__ import annotations
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# Extension instances (created here, bound to app in create_app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)

# In-memory JWT blocklist (use Redis in production)
jwt_blocklist = set()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__, instance_relative_config=False)

    # ----- Configuration -----
    from app.config import config_map
    env = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config_map[env])
    app.url_map.strict_slashes = False

    # ----- Extensions -----
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })

    # ----- Import Models -----
    from app.models import user, store, product, sale, customer, udhaar, bill, onboarding  # noqa: F401

    with app.app_context():
        db.create_all()

    # ----- JWT Token Blocklist -----
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        return jti in jwt_blocklist

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Invalid token", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Authorization token required", "error": "authorization_required"}), 401

    # ----- Register Blueprints -----
    from app.routes.auth import auth_bp
    from app.routes.store import store_bp
    from app.routes.product import product_bp
    from app.routes.sales import sales_bp
    from app.routes.customer import customer_bp
    from app.routes.bills import bills_bp
    from app.routes.reports import reports_bp
    from app.routes.ai_insights import ai_bp
    from app.routes.payments import payments_bp
    from app.routes.onboarding import onboarding_bp

    app.register_blueprint(auth_bp,       url_prefix='/api/auth')
    app.register_blueprint(store_bp,      url_prefix='/api/stores')
    app.register_blueprint(product_bp,    url_prefix='/api/stores')
    app.register_blueprint(sales_bp,      url_prefix='/api/stores')
    app.register_blueprint(customer_bp,   url_prefix='/api/stores')
    app.register_blueprint(bills_bp,      url_prefix='/api/stores')
    app.register_blueprint(reports_bp,    url_prefix='/api/stores')
    app.register_blueprint(ai_bp,         url_prefix='/api/stores')
    app.register_blueprint(payments_bp,   url_prefix='/api/payments')
    app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')

    # ----- Health Check -----
    @app.route('/api/health')
    def health():
        return jsonify({
            "success": True,
            "message": "ShopManager API is running",
            "version": "1.0.0",
            "environment": env
        })

    # ----- Global Error Handlers -----
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({"success": False, "message": "Too many requests. Please slow down."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app
