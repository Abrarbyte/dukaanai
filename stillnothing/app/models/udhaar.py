"""
app/models/udhaar.py — Udhaar (Credit) model
"""
from datetime import datetime, timezone
from app import db


class Udhaar(db.Model):
    __tablename__ = 'udhaar'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    type = db.Column(
        db.Enum('given', 'received', name='udhaar_types'),
        nullable=False,
        default='given'
    )
    # 'given'    = customer took goods on credit (balance increases)
    # 'received' = customer paid back (balance decreases)

    note = db.Column(db.Text, nullable=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id', ondelete='SET NULL'), nullable=True)
    payment_mode = db.Column(db.String(20), nullable=True)  # For partial payments
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'store_id': self.store_id,
            'amount': float(self.amount),
            'type': self.type,
            'note': self.note,
            'bill_id': self.bill_id,
            'payment_mode': self.payment_mode,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Udhaar {self.type} ₹{self.amount} customer:{self.customer_id}>'
