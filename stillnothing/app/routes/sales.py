"""
app/routes/sales.py — Sales recording and retrieval
POST /api/stores/<store_id>/sales
GET  /api/stores/<store_id>/sales
GET  /api/stores/<store_id>/sales/<sale_id>
GET  /api/stores/<store_id>/sales/today
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request
from sqlalchemy import func
from app import db
from app.models.sale import Sale
from app.models.product import Product
from app.models.customer import Customer
from app.utils.auth_helper import token_required, get_current_user, verify_store_access
from app.utils.validators import validate_positive_number, validate_positive_integer
from app.utils.helpers import (
    success_response, error_response, validation_error_response,
    paginate_query, get_pagination_params, get_date_range, parse_date_range_from_request
)

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/<int:store_id>/sales', methods=['POST'])
@token_required
def record_sale(store_id):
    """
    Record a new sale. Auto-deducts stock and calculates profit.
    Required: product_id, quantity_sold
    Optional: selling_price (overrides product price), payment_mode, customer_id/name/phone
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    errors = []

    # Get product
    product_id = data.get('product_id')
    if not product_id:
        return error_response("product_id is required", 400)

    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found in this store", 404)

    # Quantity
    ok, qty, msg = validate_positive_integer(data.get('quantity_sold', 1), 'Quantity')
    if not ok:
        errors.append(msg)
    if qty <= 0:
        errors.append("Quantity must be at least 1")

    # Selling price (use product default if not specified)
    if 'selling_price' in data:
        ok, selling_price, msg = validate_positive_number(data['selling_price'], 'Selling price')
        if not ok:
            errors.append(msg)
    else:
        selling_price = float(product.selling_price)

    if errors:
        return validation_error_response(errors)

    # Stock check
    if product.current_stock < qty:
        return error_response(
            f"Insufficient stock. Available: {product.current_stock} {product.unit}",
            400
        )

    # Calculate amounts
    discount = float(data.get('discount', 0))
    total_amount = (selling_price * qty) - discount
    profit = (selling_price - float(product.purchase_price)) * qty - discount
    payment_mode = data.get('payment_mode', 'cash')

    # Validate payment mode
    valid_modes = ['cash', 'upi', 'card', 'credit', 'cheque', 'other']
    if payment_mode not in valid_modes:
        payment_mode = 'cash'

    # Customer linking (optional)
    customer_id = data.get('customer_id')
    customer_name = data.get('customer_name') or None
    customer_phone = data.get('customer_phone') or None

    if customer_id:
        customer = Customer.query.filter_by(id=customer_id, store_id=store_id).first()
        if customer:
            customer_name = customer.name
            customer_phone = customer.phone
            # Update customer stats
            customer.total_purchases = float(customer.total_purchases) + total_amount
            customer.total_orders += 1
            # If credit payment, add to udhaar
            if payment_mode == 'credit':
                customer.udhaar_balance = float(customer.udhaar_balance) + total_amount

    # Deduct stock
    product.current_stock -= qty

    # Create sale
    sale = Sale(
        store_id=store_id,
        product_id=product.id,
        product_name_snapshot=product.name,
        quantity_sold=qty,
        purchase_price_at_sale=float(product.purchase_price),
        selling_price=selling_price,
        discount=discount,
        total_amount=total_amount,
        profit=profit,
        payment_mode=payment_mode,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        note=data.get('note'),
    )
    db.session.add(sale)

    # Update onboarding
    if user.onboarding and not user.onboarding.first_sale_recorded:
        user.onboarding.first_sale_recorded = True

    db.session.commit()

    return success_response(
        data={
            'sale': sale.to_dict(),
            'product': product.to_dict(),
        },
        message="Sale recorded successfully",
        status_code=201
    )


@sales_bp.route('/<int:store_id>/sales', methods=['GET'])
@token_required
def list_sales(store_id):
    """
    List sales with date filtering and pagination.
    Query params: page, per_page, period (today/week/month/year), start_date, end_date, payment_mode
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Check plan history limit
    limits = user.get_plan_limits()
    history_days = limits.get('history_days')

    page, per_page = get_pagination_params()
    query = Sale.query.filter_by(store_id=store_id)

    # Date range
    period = request.args.get('period')
    start_date, end_date = parse_date_range_from_request()

    if start_date and end_date:
        query = query.filter(Sale.created_at.between(start_date, end_date))
    elif period:
        start, end = get_date_range(period)
        query = query.filter(Sale.created_at.between(start, end))
    elif history_days:
        since = datetime.now(timezone.utc) - timedelta(days=history_days)
        query = query.filter(Sale.created_at >= since)

    # Filter by payment mode
    payment_mode = request.args.get('payment_mode')
    if payment_mode:
        query = query.filter(Sale.payment_mode == payment_mode)

    # Filter by customer
    customer_id = request.args.get('customer_id')
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)

    query = query.order_by(Sale.created_at.desc())
    result = paginate_query(query, page, per_page)

    # Summary for the current filter
    filtered_query = Sale.query.filter_by(store_id=store_id)
    if start_date and end_date:
        filtered_query = filtered_query.filter(Sale.created_at.between(start_date, end_date))

    summary = db.session.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0),
        func.coalesce(func.sum(Sale.profit), 0),
    ).filter(Sale.store_id == store_id).first()

    return success_response(data={
        'sales': [s.to_dict() for s in result['items']],
        'pagination': result['pagination'],
        'summary': {
            'total_orders': int(summary[0] or 0),
            'total_revenue': float(summary[1] or 0),
            'total_profit': float(summary[2] or 0),
        }
    })


@sales_bp.route('/<int:store_id>/sales/today', methods=['GET'])
@token_required
def today_sales(store_id):
    """Get today's sales summary."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    from app.services.alert_service import get_daily_summary
    summary = get_daily_summary(store_id)

    today_start, now = get_date_range('today')
    recent_sales = (
        Sale.query
        .filter(Sale.store_id == store_id, Sale.created_at >= today_start)
        .order_by(Sale.created_at.desc())
        .limit(50)
        .all()
    )

    return success_response(data={
        **summary,
        'sales': [s.to_dict() for s in recent_sales],
    })


@sales_bp.route('/<int:store_id>/sales/<int:sale_id>', methods=['GET'])
@token_required
def get_sale(store_id, sale_id):
    """Get a specific sale's details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    sale = Sale.query.filter_by(id=sale_id, store_id=store_id).first()
    if not sale:
        return error_response("Sale not found", 404)

    return success_response(data={'sale': sale.to_dict()})
