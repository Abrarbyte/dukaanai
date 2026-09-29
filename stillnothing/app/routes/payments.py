"""
app/routes/payments.py — Payment integration endpoints
POST /api/payments/create-order
POST /api/payments/verify
GET  /api/payments/upi-link
GET  /api/payments/qr/<store_id>
"""
import io
from flask import Blueprint, request, send_file
from app.utils.auth_helper import token_required, get_current_user, verify_store_access
from app.utils.helpers import success_response, error_response
from app.services import payment_service

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/create-order', methods=['POST'])
@token_required
def create_order():
    """
    Create a Razorpay payment order.
    Phase 1: Returns placeholder. Phase 3: Full Razorpay integration.
    """
    data = request.get_json(silent=True) or {}
    amount = float(data.get('amount', 0))

    if amount <= 0:
        return error_response("Amount must be greater than 0", 400)

    result = payment_service.create_razorpay_order(
        amount=amount,
        currency=data.get('currency', 'INR'),
        receipt=data.get('receipt'),
        notes=data.get('notes', {}),
    )
    return success_response(data=result, message="Order created")


@payments_bp.route('/verify', methods=['POST'])
@token_required
def verify_payment():
    """Verify Razorpay payment signature (Phase 3)."""
    data = request.get_json(silent=True) or {}
    order_id = data.get('razorpay_order_id', '')
    payment_id = data.get('razorpay_payment_id', '')
    signature = data.get('razorpay_signature', '')

    is_valid = payment_service.verify_razorpay_payment(order_id, payment_id, signature)
    if is_valid:
        return success_response(message="Payment verified successfully")
    return error_response("Payment verification failed", 400)


@payments_bp.route('/upi-link', methods=['GET'])
@token_required
def upi_link():
    """
    Generate a UPI deep link for a store.
    Query params: store_id, amount, note
    """
    user = get_current_user()
    store_id = request.args.get('store_id', type=int)
    if not store_id:
        return error_response("store_id is required", 400)

    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    amount = request.args.get('amount', type=float)
    note = request.args.get('note', 'Payment')

    # Phase 1: Use store phone as UPI ID placeholder
    # Phase 3: Use dedicated store.upi_id field
    if not store.phone:
        return error_response("Store must have a phone number to generate UPI link", 400)

    upi_id = f"{store.phone}@upi"
    link = payment_service.generate_upi_link(upi_id, store.store_name, amount, note)

    return success_response(data={
        'upi_link': link,
        'upi_id': upi_id,
        'store_name': store.store_name,
        'amount': amount,
        'note': note,
    })


@payments_bp.route('/qr/<int:store_id>', methods=['GET'])
@token_required
def payment_qr(store_id):
    """Generate a UPI QR code image for the store."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    amount = request.args.get('amount', type=float)
    note = request.args.get('note', f"Payment to {store.store_name}")

    qr_bytes = payment_service.generate_payment_qr_for_store(store, amount, note)
    if not qr_bytes:
        return error_response("Store must have a phone number to generate payment QR code", 400)

    return send_file(
        io.BytesIO(qr_bytes),
        mimetype='image/png',
        as_attachment=False,
        download_name=f"payment_qr_{store.store_name}.png"
    )


@payments_bp.route('/plans', methods=['GET'])
def get_plans():
    """Return subscription plan details (public endpoint)."""
    from app.config import BaseConfig
    plans = [
        {
            'id': 'free',
            'name': 'Free',
            'price': 0,
            'currency': 'INR',
            'billing': 'forever',
            'features': [
                '1 Store',
                '50 Products',
                'Basic Billing',
                '30 Days History',
                'Cash/UPI/Card Sales',
            ],
            'limits': BaseConfig.PLAN_LIMITS['free'],
        },
        {
            'id': 'pro',
            'name': 'Pro',
            'price': 199,
            'currency': 'INR',
            'billing': 'monthly',
            'features': [
                '1 Store',
                'Unlimited Products',
                'GST Billing (CGST + SGST)',
                'WhatsApp Bill Share',
                'Full Reports (Daily/Weekly/Monthly)',
                '1 Year History',
                'Excel Export',
            ],
            'limits': BaseConfig.PLAN_LIMITS['pro'],
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'price': 399,
            'currency': 'INR',
            'billing': 'monthly',
            'features': [
                'Unlimited Stores',
                'All Pro Features',
                'AI Insights Engine',
                'Multi-User Access',
                'Priority Support',
                'Unlimited History',
                'Demand Prediction',
            ],
            'limits': BaseConfig.PLAN_LIMITS['premium'],
        },
    ]
    return success_response(data={'plans': plans})
