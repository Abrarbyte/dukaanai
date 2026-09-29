"""
app/routes/store.py — Multi-store management endpoints
POST   /api/stores
GET    /api/stores
GET    /api/stores/<store_id>
PUT    /api/stores/<store_id>
DELETE /api/stores/<store_id>
GET    /api/stores/<store_id>/dashboard
"""
from datetime import datetime, timezone
from flask import Blueprint, request
from sqlalchemy import func
from app import db
from app.models.store import Store
from app.models.sale import Sale
from app.models.product import Product
from app.models.customer import Customer
from app.utils.auth_helper import token_required, get_current_user, verify_store_access, check_store_limit
from app.utils.validators import validate_store_data
from app.utils.helpers import success_response, error_response, validation_error_response, get_date_range
from app.services.alert_service import get_low_stock_alerts, get_daily_summary

store_bp = Blueprint('store', __name__)


@store_bp.route('', methods=['POST'])
@token_required
def create_store():
    """Create a new store for the current user."""
    user = get_current_user()

    # Check plan limit
    allowed, msg = check_store_limit(user)
    if not allowed:
        return error_response(msg, 403, upgrade_required=True)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = validate_store_data(data)
    if not valid:
        return validation_error_response(errors)

    store = Store(
        user_id=user.id,
        store_name=cleaned['store_name'],
        store_type=cleaned['store_type'],
        address=cleaned.get('address'),
        gst_number=cleaned.get('gst_number'),
        phone=cleaned.get('phone'),
        email=cleaned.get('email'),
    )
    db.session.add(store)

    # Update onboarding
    if user.onboarding:
        user.onboarding.store_created = True
        if user.onboarding.step_completed < 1:
            user.onboarding.step_completed = 1

    db.session.commit()
    return success_response(data={'store': store.to_dict()}, message="Store created successfully", status_code=201)


@store_bp.route('', methods=['GET'])
@token_required
def list_stores():
    """List all active stores for the current user."""
    user = get_current_user()
    stores = Store.query.filter_by(user_id=user.id, is_active=True).order_by(Store.created_at.asc()).all()
    return success_response(data={
        'stores': [s.to_dict() for s in stores],
        'total': len(stores),
        'plan': user.plan,
        'plan_limits': user.get_plan_limits(),
    })


@store_bp.route('/<int:store_id>', methods=['GET'])
@token_required
def get_store(store_id):
    """Get a specific store's details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)
    return success_response(data={'store': store.to_dict()})


@store_bp.route('/<int:store_id>', methods=['PUT'])
@token_required
def update_store(store_id):
    """Update store details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = validate_store_data(data)
    if not valid:
        return validation_error_response(errors)

    store.store_name = cleaned['store_name']
    store.store_type = cleaned['store_type']
    store.address = cleaned.get('address')
    store.gst_number = cleaned.get('gst_number')
    store.phone = cleaned.get('phone')
    store.email = cleaned.get('email')

    # Optional settings
    if 'invoice_prefix' in data:
        prefix = str(data['invoice_prefix']).strip().upper()
        if 1 <= len(prefix) <= 10:
            store.invoice_prefix = prefix
    if 'tax_rate' in data:
        try:
            store.tax_rate = float(data['tax_rate'])
        except (TypeError, ValueError):
            pass

    db.session.commit()
    return success_response(data={'store': store.to_dict()}, message="Store updated successfully")


@store_bp.route('/<int:store_id>', methods=['DELETE'])
@token_required
def delete_store(store_id):
    """Soft-delete a store (sets is_active=False)."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Prevent deleting last store
    active_stores = Store.query.filter_by(user_id=user.id, is_active=True).count()
    if active_stores <= 1:
        return error_response("Cannot delete your only store", 400)

    store.is_active = False
    db.session.commit()
    return success_response(message="Store deleted successfully")


@store_bp.route('/<int:store_id>/dashboard', methods=['GET'])
@token_required
def get_dashboard(store_id):
    """
    Full dashboard data for a store.
    Includes today's stats, top products, low stock alerts, recent transactions.
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Daily summary
    daily = get_daily_summary(store_id)

    # This month stats
    month_start, now = get_date_range('month')
    monthly_revenue = db.session.query(
        func.coalesce(func.sum(Sale.total_amount), 0)
    ).filter(Sale.store_id == store_id, Sale.created_at >= month_start).scalar() or 0
    monthly_profit = db.session.query(
        func.coalesce(func.sum(Sale.profit), 0)
    ).filter(Sale.store_id == store_id, Sale.created_at >= month_start).scalar() or 0

    # Total counts
    total_products = Product.query.filter_by(store_id=store_id, is_active=True).count()
    total_customers = Customer.query.filter_by(store_id=store_id, is_active=True).count()

    # Top 5 selling products (last 7 days)
    from app.services.ai_service import get_fast_selling_products
    top_products = get_fast_selling_products(store_id, days=7, limit=5)

    # Low stock alerts
    low_stock = get_low_stock_alerts(store_id)

    # Recent 10 sales
    recent_sales = (
        Sale.query
        .filter_by(store_id=store_id)
        .order_by(Sale.created_at.desc())
        .limit(10)
        .all()
    )

    # Weekly revenue chart (last 7 days)
    weekly_chart = []
    for i in range(6, -1, -1):
        from datetime import timedelta
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_revenue = db.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).filter(
            Sale.store_id == store_id,
            Sale.created_at.between(day_start, day_end)
        ).scalar() or 0
        weekly_chart.append({
            'date': day_start.strftime('%d %b'),
            'revenue': float(day_revenue),
        })

    return success_response(data={
        'store': store.to_dict(),
        'today': daily['today'],
        'monthly': {
            'revenue': float(monthly_revenue),
            'profit': float(monthly_profit),
        },
        'stats': {
            'total_products': total_products,
            'total_customers': total_customers,
            'low_stock_count': len(low_stock),
        },
        'top_products': top_products,
        'low_stock_alerts': low_stock[:5],  # Show top 5 on dashboard
        'recent_sales': [s.to_dict() for s in recent_sales],
        'weekly_chart': weekly_chart,
        'alerts': daily['alerts'],
        'payment_modes': daily['payment_modes'],
    })
