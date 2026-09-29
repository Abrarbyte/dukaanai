"""
app/routes/customer.py — Customer management and udhaar tracking
POST /api/stores/<store_id>/customers
GET  /api/stores/<store_id>/customers
GET  /api/stores/<store_id>/customers/<customer_id>
PUT  /api/stores/<store_id>/customers/<customer_id>
POST /api/stores/<store_id>/customers/<customer_id>/udhaar
GET  /api/stores/<store_id>/customers/<customer_id>/udhaar
GET  /api/stores/<store_id>/customers/<customer_id>/reminder-link
"""
from flask import Blueprint, request
from app import db
from app.models.customer import Customer
from app.models.udhaar import Udhaar
from app.utils.auth_helper import token_required, get_current_user, verify_store_access
from app.utils.validators import validate_required_string, validate_phone, validate_gst_number, validate_positive_number
from app.utils.helpers import (
    success_response, error_response, validation_error_response,
    paginate_query, get_pagination_params
)

customer_bp = Blueprint('customer', __name__)


def _validate_customer_data(data: dict) -> tuple[bool, dict, list[str]]:
    errors = []
    cleaned = {}

    ok, val, msg = validate_required_string(data.get('name'), 'Customer name', 100)
    if not ok: errors.append(msg)
    else: cleaned['name'] = val

    phone_raw = data.get('phone', '')
    if phone_raw:
        ok, val = validate_phone(phone_raw)
        if not ok: errors.append(val)
        else: cleaned['phone'] = val
    else:
        cleaned['phone'] = None

    ok, val = validate_gst_number(data.get('gstin', ''))
    if not ok: errors.append(val)
    else: cleaned['gstin'] = val or None

    cleaned['email'] = data.get('email') or None
    cleaned['address'] = str(data.get('address', '')).strip() or None
    cleaned['notes'] = str(data.get('notes', '')).strip() or None

    return len(errors) == 0, cleaned, errors


@customer_bp.route('/<int:store_id>/customers', methods=['POST'])
@token_required
def create_customer(store_id):
    """Add a new customer to the store."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = _validate_customer_data(data)
    if not valid:
        return validation_error_response(errors)

    # Check for duplicate phone in this store
    if cleaned.get('phone'):
        existing = Customer.query.filter_by(
            store_id=store_id, phone=cleaned['phone'], is_active=True
        ).first()
        if existing:
            return error_response(f"A customer with phone {cleaned['phone']} already exists", 409)

    # Opening udhaar balance
    opening_udhaar = float(data.get('opening_udhaar', 0))

    customer = Customer(store_id=store_id, udhaar_balance=opening_udhaar, **cleaned)
    db.session.add(customer)
    db.session.flush()

    # Create opening udhaar entry if applicable
    if opening_udhaar > 0:
        entry = Udhaar(
            customer_id=customer.id,
            store_id=store_id,
            amount=opening_udhaar,
            type='given',
            note='Opening balance'
        )
        db.session.add(entry)

    db.session.commit()
    return success_response(data={'customer': customer.to_dict()}, message="Customer added", status_code=201)


@customer_bp.route('/<int:store_id>/customers', methods=['GET'])
@token_required
def list_customers(store_id):
    """List customers with search and pagination."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    page, per_page = get_pagination_params()
    query = Customer.query.filter_by(store_id=store_id, is_active=True)

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
            )
        )

    # Filter: only with udhaar
    if request.args.get('has_udhaar') == '1':
        query = query.filter(Customer.udhaar_balance > 0)

    # Filter: repeat customers only
    if request.args.get('repeat_only') == '1':
        query = query.filter(Customer.total_orders >= 2)

    sort = request.args.get('sort', 'name')
    sort_map = {
        'name': Customer.name.asc(),
        'purchases': Customer.total_purchases.desc(),
        'udhaar': Customer.udhaar_balance.desc(),
        'orders': Customer.total_orders.desc(),
        'created': Customer.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Customer.name.asc()))

    result = paginate_query(query, page, per_page)

    # Total outstanding udhaar
    total_udhaar = sum(float(c.udhaar_balance) for c in result['items'])

    return success_response(data={
        'customers': [c.to_dict() for c in result['items']],
        'pagination': result['pagination'],
        'total_outstanding_udhaar': total_udhaar,
    })


