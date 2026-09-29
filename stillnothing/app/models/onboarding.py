"""
app/models/onboarding.py — Onboarding state model
"""
from datetime import datetime, timezone
from app import db


class Onboarding(db.Model):
    __tablename__ = 'onboarding'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Tracks onboarding wizard progress
    step_completed = db.Column(db.Integer, default=0, nullable=False)
    # Step 0: Not started
    # Step 1: Store details created
    # Step 2: Products added (manual/Excel/barcode)
    # Step 3: Opening stock entered
    # Step 4: Dashboard ready (fully onboarded)

    is_onboarded = db.Column(db.Boolean, default=False, nullable=False)
    skipped = db.Column(db.Boolean, default=False, nullable=False)

    # Detailed step flags
    store_created = db.Column(db.Boolean, default=False, nullable=False)
    products_added = db.Column(db.Boolean, default=False, nullable=False)
    stock_entered = db.Column(db.Boolean, default=False, nullable=False)
    first_sale_recorded = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'step_completed': self.step_completed,
            'is_onboarded': self.is_onboarded,
            'skipped': self.skipped,
            'store_created': self.store_created,
            'products_added': self.products_added,
            'stock_entered': self.stock_entered,
            'first_sale_recorded': self.first_sale_recorded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Onboarding user:{self.user_id} step:{self.step_completed} done:{self.is_onboarded}>'
