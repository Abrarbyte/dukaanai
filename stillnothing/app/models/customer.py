"""
app/models/customer.py — Customer model
"""
from datetime import datetime, timezone
from app import db


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)

    # Identity
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True, index=True)
    email = db.Column(db.String(150), nullable=True)
    address = db.Column(db.Text, nullable=True)
    gstin = db.Column(db.String(15), nullable=True)  # Customer's GST number (B2B)

    # Stats (maintained via triggers / app logic)
    total_purchases = db.Column(db.Numeric(14, 2), default=0.0, nullable=False)
    total_orders = db.Column(db.Integer, default=0, nullable=False)
    udhaar_balance = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # Outstanding credit

    # Metadata
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sales = db.relationship('Sale', backref='customer', lazy='dynamic')
    udhaar_entries = db.relationship('Udhaar', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='customer', lazy='dynamic')

    @property
    def is_repeat_customer(self) -> bool:
        return self.total_orders >= 2

    @property
    def has_outstanding_udhaar(self) -> bool:
        return float(self.udhaar_balance) > 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'gstin': self.gstin,
            'total_purchases': float(self.total_purchases),
            'total_orders': self.total_orders,
            'udhaar_balance': float(self.udhaar_balance),
            'is_repeat_customer': self.is_repeat_customer,
            'has_outstanding_udhaar': self.has_outstanding_udhaar,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Customer {self.name} [store:{self.store_id}]>'
