"""
app/models/sale.py — Sale model
"""
from datetime import datetime, timezone
from app import db


class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True)

    # Sale details
    quantity_sold = db.Column(db.Integer, nullable=False, default=1)
    purchase_price_at_sale = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    discount = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)
    profit = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)

    # Payment
    payment_mode = db.Column(
        db.Enum('cash', 'upi', 'card', 'credit', 'cheque', 'other', name='payment_modes'),
        default='cash',
        nullable=False
    )

    # Customer (optional, for quick sales)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(15), nullable=True)

    # Bill reference
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id', ondelete='SET NULL'), nullable=True, index=True)

    # Product name snapshot (in case product is deleted)
    product_name_snapshot = db.Column(db.String(200), nullable=True)

    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'store_id': self.store_id,
            'product_id': self.product_id,
            'product_name': self.product_name_snapshot,
            'quantity_sold': self.quantity_sold,
            'selling_price': float(self.selling_price),
            'total_amount': float(self.total_amount),
            'discount': float(self.discount),
            'profit': float(self.profit),
            'payment_mode': self.payment_mode,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'bill_id': self.bill_id,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Sale #{self.id} store:{self.store_id} ₹{self.total_amount}>'
