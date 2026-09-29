"""
app/services/ai_service.py — Rule-based AI insights engine (Phase 1)
Phase 3 will enhance this with ML / LLM-based predictions.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app import db
from app.models.sale import Sale
from app.models.product import Product


def get_fast_selling_products(store_id: int, days: int = 7, limit: int = 10) -> list[dict]:
    """
    Return top selling products by quantity in the last N days.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
        db.session.query(
            Sale.product_id,
            Sale.product_name_snapshot.label('product_name'),
            func.sum(Sale.quantity_sold).label('total_qty'),
            func.sum(Sale.total_amount).label('total_revenue'),
            func.count(Sale.id).label('order_count'),
        )
        .filter(Sale.store_id == store_id, Sale.created_at >= since)
        .group_by(Sale.product_id, Sale.product_name_snapshot)
        .order_by(func.sum(Sale.quantity_sold).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            'product_id': r.product_id,
            'product_name': r.product_name,
            'total_qty_sold': int(r.total_qty or 0),
            'total_revenue': float(r.total_revenue or 0),
            'order_count': int(r.order_count or 0),
            'period_days': days,
        }
        for r in results
    ]


def get_dead_stock(store_id: int, days: int = 30, limit: int = 20) -> list[dict]:
    """
    Return products that have NOT been sold in the last N days.
    Includes products never sold.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Get product IDs that HAVE been sold recently
    sold_recently = (
        db.session.query(Sale.product_id)
        .filter(Sale.store_id == store_id, Sale.created_at >= since)
        .distinct()
        .subquery()
    )

    dead_products = (
        Product.query
        .filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.current_stock > 0,
            ~Product.id.in_(db.session.query(sold_recently))
        )
        .order_by(Product.current_stock.desc())
        .limit(limit)
        .all()
    )

    result = []
    for p in dead_products:
        stock_value = float(p.purchase_price) * p.current_stock
        result.append({
            'product_id': p.id,
            'product_name': p.name,
            'category': p.category,
            'current_stock': p.current_stock,
            'stock_value': stock_value,
            'selling_price': float(p.selling_price),
            'days_no_sale': days,
        })
    return result


def get_restock_suggestions(store_id: int, limit: int = 15) -> list[dict]:
    """
    Suggest products to restock based on:
    - Low stock (current_stock <= min_stock_alert)
    - High recent sales velocity
    """
    since_7_days = datetime.now(timezone.utc) - timedelta(days=7)

    # Recent sales velocity per product
    velocity = (
        db.session.query(
            Sale.product_id,
            func.sum(Sale.quantity_sold).label('sold_7d'),
        )
        .filter(Sale.store_id == store_id, Sale.created_at >= since_7_days)
        .group_by(Sale.product_id)
        .subquery()
    )

    low_stock_products = (
        db.session.query(Product, velocity.c.sold_7d)
        .outerjoin(velocity, Product.id == velocity.c.product_id)
        .filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.current_stock <= Product.min_stock_alert,
        )
        .order_by(
            (velocity.c.sold_7d).desc().nulls_last(),
            Product.current_stock.asc()
        )
        .limit(limit)
        .all()
    )

    result = []
    for p, sold_7d in low_stock_products:
        sold = int(sold_7d or 0)
        # Suggest restocking 2 weeks' worth of supply
        suggested_qty = max(p.min_stock_alert * 3, sold * 2) - p.current_stock
        result.append({
            'product_id': p.id,
            'product_name': p.name,
            'category': p.category,
            'current_stock': p.current_stock,
            'min_stock_alert': p.min_stock_alert,
            'sold_last_7_days': sold,
            'suggested_restock_qty': max(0, suggested_qty),
            'restock_cost_estimate': float(p.purchase_price) * max(0, suggested_qty),
            'is_out_of_stock': p.is_out_of_stock,
        })
    return result


def get_best_margin_products(store_id: int, limit: int = 10) -> list[dict]:
    """
    Return products with the highest profit margin.
    """
    products = (
        Product.query
        .filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.selling_price > 0,
        )
        .all()
    )

    # Sort by profit margin descending
    products.sort(key=lambda p: p.profit_margin, reverse=True)

    return [
        {
            'product_id': p.id,
            'product_name': p.name,
            'category': p.category,
            'purchase_price': float(p.purchase_price),
            'selling_price': float(p.selling_price),
            'profit_margin': p.profit_margin,
            'profit_per_unit': float(p.selling_price) - float(p.purchase_price),
        }
        for p in products[:limit]
    ]


def get_peak_sales_hours(store_id: int, days: int = 30) -> list[dict]:
    """
    Return hourly sales distribution to identify peak business hours.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
        db.session.query(
            func.hour(Sale.created_at).label('hour'),
            func.count(Sale.id).label('order_count'),
            func.sum(Sale.total_amount).label('total_revenue'),
        )
        .filter(Sale.store_id == store_id, Sale.created_at >= since)
        .group_by(func.hour(Sale.created_at))
        .order_by(func.hour(Sale.created_at))
        .all()
    )

    # Build a full 24-hour map
    hour_map = {r.hour: {'order_count': int(r.order_count or 0),
                          'total_revenue': float(r.total_revenue or 0)} for r in results}

    peak_hours = []
    for h in range(24):
        data = hour_map.get(h, {'order_count': 0, 'total_revenue': 0.0})
        hour_label = f"{'0' if h < 10 else ''}{h}:00"
        peak_hours.append({
            'hour': h,
            'hour_label': hour_label,
            'order_count': data['order_count'],
            'total_revenue': data['total_revenue'],
        })

    return peak_hours


def get_demand_prediction(store_id: int, product_id: int) -> dict:
    """
    Simple demand prediction based on rolling average.
    Phase 3 will replace this with ML models.
    """
    # Last 4 weeks data
    predictions = []
    for week in range(4, 0, -1):
        week_start = datetime.now(timezone.utc) - timedelta(weeks=week)
        week_end = datetime.now(timezone.utc) - timedelta(weeks=week - 1)
        qty = db.session.query(func.sum(Sale.quantity_sold)).filter(
            Sale.store_id == store_id,
            Sale.product_id == product_id,
            Sale.created_at.between(week_start, week_end)
        ).scalar() or 0
        predictions.append(int(qty))

    avg_weekly = sum(predictions) / len(predictions) if predictions else 0
    predicted_next_week = round(avg_weekly * 1.05)  # Simple 5% growth assumption

    return {
        'product_id': product_id,
        'weekly_sales_history': predictions,
        'avg_weekly_sales': round(avg_weekly, 1),
        'predicted_next_week': predicted_next_week,
        'confidence': 'low',  # Phase 3 will have proper confidence scores
        'method': 'rolling_average',
    }
