"""
app/routes/reports.py — Reports and analytics endpoints
GET /api/stores/<store_id>/reports/daily
GET /api/stores/<store_id>/reports/weekly
GET /api/stores/<store_id>/reports/monthly
GET /api/stores/<store_id>/reports/products
GET /api/stores/<store_id>/reports/export
"""
import io
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, send_file
from sqlalchemy import func
from app import db
from app.models.sale import Sale
from app.models.product import Product
from app.models.customer import Customer
from app.models.bill import Bill
from app.utils.auth_helper import token_required, get_current_user, verify_store_access
from app.utils.helpers import (
    success_response, error_response, get_date_range, parse_date_range_from_request
)

reports_bp = Blueprint('reports', __name__)


def _get_sales_summary(store_id: int, start: datetime, end: datetime) -> dict:
    """Core sales aggregation for any date range."""
    result = db.session.query(
        func.count(Sale.id).label('total_orders'),
        func.coalesce(func.sum(Sale.total_amount), 0).label('total_revenue'),
        func.coalesce(func.sum(Sale.profit), 0).label('total_profit'),
        func.coalesce(func.sum(Sale.quantity_sold), 0).label('total_qty_sold'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(start, end)
    ).first()

    # Payment mode breakdown
    payment_data = db.session.query(
        Sale.payment_mode,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('amount'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(start, end)
    ).group_by(Sale.payment_mode).all()

    # Top 10 products
    top_products = db.session.query(
        Sale.product_id,
        Sale.product_name_snapshot,
        func.sum(Sale.quantity_sold).label('total_qty'),
        func.sum(Sale.total_amount).label('total_revenue'),
        func.sum(Sale.profit).label('total_profit'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(start, end),
    ).group_by(
        Sale.product_id, Sale.product_name_snapshot
    ).order_by(
        func.sum(Sale.total_amount).desc()
    ).limit(10).all()

    return {
        'total_orders': int(result.total_orders or 0),
        'total_revenue': float(result.total_revenue or 0),
        'total_profit': float(result.total_profit or 0),
        'total_qty_sold': int(result.total_qty_sold or 0),
        'profit_margin': round(
            float(result.total_profit / result.total_revenue * 100) if result.total_revenue else 0, 2
        ),
        'payment_modes': [
            {'mode': r.payment_mode, 'count': int(r.count), 'amount': float(r.amount or 0)}
            for r in payment_data
        ],
        'top_products': [
            {
                'product_id': r.product_id,
                'product_name': r.product_name_snapshot,
                'total_qty': int(r.total_qty or 0),
                'total_revenue': float(r.total_revenue or 0),
                'total_profit': float(r.total_profit or 0),
            }
            for r in top_products
        ],
    }


@reports_bp.route('/<int:store_id>/reports/summary', methods=['GET'])
@reports_bp.route('/<int:store_id>/reports/daily', methods=['GET'])
@token_required
def daily_report(store_id):
    """Daily report — defaults to today."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD", 400)
    else:
        target_date = datetime.now(timezone.utc)

    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    summary = _get_sales_summary(store_id, day_start, day_end)

    # Hourly breakdown
    hour_col = func.extract('hour', Sale.created_at)
    hourly = db.session.query(
        hour_col.label('hour'),
        func.count(Sale.id).label('orders'),
        func.sum(Sale.total_amount).label('revenue'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(day_start, day_end)
    ).group_by(hour_col).all()

    hourly_data = {r.hour: {'orders': int(r.orders), 'revenue': float(r.revenue or 0)} for r in hourly}
    hourly_chart = [
        {
            'hour': h,
            'hour_label': f"{'0' if h < 10 else ''}{h}:00",
            **hourly_data.get(h, {'orders': 0, 'revenue': 0.0})
        }
        for h in range(24)
    ]

    return success_response(data={
        'period': day_start.strftime('%d %B %Y'),
        'start': day_start.isoformat(),
        'end': day_end.isoformat(),
        **summary,
        'hourly_chart': hourly_chart,
    })


@reports_bp.route('/<int:store_id>/reports/weekly', methods=['GET'])
@token_required
def weekly_report(store_id):
    """Weekly report."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    week_start, now = get_date_range('week')
    summary = _get_sales_summary(store_id, week_start, now)

    # Daily breakdown for the week
    daily_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        if day > now:
            break
        day_end = day + timedelta(days=1)
        day_summary = db.session.query(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.coalesce(func.sum(Sale.profit), 0),
        ).filter(
            Sale.store_id == store_id,
            Sale.created_at.between(day, day_end)
        ).first()
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%A'),
            'orders': int(day_summary[0] or 0),
            'revenue': float(day_summary[1] or 0),
            'profit': float(day_summary[2] or 0),
        })

    return success_response(data={
        'period': f"{week_start.strftime('%d %b')} - {now.strftime('%d %b %Y')}",
        'start': week_start.isoformat(),
        'end': now.isoformat(),
        **summary,
        'daily_breakdown': daily_data,
    })


@reports_bp.route('/<int:store_id>/reports/monthly', methods=['GET'])
@token_required
def monthly_report(store_id):
    """Monthly P&L report."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Support ?month=2024-01 param
    month_str = request.args.get('month')
    if month_str:
        try:
            target = datetime.strptime(month_str, '%Y-%m').replace(tzinfo=timezone.utc)
            month_start = target.replace(day=1)
        except ValueError:
            return error_response("Invalid month format. Use YYYY-MM", 400)
    else:
        month_start, _ = get_date_range('month')

    # End of month
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1)
    month_end = min(month_end, datetime.now(timezone.utc))

    summary = _get_sales_summary(store_id, month_start, month_end)

    # Daily breakdown for the month
    daily_data = []
    current = month_start
    while current < month_end:
        day_end = current + timedelta(days=1)
        day_summary = db.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0),
            func.coalesce(func.sum(Sale.profit), 0),
        ).filter(
            Sale.store_id == store_id,
            Sale.created_at.between(current, day_end)
        ).first()
        daily_data.append({
            'date': current.strftime('%Y-%m-%d'),
            'day': current.strftime('%d'),
            'revenue': float(day_summary[0] or 0),
            'profit': float(day_summary[1] or 0),
        })
        current += timedelta(days=1)

    # Inventory snapshot
    total_products = Product.query.filter_by(store_id=store_id, is_active=True).count()
    low_stock_count = Product.query.filter(
        Product.store_id == store_id,
        Product.is_active == True,
        Product.current_stock <= Product.min_stock_alert
    ).count()
    total_customers = Customer.query.filter_by(store_id=store_id, is_active=True).count()

    return success_response(data={
        'period': month_start.strftime('%B %Y'),
        'start': month_start.isoformat(),
        'end': month_end.isoformat(),
        **summary,
        'daily_chart': daily_data,
        'inventory': {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'total_customers': total_customers,
        }
    })


@reports_bp.route('/<int:store_id>/reports/products', methods=['GET'])
@token_required
def product_report(store_id):
    """Product-wise performance report."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    period = request.args.get('period', 'month')
    start, end = get_date_range(period)

    product_stats = db.session.query(
        Sale.product_id,
        Sale.product_name_snapshot,
        func.sum(Sale.quantity_sold).label('total_qty'),
        func.sum(Sale.total_amount).label('total_revenue'),
        func.sum(Sale.profit).label('total_profit'),
        func.count(Sale.id).label('order_count'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(start, end),
    ).group_by(
        Sale.product_id, Sale.product_name_snapshot
    ).order_by(
        func.sum(Sale.total_amount).desc()
    ).all()

    products = []
    for r in product_stats:
        product = db.session.get(Product, r.product_id) if r.product_id else None
        products.append({
            'product_id': r.product_id,
            'product_name': r.product_name_snapshot,
            'category': product.category if product else None,
            'current_stock': product.current_stock if product else 0,
            'total_qty_sold': int(r.total_qty or 0),
            'total_revenue': float(r.total_revenue or 0),
            'total_profit': float(r.total_profit or 0),
            'order_count': int(r.order_count or 0),
            'profit_margin': round(
                float(r.total_profit / r.total_revenue * 100) if r.total_revenue else 0, 2
            ),
        })

    return success_response(data={
        'period': period,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'products': products,
        'total_products_sold': len(products),
    })


@reports_bp.route('/<int:store_id>/reports/export', methods=['GET'])
@token_required
def export_report(store_id):
    """Export sales data as Excel or PDF."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    export_format = request.args.get('format', 'excel').lower()
    period = request.args.get('period', 'month')
    start, end = get_date_range(period)

    summary = _get_sales_summary(store_id, start, end)

    if export_format == 'pdf':
        from app.services.pdf_service import generate_report_pdf
        pdf_bytes = generate_report_pdf(
            report_data={
                'period': f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}",
                **summary,
                'data': summary['top_products'],
            },
            report_type=period,
            store=store
        )
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"report_{store.store_name}_{period}.pdf"
        )
    else:
        # Excel export
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sales Report"

        # Header
        ws.append(['ShopManager — Sales Report'])
        ws.append([f"Store: {store.store_name}"])
        ws.append([f"Period: {start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"])
        ws.append([])

        # Summary
        ws.append(['SUMMARY', ''])
        ws.append(['Total Orders', summary['total_orders']])
        ws.append(['Total Revenue', f"₹{summary['total_revenue']:,.2f}"])
        ws.append(['Total Profit', f"₹{summary['total_profit']:,.2f}"])
        ws.append(['Profit Margin', f"{summary['profit_margin']}%"])
        ws.append([])

        # Detailed sales
        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.created_at.between(start, end)
        ).order_by(Sale.created_at.desc()).all()

        ws.append(['Date', 'Product', 'Qty', 'Amount', 'Profit', 'Payment Mode', 'Customer'])
        for s in sales:
            ws.append([
                s.created_at.strftime('%d/%m/%Y %H:%M') if s.created_at else '',
                s.product_name_snapshot or '',
                s.quantity_sold,
                float(s.total_amount),
                float(s.profit),
                s.payment_mode,
                s.customer_name or '',
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"report_{store.store_name}_{period}.xlsx"
        )
