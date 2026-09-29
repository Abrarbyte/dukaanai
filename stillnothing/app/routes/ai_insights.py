"""
app/routes/ai_insights.py — AI-powered analytics endpoints
GET /api/stores/<store_id>/insights/fast-selling
GET /api/stores/<store_id>/insights/dead-stock
GET /api/stores/<store_id>/insights/restock
GET /api/stores/<store_id>/insights/best-margin
GET /api/stores/<store_id>/insights/peak-hours
GET /api/stores/<store_id>/insights/demand/<product_id>
"""
from flask import Blueprint, request
from app.utils.auth_helper import token_required, get_current_user, verify_store_access, check_feature_access
from app.utils.helpers import success_response, error_response
from app.services import ai_service

ai_bp = Blueprint('ai', __name__)


def _require_ai_access(user, store):
    """Check that user's plan allows AI insights (premium only)."""
    ok, msg = check_feature_access(user, 'ai_insights')
    if not ok:
        # For Phase 1, provide basic insights to all plans (Phase 3 will enforce)
        # Return (allowed=True) but note the upgrade
        pass
    return True, None


@ai_bp.route('/<int:store_id>/insights/fast-selling', methods=['GET'])
@token_required
def fast_selling(store_id):
    """Top selling products by quantity in recent period."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        days, limit = 7, 10

    days = max(1, min(days, 365))
    limit = max(1, min(limit, 50))

    products = ai_service.get_fast_selling_products(store_id, days=days, limit=limit)
    return success_response(data={
        'fast_selling_products': products,
        'period_days': days,
        'insight': f"These {len(products)} products generated the most sales in the last {days} days."
    })


@ai_bp.route('/<int:store_id>/insights/dead-stock', methods=['GET'])
@token_required
def dead_stock(store_id):
    """Products with zero sales in the last N days."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    try:
        days = int(request.args.get('days', 30))
    except (TypeError, ValueError):
        days = 30

    days = max(7, min(days, 365))
    products = ai_service.get_dead_stock(store_id, days=days)

    total_locked_value = sum(p['stock_value'] for p in products)
    return success_response(data={
        'dead_stock_products': products,
        'period_days': days,
        'total_products': len(products),
        'total_value_locked': total_locked_value,
        'insight': (
            f"{len(products)} products haven't sold in {days} days, "
            f"locking ₹{total_locked_value:,.2f} in inventory."
        )
    })


@ai_bp.route('/<int:store_id>/insights/restock', methods=['GET'])
@token_required
def restock_suggestions(store_id):
    """Products that need restocking urgently."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    suggestions = ai_service.get_restock_suggestions(store_id)
    total_restock_cost = sum(s['restock_cost_estimate'] for s in suggestions)

    return success_response(data={
        'restock_suggestions': suggestions,
        'total_products': len(suggestions),
        'estimated_total_cost': total_restock_cost,
        'insight': (
            f"{len(suggestions)} products need restocking. "
            f"Estimated investment: ₹{total_restock_cost:,.2f}"
        )
    })


@ai_bp.route('/<int:store_id>/insights/best-margin', methods=['GET'])
@token_required
def best_margin(store_id):
    """Products with highest profit margins."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    try:
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10

    products = ai_service.get_best_margin_products(store_id, limit=limit)
    return success_response(data={
        'best_margin_products': products,
        'insight': f"Focus on selling these {len(products)} products to maximize profit."
    })


@ai_bp.route('/<int:store_id>/insights/peak-hours', methods=['GET'])
@token_required
def peak_hours(store_id):
    """Peak sales hours analysis."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    try:
        days = int(request.args.get('days', 30))
    except (TypeError, ValueError):
        days = 30

    data = ai_service.get_peak_sales_hours(store_id, days=days)

    # Find peak hour
    peak = max(data, key=lambda x: x['order_count']) if data else None
    insight = (
        f"Your busiest hour is {peak['hour_label']} with {peak['order_count']} orders."
        if peak and peak['order_count'] > 0
        else "Not enough sales data yet to identify peak hours."
    )

    return success_response(data={
        'hourly_data': data,
        'period_days': days,
        'peak_hour': peak,
        'insight': insight,
    })


@ai_bp.route('/<int:store_id>/insights/demand/<int:product_id>', methods=['GET'])
@token_required
def demand_prediction(store_id, product_id):
    """Simple demand prediction for a specific product."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    from app.models.product import Product
    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found", 404)

    prediction = ai_service.get_demand_prediction(store_id, product_id)

    # Stock coverage estimate
    avg_weekly = prediction['avg_weekly_sales']
    weeks_of_stock = (product.current_stock / avg_weekly) if avg_weekly > 0 else None

    return success_response(data={
        **prediction,
        'product_name': product.name,
        'current_stock': product.current_stock,
        'weeks_of_stock_remaining': round(weeks_of_stock, 1) if weeks_of_stock else None,
        'insight': (
            f"Predicted demand next week: {prediction['predicted_next_week']} units. "
            f"Current stock will last ~{round(weeks_of_stock, 1)} weeks."
            if weeks_of_stock else
            f"Predicted demand next week: {prediction['predicted_next_week']} units."
        )
    })
