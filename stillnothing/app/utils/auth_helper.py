"""
app/utils/auth_helper.py — JWT helpers, decorators, plan enforcement
"""
from __future__ import annotations
from functools import wraps
from flask import jsonify, current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app import db
from app.models.user import User
from app.models.store import Store


def get_current_user() -> User | None:
    """Return the authenticated User object from JWT identity."""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
        return db.session.get(User, int(user_id))
    except Exception as e:
        print(f"[AUTH DEBUG] get_current_user error: {str(e)}")
        return None


def token_required(f):
    """Decorator: Require valid JWT access token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"\n[AUTH DEBUG] --- Request: {request.method} {request.path} ---")
        print(f"[AUTH DEBUG] Auth Header: {request.headers.get('Authorization')}")
        
        try:
            verify_jwt_in_request()
            print(f"[AUTH DEBUG] verify_jwt_in_request: SUCCESS")
        except Exception as e:
            print(f"[AUTH DEBUG] verify_jwt_in_request: FAILED - {str(e)}")
            return jsonify({
                "success": False, 
                "message": f"Authentication failed: {str(e)}",
                "error": "authentication_failed"
            }), 401
        
        user = get_current_user()
        if not user:
            print(f"[AUTH DEBUG] User identification: FAILED (ID: {get_jwt_identity()})")
            return jsonify({"success": False, "message": "User context could not be established", "error": "user_not_found"}), 401
        
        print(f"[AUTH DEBUG] User identification: SUCCESS (User: {user.email})")
        
        if not user.is_active:
            print(f"[AUTH DEBUG] User status: INACTIVE")
            return jsonify({"success": False, "message": "Account is deactivated", "error": "account_deactivated"}), 403
        
        return f(*args, **kwargs)
    return decorated


def require_plan(*plans):
    """
    Decorator factory: restrict endpoint to users on specified plans.
    Usage: @require_plan('pro', 'premium')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            print(f"\n[AUTH DEBUG] --- Plan Protected Request: {request.method} {request.path} ---")
            try:
                verify_jwt_in_request()
            except Exception as e:
                print(f"[AUTH DEBUG] verify_jwt_in_request: FAILED - {str(e)}")
                return jsonify({
                    "success": False, 
                    "message": f"Authentication failed: {str(e)}",
                    "error": "authentication_failed"
                }), 401
            
            user = get_current_user()
            if not user:
                print(f"[AUTH DEBUG] User identification: FAILED")
                return jsonify({"success": False, "message": "User not found", "error": "user_not_found"}), 401
            
            print(f"[AUTH DEBUG] Plan Check: {user.plan} in {plans}")
            
            if user.plan not in plans:
                print(f"[AUTH DEBUG] Plan Check: FAILED")
                return jsonify({
                    "success": False,
                    "message": f"This feature requires a {' or '.join(plans)} plan. Current plan: {user.plan}",
                    "upgrade_required": True,
                    "current_plan": user.plan,
                    "required_plans": list(plans),
                    "error": "insufficient_plan"
                }), 403
            
            print(f"[AUTH DEBUG] Plan Check: SUCCESS")
            return f(*args, **kwargs)
        return decorated
    return decorator


def verify_store_access(store_id: int, user: User) -> Store | None:
    """
    Verify that a store belongs to the requesting user.
    Returns the Store object if access is granted, None otherwise.
    """
    store = db.session.get(Store, store_id)
    if not store:
        return None
    if store.user_id != user.id:
        return None
    if not store.is_active:
        return None
    return store


def check_store_limit(user: User) -> tuple[bool, str]:
    """
    Check if user can create another store based on their plan.
    Returns (allowed: bool, message: str)
    """
    limits = user.get_plan_limits()
    max_stores = limits.get('max_stores')
    if max_stores is None:
        return True, "OK"

    current_stores = Store.query.filter_by(user_id=user.id, is_active=True).count()
    if current_stores >= max_stores:
        return False, (
            f"Your {user.plan} plan allows {max_stores} store(s). "
            f"Upgrade to Premium for unlimited stores."
        )
    return True, "OK"


def check_product_limit(user: User, store_id: int) -> tuple[bool, str]:
    """
    Check if user can add another product based on their plan.
    Returns (allowed: bool, message: str)
    """
    from app.models.product import Product
    limits = user.get_plan_limits()
    max_products = limits.get('max_products')
    if max_products is None:
        return True, "OK"

    current_products = Product.query.filter_by(store_id=store_id, is_active=True).count()
    if current_products >= max_products:
        return False, (
            f"Your {user.plan} plan allows {max_products} product(s). "
            f"Upgrade to Pro or Premium for unlimited products."
        )
    return True, "OK"


def check_feature_access(user: User, feature: str) -> tuple[bool, str]:
    """
    Check if user's plan allows a specific feature.
    Features: 'gst_billing', 'whatsapp_share', 'ai_insights', 'multi_user'
    """
    limits = user.get_plan_limits()
    allowed = limits.get(feature, False)
    if not allowed:
        plan_name = 'Pro' if feature in ['gst_billing', 'whatsapp_share'] else 'Premium'
        return False, f"This feature requires the {plan_name} plan. Upgrade to unlock."
    return True, "OK"
