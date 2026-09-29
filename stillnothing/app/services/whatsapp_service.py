"""
app/services/whatsapp_service.py — WhatsApp integration scaffold
Phase 1: URL-based WhatsApp deep links (no API required)
Phase 3: WhatsApp Business API (Meta Cloud API)
"""
import urllib.parse
from typing import Optional


def generate_whatsapp_deeplink(phone: str, message: str) -> str:
    """
    Generate a WhatsApp deep link to open chat with pre-filled message.
    Works without any API — uses wa.me universal link.
    """
    # Normalize phone number (remove non-digits, ensure country code)
    phone_clean = ''.join(filter(str.isdigit, phone))
    if phone_clean.startswith('0'):
        phone_clean = phone_clean[1:]
    if not phone_clean.startswith('91') and len(phone_clean) == 10:
        phone_clean = '91' + phone_clean

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{phone_clean}?text={encoded_message}"


def build_bill_message(bill, store) -> str:
    """
    Build a WhatsApp bill message with key details.
    Full bill PDF should be shared separately.
    """
    items_text = ""
    for item in (bill.bill_items or []):
        name = item.get('name', 'Item')
        qty = item.get('quantity', item.get('qty', 1))
        total = float(item.get('total', 0))
        items_text += f"\n  • {name} x{qty} = ₹{total:,.2f}"

    message = (
        f"🧾 *Bill from {store.store_name}*\n"
        f"Invoice: #{bill.invoice_number}\n"
        f"Date: {bill.created_at.strftime('%d %b %Y') if bill.created_at else 'Today'}\n"
        f"\n*Items:*{items_text}\n"
        f"\n{'─' * 25}\n"
        f"Subtotal: ₹{float(bill.subtotal):,.2f}\n"
    )
    if float(bill.discount) > 0:
        message += f"Discount: -₹{float(bill.discount):,.2f}\n"
    if float(bill.gst_amount) > 0:
        message += f"GST: ₹{float(bill.gst_amount):,.2f}\n"
    message += (
        f"*Total: ₹{float(bill.total_amount):,.2f}*\n"
        f"\nPayment: {bill.payment_mode.upper()}\n"
        f"\nThank you for shopping with us! 🙏\n"
    )
    if store.phone:
        message += f"Contact: {store.phone}"
    return message


def get_bill_whatsapp_link(bill, store) -> str:
    """
    Get WhatsApp deep link to share bill with customer.
    Returns URL to open WhatsApp with pre-filled bill message.
    """
    if not bill.customer_phone:
        # Generic link without phone (user must enter manually)
        message = build_bill_message(bill, store)
        encoded = urllib.parse.quote(message)
        return f"https://wa.me/?text={encoded}"

    message = build_bill_message(bill, store)
    return generate_whatsapp_deeplink(bill.customer_phone, message)


def build_payment_reminder_message(customer, store, amount: float) -> str:
    """Build a payment reminder message for udhaar."""
    message = (
        f"🔔 *Payment Reminder from {store.store_name}*\n\n"
        f"Dear {customer.name},\n\n"
        f"You have an outstanding balance of *₹{amount:,.2f}* at {store.store_name}.\n\n"
        f"Please clear the amount at your earliest convenience.\n\n"
        f"Thank you! 🙏"
    )
    if store.phone:
        message += f"\nContact: {store.phone}"
    return message


def get_payment_reminder_link(customer, store) -> Optional[str]:
    """Get WhatsApp link to send payment reminder."""
    if not customer.phone:
        return None
    message = build_payment_reminder_message(customer, store, float(customer.udhaar_balance))
    return generate_whatsapp_deeplink(customer.phone, message)


# ============================================================
# Phase 3 Placeholder: WhatsApp Business API (Meta Cloud API)
# ============================================================

def send_bill_via_whatsapp_api(phone: str, bill, store) -> dict:
    """
    Phase 3: Send bill PDF via WhatsApp Business API.
    Currently returns a placeholder response.
    """
    return {
        "status": "pending",
        "message": "WhatsApp Business API integration coming in Phase 3",
        "fallback_link": get_bill_whatsapp_link(bill, store),
    }


def send_payment_reminder_api(customer, store) -> dict:
    """
    Phase 3: Send automated payment reminder via WhatsApp Business API.
    """
    return {
        "status": "pending",
        "message": "WhatsApp Business API integration coming in Phase 3",
        "fallback_link": get_payment_reminder_link(customer, store),
    }
