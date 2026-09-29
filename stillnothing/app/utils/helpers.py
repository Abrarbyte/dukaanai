"""
app/utils/helpers.py — Shared utility functions
"""
from __future__ import annotations
import io
import math
from datetime import datetime, date, timezone, timedelta
from typing import Any
from flask import jsonify, request
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


# ---------------------------------------------------------------------------
# Response Helpers
# ---------------------------------------------------------------------------

def success_response(data: Any = None, message: str = "Success", status_code: int = 200, **kwargs):
    """Standard JSON success response."""
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload), status_code


def error_response(message: str = "An error occurred", status_code: int = 400, **kwargs):
    """Standard JSON error response."""
    payload = {"success": False, "message": message}
    payload.update(kwargs)
    return jsonify(payload), status_code


def validation_error_response(errors: list[str]):
    """Standard validation error response."""
    return jsonify({
        "success": False,
        "message": "Validation failed",
        "errors": errors
    }), 422


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100) -> dict:
    """
    Paginate a SQLAlchemy query and return metadata + items.
    Usage: result = paginate_query(Product.query.filter_by(store_id=1))
    """
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }


def get_pagination_params() -> tuple[int, int]:
    """Extract page & per_page from request query string."""
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
    except (TypeError, ValueError):
        per_page = 20
    return page, per_page


# ---------------------------------------------------------------------------
# Date Helpers
# ---------------------------------------------------------------------------

def get_date_range(period: str = 'today') -> tuple[datetime, datetime]:
    """
    Get start/end datetime for common periods.
    period: 'today', 'yesterday', 'week', 'month', 'year', or 'custom'
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == 'today':
        return today_start, now
    elif period == 'yesterday':
        yesterday = today_start - timedelta(days=1)
        return yesterday, today_start
    elif period == 'week':
        week_start = today_start - timedelta(days=today_start.weekday())
        return week_start, now
    elif period == 'month':
        month_start = today_start.replace(day=1)
        return month_start, now
    elif period == 'year':
        year_start = today_start.replace(month=1, day=1)
        return year_start, now
    else:
        return today_start, now


def parse_date_range_from_request() -> tuple[datetime | None, datetime | None]:
    """Parse start_date and end_date from request query params."""
    try:
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        start = datetime.fromisoformat(start_str) if start_str else None
        end = datetime.fromisoformat(end_str) if end_str else None
        return start, end
    except (ValueError, TypeError):
        return None, None


def ist_now() -> datetime:
    """Return current time in IST (UTC+5:30)."""
    ist_offset = timedelta(hours=5, minutes=30)
    return datetime.now(timezone.utc).astimezone(timezone(ist_offset))


# ---------------------------------------------------------------------------
# Excel Helpers
# ---------------------------------------------------------------------------

PRODUCT_IMPORT_COLUMNS = [
    'Name', 'Category', 'Purchase Price', 'Selling Price',
    'Current Stock', 'Min Stock Alert', 'Unit', 'Barcode', 'HSN Code', 'Tax Rate %'
]


def generate_excel_template() -> io.BytesIO:
    """Generate a downloadable Excel template for product import."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Header row
    ws.append(PRODUCT_IMPORT_COLUMNS)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Sample row
    ws.append(['Sample Product', 'Electronics', 500, 799, 50, 5, 'pcs', '', '', 18])

    # Auto-width columns
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col) + 4
        ws.column_dimensions[col[0].column_letter].width = min(max_len, 30)

    ws.row_dimensions[1].height = 25

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def parse_excel_products(file_stream) -> tuple[list[dict], list[str]]:
    """
    Parse uploaded Excel file and return list of product dicts.
    Returns (products: list[dict], errors: list[str])
    """
    products = []
    errors = []

    try:
        wb = openpyxl.load_workbook(file_stream, data_only=True)
        ws = wb.active
    except Exception as e:
        return [], [f"Failed to read Excel file: {str(e)}"]

    # Validate headers
    headers = [str(cell.value or '').strip() for cell in ws[1]]
    for required_col in ['Name', 'Selling Price']:
        if required_col not in headers:
            errors.append(f"Missing required column: '{required_col}'")
    if errors:
        return [], errors

    col_index = {col: idx for idx, col in enumerate(headers)}

    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):  # Skip empty rows
            continue

        def get_val(col_name, default=None):
            idx = col_index.get(col_name)
            if idx is None:
                return default
            val = row[idx]
            return val if val is not None else default

        name = str(get_val('Name', '')).strip()
        if not name:
            errors.append(f"Row {row_num}: Product name is required")
            continue

        try:
            product = {
                'name': name,
                'category': str(get_val('Category', '')).strip() or None,
                'purchase_price': float(get_val('Purchase Price', 0) or 0),
                'selling_price': float(get_val('Selling Price', 0) or 0),
                'current_stock': int(float(get_val('Current Stock', 0) or 0)),
                'min_stock_alert': int(float(get_val('Min Stock Alert', 5) or 5)),
                'unit': str(get_val('Unit', 'pcs') or 'pcs').strip(),
                'barcode': str(get_val('Barcode', '') or '').strip() or None,
                'hsn_code': str(get_val('HSN Code', '') or '').strip() or None,
                'tax_rate': float(get_val('Tax Rate %', 0) or 0),
            }
            if product['selling_price'] <= 0:
                errors.append(f"Row {row_num}: Selling price must be greater than 0")
                continue
            products.append(product)
        except (ValueError, TypeError) as e:
            errors.append(f"Row {row_num}: Invalid data — {str(e)}")

    return products, errors


# ---------------------------------------------------------------------------
# Number Formatting
# ---------------------------------------------------------------------------

def format_currency(amount: float, currency: str = 'INR') -> str:
    """Format amount as currency string."""
    if currency == 'INR':
        return f"₹{amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def round_half_up(number: float, decimals: int = 2) -> float:
    """Round to given decimal places."""
    multiplier = 10 ** decimals
    return math.floor(number * multiplier + 0.5) / multiplier
