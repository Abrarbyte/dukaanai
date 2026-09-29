"""
app/routes/auth.py — Authentication endpoints
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/forgot-password
POST /api/auth/reset-password
GET  /api/auth/me
PUT  /api/auth/me
"""
import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt, jwt_required
)
from app import db, bcrypt, jwt_blocklist, limiter
from app.models.user import User
from app.models.onboarding import Onboarding
from app.utils.auth_helper import token_required, get_current_user
from app.utils.validators import validate_signup_data, validate_email, validate_password
from app.utils.helpers import success_response, error_response, validation_error_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("10 per hour")
def signup():
    """Register a new user account."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = validate_signup_data(data)
    if not valid:
        return validation_error_response(errors)

    # Check if email already exists
    if User.query.filter_by(email=cleaned['email']).first():
        return error_response("An account with this email already exists", 409)

    # Hash password
    password_hash = bcrypt.generate_password_hash(cleaned['password']).decode('utf-8')

    # Create user
    user = User(
        name=cleaned['name'],
        email=cleaned['email'],
        password_hash=password_hash,
        phone=cleaned.get('phone'),
        plan='free',
    )
    db.session.add(user)
    db.session.flush()  # Get user.id before commit

    # Create onboarding record
    onboarding = Onboarding(user_id=user.id)
    db.session.add(onboarding)
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'onboarding_required': True,
        },
        message="Account created successfully",
        status_code=201
    )


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    remember_me = bool(data.get('remember_me', False))

    if not email or not password:
        return error_response("Email and password are required", 400)

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return error_response("Invalid email or password", 401)

    if not user.is_active:
        return error_response("Account has been deactivated. Contact support.", 403)

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # Adjust token expiry for "remember me"
    access_expires = timedelta(hours=24) if not remember_me else timedelta(days=7)
    refresh_expires = timedelta(days=30) if not remember_me else timedelta(days=90)

    access_token = create_access_token(identity=str(user.id), expires_delta=access_expires)
    refresh_token = create_refresh_token(identity=str(user.id), expires_delta=refresh_expires)

    # Check onboarding status
    onboarding = user.onboarding
    is_onboarded = onboarding.is_onboarded if onboarding else False

    return success_response(data={
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'is_onboarded': is_onboarded,
    }, message="Login successful")


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout: add current token to blocklist."""
    jti = get_jwt().get("jti")
    if jti:
        jwt_blocklist.add(jti)
    return success_response(message="Logged out successfully")


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Get a new access token using refresh token."""
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return success_response(data={'access_token': new_access_token}, message="Token refreshed")


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")
def forgot_password():
    """Initiate password reset flow."""
    data = request.get_json(silent=True) or {}
    ok, email = validate_email(data.get('email', ''))
    if not ok:
        return error_response(email, 400)

    user = User.query.filter_by(email=email).first()

    # Always return success to prevent email enumeration
    if user:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        # Phase 3: Send email with reset link
        # For now, return the token (dev mode only; remove in production)
        reset_link = f"{current_app.config['APP_URL']}/reset-password?token={reset_token}"
        if current_app.debug:
            return success_response(
                data={'reset_token': reset_token, 'reset_link': reset_link},
                message="Password reset link generated (dev mode)"
            )

    return success_response(message="If that email exists, a reset link has been sent.")


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("10 per hour")
def reset_password():
    """Complete password reset with token."""
    data = request.get_json(silent=True) or {}
    token = data.get('token', '').strip()
    new_password = data.get('new_password', '')

    if not token:
        return error_response("Reset token is required", 400)

    ok, val = validate_password(new_password)
    if not ok:
        return error_response(val, 400)

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return error_response("Invalid or expired reset token", 400)

    if user.reset_token_expiry < datetime.now(timezone.utc):
        return error_response("Reset token has expired. Please request a new one.", 400)

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()

    return success_response(message="Password reset successfully. Please login.")


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me():
    """Return current authenticated user's profile."""
    user = get_current_user()
    return success_response(data={'user': user.to_dict()})


@auth_bp.route('/me', methods=['PUT'])
@token_required
def update_me():
    """Update current user's profile (name, phone only; email/password are separate)."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = str(data['name']).strip()
        if not name or len(name) > 100:
            return error_response("Name must be 1-100 characters", 400)
        user.name = name

    if 'phone' in data:
        from app.utils.validators import validate_phone
        ok, phone = validate_phone(data['phone'])
        if not ok:
            return error_response(phone, 400)
        user.phone = phone or None

    db.session.commit()
    return success_response(data={'user': user.to_dict()}, message="Profile updated")


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change password for authenticated user."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not bcrypt.check_password_hash(user.password_hash, current_password):
        return error_response("Current password is incorrect", 400)

    ok, val = validate_password(new_password)
    if not ok:
        return error_response(val, 400)

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return success_response(message="Password changed successfully")
