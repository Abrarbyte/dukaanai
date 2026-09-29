"""
app/models/product.py — Product model
"""
from datetime import datetime, timezone
from app import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)

    # Pricing
    purchase_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    mrp = db.Column(db.Numeric(12, 2), nullable=True)  # Maximum retail price

    # Inventory
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_alert = db.Column(db.Integer, nullable=False, default=5)
    unit = db.Column(db.String(20), default='pcs', nullable=False)  # pcs, kg, L, etc.

    # Identification
    barcode = db.Column(db.String(100), nullable=True, index=True)
    sku = db.Column(db.String(100), nullable=True)

    # Tax
    hsn_code = db.Column(db.String(20), nullable=True)  # For GST billing
    tax_rate = db.Column(db.Float, default=0.0, nullable=False)  # Product-specific GST

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sales = db.relationship('Sale', backref='product', lazy='dynamic')

    @property
    def profit_margin(self) -> float:
        """Calculate profit margin percentage."""
        if self.selling_price and self.purchase_price and float(self.selling_price) > 0:
            margin = ((float(self.selling_price) - float(self.purchase_price)) / float(self.selling_price)) * 100
            return round(margin, 2)
        return 0.0

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.min_stock_alert

    @property
    def is_out_of_stock(self) -> bool:
        return self.current_stock <= 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'purchase_price': float(self.purchase_price),
            'selling_price': float(self.selling_price),
            'mrp': float(self.mrp) if self.mrp else None,
            'current_stock': self.current_stock,
            'min_stock_alert': self.min_stock_alert,
            'unit': self.unit,
            'barcode': self.barcode,
            'sku': self.sku,
            'hsn_code': self.hsn_code,
            'tax_rate': self.tax_rate,
            'profit_margin': self.profit_margin,
            'is_low_stock': self.is_low_stock,
            'is_out_of_stock': self.is_out_of_stock,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Product {self.name} [store:{self.store_id}]>'
