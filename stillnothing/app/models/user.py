"""
app/models/user.py — User model
"""
from datetime import datetime, timezone
from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    plan = db.Column(
        db.Enum('free', 'pro', 'premium', name='plan_types'),
        default='free',
        nullable=False
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    stores = db.relationship('Store', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    onboarding = db.relationship('Onboarding', backref='user', uselist=False, cascade='all, delete-orphan')

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'plan': self.plan,
            'is_active': self.is_active,
            'is_email_verified': self.is_email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return data

    def get_plan_limits(self) -> dict:
        from app.config import BaseConfig
        return BaseConfig.PLAN_LIMITS.get(self.plan, BaseConfig.PLAN_LIMITS['free'])

    def __repr__(self):
        return f'<User {self.email} [{self.plan}]>'