@customer_bp.route('/<int:store_id>/customers/<int:customer_id>', methods=['GET'])
@token_required
def get_customer(store_id, customer_id):
    """Get customer profile with full purchase history."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()
    if not customer:
        return error_response("Customer not found", 404)

    # Recent purchases
    from app.models.sale import Sale
    recent_sales = (
        Sale.query.filter_by(customer_id=customer_id, store_id=store_id)
        .order_by(Sale.created_at.desc())
        .limit(20)
        .all()
    )

    # Udhaar history
    udhaar_entries = (
        Udhaar.query.filter_by(customer_id=customer_id, store_id=store_id)
        .order_by(Udhaar.created_at.desc())
        .limit(20)
        .all()
    )

    return success_response(data={
        'customer': customer.to_dict(),
        'recent_purchases': [s.to_dict() for s in recent_sales],
        'udhaar_history': [u.to_dict() for u in udhaar_entries],
    })


@customer_bp.route('/<int:store_id>/customers/<int:customer_id>', methods=['PUT'])
@token_required
def update_customer(store_id, customer_id):
    """Update customer details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()
    if not customer:
        return error_response("Customer not found", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = _validate_customer_data(data)
    if not valid:
        return validation_error_response(errors)

    for field, value in cleaned.items():
        setattr(customer, field, value)

    db.session.commit()
    return success_response(data={'customer': customer.to_dict()}, message="Customer updated")


@customer_bp.route('/<int:store_id>/customers/<int:customer_id>/udhaar', methods=['POST'])
@token_required
def add_udhaar(store_id, customer_id):
    """
    Add an udhaar entry (given or received).
    type: 'given' (credit extended) or 'received' (payment received)
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()
    if not customer:
        return error_response("Customer not found", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    ok, amount, msg = validate_positive_number(data.get('amount', 0), 'Amount')
    if not ok or amount <= 0:
        return error_response("Amount must be a positive number", 400)

    udhaar_type = data.get('type', 'given')
    if udhaar_type not in ['given', 'received']:
        return error_response("Type must be 'given' or 'received'", 400)

    # If receiving payment, ensure it doesn't exceed balance
    if udhaar_type == 'received' and amount > float(customer.udhaar_balance):
        return error_response(
            f"Payment amount (₹{amount:,.2f}) exceeds outstanding balance (₹{float(customer.udhaar_balance):,.2f})",
            400
        )

    entry = Udhaar(
        customer_id=customer_id,
        store_id=store_id,
        amount=amount,
        type=udhaar_type,
        note=data.get('note', ''),
        payment_mode=data.get('payment_mode'),
    )
    db.session.add(entry)

    # Update customer balance
    if udhaar_type == 'given':
        customer.udhaar_balance = float(customer.udhaar_balance) + amount
    else:
        customer.udhaar_balance = float(customer.udhaar_balance) - amount

    db.session.commit()

    return success_response(
        data={
            'udhaar_entry': entry.to_dict(),
            'new_balance': float(customer.udhaar_balance),
        },
        message=f"₹{amount:,.2f} {'credit recorded' if udhaar_type == 'given' else 'payment received'}",
        status_code=201
    )


@customer_bp.route('/<int:store_id>/customers/<int:customer_id>/udhaar', methods=['GET'])
@token_required
def get_udhaar(store_id, customer_id):
    """Get full udhaar ledger for a customer."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()
    if not customer:
        return error_response("Customer not found", 404)

    page, per_page = get_pagination_params()
    query = Udhaar.query.filter_by(customer_id=customer_id, store_id=store_id).order_by(Udhaar.created_at.desc())
    result = paginate_query(query, page, per_page)

    return success_response(data={
        'customer': customer.to_dict(),
        'udhaar_entries': [u.to_dict() for u in result['items']],
        'pagination': result['pagination'],
        'current_balance': float(customer.udhaar_balance),
    })


@customer_bp.route('/<int:store_id>/customers/<int:customer_id>/reminder-link', methods=['GET'])
@token_required
def get_reminder_link(store_id, customer_id):
    """Get WhatsApp payment reminder link for customer."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()
    if not customer:
        return error_response("Customer not found", 404)

    from app.services.whatsapp_service import get_payment_reminder_link
    link = get_payment_reminder_link(customer, store)

    if not link:
        return error_response("Customer has no phone number. Add a phone number to send reminders.", 400)

    # Mark reminder sent
    from datetime import datetime, timezone
    latest_udhaar = Udhaar.query.filter_by(
        customer_id=customer_id, store_id=store_id
    ).order_by(Udhaar.created_at.desc()).first()
    if latest_udhaar:
        latest_udhaar.reminder_sent = True
        latest_udhaar.reminder_sent_at = datetime.now(timezone.utc)
        db.session.commit()

    return success_response(data={
        'whatsapp_link': link,
        'customer_name': customer.name,
        'outstanding_balance': float(customer.udhaar_balance),
    })
