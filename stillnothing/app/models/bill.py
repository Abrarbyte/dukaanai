"""
app/models/bill.py — Bill / Invoice model
"""
import json
from datetime import datetime, timezone
from app import db


class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)

    # Invoice number (e.g., INV-00001)
    invoice_number = db.Column(db.String(30), nullable=False, unique=True, index=True)

    # Amounts
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0.0)
    discount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    discount_type = db.Column(db.Enum('flat', 'percent', name='discount_types'), default='flat')
    taxable_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.0)
    cgst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    sgst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    igst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    gst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)  # Total GST
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(14, 2), nullable=False, default=0.0)
    amount_due = db.Column(db.Numeric(14, 2), nullable=False, default=0.0)

    # Payment
    payment_mode = db.Column(
        db.Enum('cash', 'upi', 'card', 'credit', 'cheque', 'split', 'other', name='bill_payment_modes'),
        default='cash',
        nullable=False
    )
    payment_status = db.Column(
        db.Enum('paid', 'partial', 'unpaid', name='payment_statuses'),
        default='paid',
        nullable=False,
        index=True
    )

    # Bill items stored as JSON: [{product_id, name, qty, unit_price, discount, tax_rate, total}]
    bill_items = db.Column(db.JSON, nullable=False, default=list)

    # Customer snapshot (so bill is valid even if customer is deleted)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(15), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    customer_gstin = db.Column(db.String(15), nullable=True)

    # Notes
    note = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)

    # Metadata
    pdf_path = db.Column(db.String(500), nullable=True)
    whatsapp_sent = db.Column(db.Boolean, default=False, nullable=False)
    is_cancelled = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sales = db.relationship('Sale', backref='bill', lazy='dynamic')
    udhaar_entries = db.relationship('Udhaar', backref='bill', lazy='dynamic')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'store_id': self.store_id,
            'customer_id': self.customer_id,
            'invoice_number': self.invoice_number,
            'subtotal': float(self.subtotal),
            'discount': float(self.discount),
            'discount_type': self.discount_type,
            'taxable_amount': float(self.taxable_amount),
            'cgst_amount': float(self.cgst_amount),
            'sgst_amount': float(self.sgst_amount),
            'igst_amount': float(self.igst_amount),
            'gst_amount': float(self.gst_amount),
            'total_amount': float(self.total_amount),
            'amount_paid': float(self.amount_paid),
            'amount_due': float(self.amount_due),
            'payment_mode': self.payment_mode,
            'payment_status': self.payment_status,
            'bill_items': self.bill_items or [],
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'customer_gstin': self.customer_gstin,
            'note': self.note,
            'terms': self.terms,
            'whatsapp_sent': self.whatsapp_sent,
            'is_cancelled': self.is_cancelled,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Bill {self.invoice_number} ₹{self.total_amount}>'
