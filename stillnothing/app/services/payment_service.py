"""
app/services/payment_service.py — Payment integration scaffold
Phase 1: UPI deep links and QR code generation (no API key needed)
Phase 3: Full Razorpay integration
"""
import io
import hashlib
import hmac
import urllib.parse
from typing import Optional
import qrcode
from qrcode.image.pure import PyPNGImage
from flask import current_app


# ---------------------------------------------------------------------------
# UPI Deep Links (Phase 1 — works without any API key)
# ---------------------------------------------------------------------------

def generate_upi_link(
    upi_id: str,
    name: str,
    amount: Optional[float] = None,
    note: str = "Payment",
    currency: str = "INR"
) -> str:
    """
    Generate a UPI payment deep link (works on all UPI apps).
    Format: upi://pay?pa=<upi_id>&pn=<name>&am=<amount>&tn=<note>&cu=INR
    """
    params = {
        'pa': upi_id,
        'pn': name,
        'tn': note,
        'cu': currency,
    }
    if amount and amount > 0:
        params['am'] = f"{amount:.2f}"

    query = urllib.parse.urlencode(params)
    return f"upi://pay?{query}"


def generate_upi_qr_code(
    upi_id: str,
    name: str,
    amount: Optional[float] = None,
    note: str = "Payment"
) -> bytes:
    """
    Generate a QR code image (PNG bytes) for UPI payments.
    Returns PNG bytes that can be sent directly as a file response.
    """
    upi_url = generate_upi_link(upi_id, name, amount, note)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1E40AF", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


def generate_payment_qr_for_store(store, amount: Optional[float] = None, note: str = "Payment") -> Optional[bytes]:
    """
    Generate payment QR for a store (if store has UPI configured).
    Currently uses GST number as placeholder; Phase 3 will store UPI ID in store settings.
    """
    # Phase 3: Use store.upi_id field
    # For now, if store has a phone, generate a generic QR
    if not store.phone:
        return None
    # Placeholder UPI ID using phone
    upi_id = f"{store.phone}@upi"
    return generate_upi_qr_code(upi_id, store.store_name, amount, note)


# ---------------------------------------------------------------------------
# Razorpay Integration (Phase 3 Scaffold)
# ---------------------------------------------------------------------------

def create_razorpay_order(amount: float, currency: str = 'INR', receipt: str = None, notes: dict = None) -> dict:
    """
    Phase 3: Create a Razorpay payment order.
    Returns placeholder response in Phase 1.
    """
    return {
        "status": "pending_phase3",
        "message": "Razorpay integration will be implemented in Phase 3",
        "amount": amount,
        "currency": currency,
        "receipt": receipt,
    }


def verify_razorpay_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """
    Phase 3: Verify Razorpay payment signature.
    Returns False in Phase 1 (not implemented).
    """
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', '')
    if not key_secret or key_secret == 'placeholder_secret':
        return False

    # Razorpay signature verification
    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        key_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, razorpay_signature)


def get_razorpay_key_id() -> str:
    """Return the Razorpay Key ID for frontend use."""
    return current_app.config.get('RAZORPAY_KEY_ID', '')
