"""
app/models/store.py — Store model
"""
from datetime import datetime, timezone
from app import db


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    store_name = db.Column(db.String(150), nullable=False)
    store_type = db.Column(
        db.Enum('clothing', 'kirana', 'medical', 'electronics', 'general', 'restaurant', 'pharmacy', 'other',
                name='store_types'),
        default='general',
        nullable=False
    )
    address = db.Column(db.Text, nullable=True)
    gst_number = db.Column(db.String(15), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    currency = db.Column(db.String(3), default='INR', nullable=False)
    tax_rate = db.Column(db.Float, default=18.0, nullable=False)  # GST % (split CGST+SGST)
    invoice_prefix = db.Column(db.String(10), default='INV', nullable=False)
    invoice_counter = db.Column(db.Integer, default=1, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    products = db.relationship('Product', backref='store', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='store', lazy='dynamic', cascade='all, delete-orphan')
    customers = db.relationship('Customer', backref='store', lazy='dynamic', cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='store', lazy='dynamic', cascade='all, delete-orphan')
    udhaar_entries = db.relationship('Udhaar', backref='store', lazy='dynamic', cascade='all, delete-orphan')

    def get_next_invoice_number(self) -> str:
        """Generate next invoice number and increment counter."""
        invoice_num = f"{self.invoice_prefix}-{self.invoice_counter:05d}"
        self.invoice_counter += 1
        return invoice_num

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'store_name': self.store_name,
            'store_type': self.store_type,
            'address': self.address,
            'gst_number': self.gst_number,
            'phone': self.phone,
            'email': self.email,
            'logo_url': self.logo_url,
            'currency': self.currency,
            'tax_rate': self.tax_rate,
            'invoice_prefix': self.invoice_prefix,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Store {self.store_name} [user:{self.user_id}]>'
