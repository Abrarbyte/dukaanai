"""
app/services/alert_service.py — Business alerts and notifications
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app import db
from app.models.product import Product
from app.models.customer import Customer
from app.models.sale import Sale


def get_low_stock_alerts(store_id: int) -> list[dict]:
    """
    Return all products at or below their min_stock_alert threshold.
    Sorted by criticality (out of stock first, then by stock level).
    """
    products = (
        Product.query
        .filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.current_stock <= Product.min_stock_alert,
        )
        .order_by(Product.current_stock.asc())
        .all()
    )

    return [
        {
            'product_id': p.id,
            'product_name': p.name,
            'category': p.category,
            'current_stock': p.current_stock,
            'min_stock_alert': p.min_stock_alert,
            'unit': p.unit,
            'is_out_of_stock': p.is_out_of_stock,
            'restock_urgency': 'critical' if p.is_out_of_stock else 'warning',
        }
        for p in products
    ]


def get_udhaar_outstanding(store_id: int, min_balance: float = 0.01) -> list[dict]:
    """
    Return customers with outstanding udhaar balance above min_balance.
    Sorted by balance descending (highest debt first).
    """
    customers = (
        Customer.query
        .filter(
            Customer.store_id == store_id,
            Customer.is_active == True,
            Customer.udhaar_balance >= min_balance,
        )
        .order_by(Customer.udhaar_balance.desc())
        .all()
    )

    total_outstanding = sum(float(c.udhaar_balance) for c in customers)

    return {
        'total_outstanding': total_outstanding,
        'customer_count': len(customers),
        'customers': [
            {
                'customer_id': c.id,
                'name': c.name,
                'phone': c.phone,
                'udhaar_balance': float(c.udhaar_balance),
                'total_orders': c.total_orders,
            }
            for c in customers
        ]
    }


def get_daily_summary(store_id: int) -> dict:
    """
    Generate a comprehensive daily business summary.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    # Today's stats
    today_sales = db.session.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0),
        func.coalesce(func.sum(Sale.profit), 0),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at >= today_start,
    ).first()

    # Yesterday's stats (for comparison)
    yesterday_sales = db.session.query(
        func.coalesce(func.sum(Sale.total_amount), 0),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at.between(yesterday_start, today_start),
    ).scalar() or 0

    today_orders = int(today_sales[0] or 0)
    today_revenue = float(today_sales[1] or 0)
    today_profit = float(today_sales[2] or 0)
    yesterday_revenue = float(yesterday_sales)

    # Revenue change
    revenue_change_pct = (
        ((today_revenue - yesterday_revenue) / yesterday_revenue * 100)
        if yesterday_revenue > 0 else 0
    )

    # Low stock count
    low_stock_count = Product.query.filter(
        Product.store_id == store_id,
        Product.is_active == True,
        Product.current_stock <= Product.min_stock_alert,
    ).count()

    # Outstanding udhaar
    total_udhaar = db.session.query(
        func.coalesce(func.sum(Customer.udhaar_balance), 0)
    ).filter(Customer.store_id == store_id, Customer.is_active == True).scalar() or 0

    # Payment mode breakdown (today)
    payment_breakdown = db.session.query(
        Sale.payment_mode,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('amount'),
    ).filter(
        Sale.store_id == store_id,
        Sale.created_at >= today_start,
    ).group_by(Sale.payment_mode).all()

    return {
        'date': today_start.strftime('%Y-%m-%d'),
        'today': {
            'orders': today_orders,
            'revenue': today_revenue,
            'profit': today_profit,
            'profit_margin': round((today_profit / today_revenue * 100) if today_revenue > 0 else 0, 2),
        },
        'yesterday_revenue': yesterday_revenue,
        'revenue_change_pct': round(revenue_change_pct, 2),
        'alerts': {
            'low_stock_products': low_stock_count,
            'outstanding_udhaar': float(total_udhaar),
        },
        'payment_modes': [
            {
                'mode': r.payment_mode,
                'count': int(r.count or 0),
                'amount': float(r.amount or 0),
            }
            for r in payment_breakdown
        ]
    }
