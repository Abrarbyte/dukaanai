"""
app/utils/validators.py — Input validation functions
"""
import re
from typing import Any


# ---------------------------------------------------------------------------
# Email & Phone
# ---------------------------------------------------------------------------

def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is required"
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    if len(email) > 150:
        return False, "Email must be under 150 characters"
    return True, email


def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate Indian phone number (10 digits, optional +91 prefix)."""
    if not phone:
        return True, ""  # Phone is optional in most places
    phone = re.sub(r'[\s\-\(\)]', '', str(phone))
    if phone.startswith('+91'):
        phone = phone[3:]
    elif phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]
    if not re.match(r'^[6-9]\d{9}$', phone):
        return False, "Invalid phone number. Enter a valid 10-digit Indian number."
    return True, phone


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength (flexible for development and ease of use)."""
    if not password:
        return False, "Password is required"
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    return True, password


def validate_gst_number(gst: str) -> tuple[bool, str]:
    """Validate Indian GST number format: 15 alphanumeric characters."""
    if not gst:
        return True, ""  # GST is optional
    gst = gst.strip().upper()
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(pattern, gst):
        return False, "Invalid GST number format (e.g., 27AAPFU0939F1ZV)"
    return True, gst


# ---------------------------------------------------------------------------
# Numeric & String
# ---------------------------------------------------------------------------

def validate_positive_number(value: Any, field_name: str = "Value") -> tuple[bool, float, str]:
    """Validate that a value is a non-negative number."""
    try:
        num = float(value)
        if num < 0:
            return False, 0.0, f"{field_name} cannot be negative"
        return True, num, ""
    except (TypeError, ValueError):
        return False, 0.0, f"{field_name} must be a valid number"


def validate_positive_integer(value: Any, field_name: str = "Value") -> tuple[bool, int, str]:
    """Validate that a value is a non-negative integer."""
    try:
        num = int(float(value))
        if num < 0:
            return False, 0, f"{field_name} cannot be negative"
        return True, num, ""
    except (TypeError, ValueError):
        return False, 0, f"{field_name} must be a valid integer"


def validate_required_string(value: Any, field_name: str, max_length: int = 200) -> tuple[bool, str, str]:
    """Validate a required string field."""
    if value is None or str(value).strip() == '':
        return False, "", f"{field_name} is required"
    s = str(value).strip()
    if len(s) > max_length:
        return False, "", f"{field_name} must be under {max_length} characters"
    return True, s, ""


# ---------------------------------------------------------------------------
# Auth Validators
# ---------------------------------------------------------------------------

def validate_signup_data(data: dict) -> tuple[bool, dict, list[str]]:
    """Validate signup payload. Returns (valid, cleaned_data, errors)."""
    errors = []
    cleaned = {}

    # Name
    ok, val, msg = validate_required_string(data.get('name'), 'Name', 100)
    if not ok: errors.append(msg)
    else: cleaned['name'] = val

    # Email
    ok, val = validate_email(data.get('email', ''))
    if not ok: errors.append(val)
    else: cleaned['email'] = val

    # Password
    ok, val = validate_password(data.get('password', ''))
    if not ok: errors.append(val)
    else: cleaned['password'] = val

    # Phone (optional)
    phone_raw = data.get('phone', '')
    if phone_raw:
        ok, val = validate_phone(phone_raw)
        if not ok: errors.append(val)
        else: cleaned['phone'] = val
    else:
        cleaned['phone'] = None

    return len(errors) == 0, cleaned, errors


def validate_store_data(data: dict) -> tuple[bool, dict, list[str]]:
    """Validate store creation/update payload."""
    errors = []
    cleaned = {}

    STORE_TYPES = ['clothing', 'kirana', 'medical', 'electronics', 'general', 'restaurant', 'pharmacy', 'other']

    ok, val, msg = validate_required_string(data.get('store_name'), 'Store name', 150)
    if not ok: errors.append(msg)
    else: cleaned['store_name'] = val

    # Normalize store_type to lowercase for case-insensitive matching
    store_type = str(data.get('store_type', 'general')).strip().lower()
    if store_type not in STORE_TYPES:
        errors.append(f"Invalid store type. Choose from: {', '.join(STORE_TYPES)}")
    else:
        cleaned['store_type'] = store_type

    cleaned['address'] = str(data.get('address', '')).strip() or None
    cleaned['phone'] = data.get('phone') or None
    cleaned['email'] = data.get('email') or None

    gst = data.get('gst_number', '')
    ok, val = validate_gst_number(gst)
    if not ok: errors.append(val)
    else: cleaned['gst_number'] = val or None

    return len(errors) == 0, cleaned, errors


def validate_product_data(data: dict) -> tuple[bool, dict, list[str]]:
    """Validate product creation/update payload."""
    errors = []
    cleaned = {}

    ok, val, msg = validate_required_string(data.get('name'), 'Product name', 200)
    if not ok: errors.append(msg)
    else: cleaned['name'] = val

    ok, val, msg = validate_positive_number(data.get('selling_price', 0), 'Selling price')
    if not ok: errors.append(msg)
    else: cleaned['selling_price'] = val

    ok, val, msg = validate_positive_number(data.get('purchase_price', 0), 'Purchase price')
    if not ok: errors.append(msg)
    else: cleaned['purchase_price'] = val

    stock_val = data.get('current_stock') if 'current_stock' in data else (
        data.get('stock_quantity') if 'stock_quantity' in data else (
            data.get('initial_stock') if 'initial_stock' in data else data.get('stock', 0)
        )
    )
    ok, val, msg = validate_positive_integer(stock_val, 'Current stock')
    if not ok: errors.append(msg)
    else: cleaned['current_stock'] = val

    ok, val, msg = validate_positive_integer(data.get('min_stock_alert', 5), 'Min stock alert')
    if not ok: errors.append(msg)
    else: cleaned['min_stock_alert'] = val

    cleaned['category'] = str(data.get('category', '')).strip() or None
    cleaned['description'] = str(data.get('description', '')).strip() or None
    cleaned['unit'] = str(data.get('unit', 'pcs')).strip()
    cleaned['barcode'] = str(data.get('barcode', '')).strip() or None
    cleaned['sku'] = str(data.get('sku', '')).strip() or None
    cleaned['hsn_code'] = str(data.get('hsn_code', '')).strip() or None

    ok, val, msg = validate_positive_number(data.get('tax_rate', 0), 'Tax rate')
    if not ok: errors.append(msg)
    else: cleaned['tax_rate'] = val

    mrp = data.get('mrp')
    if mrp is not None:
        ok, val, msg = validate_positive_number(mrp, 'MRP')
        if not ok: errors.append(msg)
        else: cleaned['mrp'] = val
    else:
        cleaned['mrp'] = None

    return len(errors) == 0, cleaned, errors
