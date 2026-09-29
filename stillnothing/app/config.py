"""
Shop Manager SaaS — Application Configuration
"""
import os
from datetime import timedelta


class BaseConfig:
    """Shared configuration for all environments."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16 MB

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,       # Recycle connections before MySQL wait_timeout (288s)
        'pool_pre_ping': True,     # Test connection health before use
        'pool_size': 10,
        'max_overflow': 20,
    }

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # App
    APP_NAME = os.environ.get('APP_NAME', 'ShopManager')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

    # Razorpay (Phase 3)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # WhatsApp (Phase 3)
    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL', '')
    WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

    # Plan Limits
    PLAN_LIMITS = {
        'free': {
            'max_stores': 1,
            'max_products': 50,
            'history_days': 30,
            'gst_billing': False,
            'whatsapp_share': False,
            'ai_insights': False,
            'multi_user': False,
        },
        'pro': {
            'max_stores': 1,
            'max_products': None,   # Unlimited
            'history_days': 365,
            'gst_billing': True,
            'whatsapp_share': True,
            'ai_insights': False,
            'multi_user': False,
        },
        'premium': {
            'max_stores': None,     # Unlimited
            'max_products': None,   # Unlimited
            'history_days': None,   # Unlimited
            'gst_billing': True,
            'whatsapp_share': True,
            'ai_insights': True,
            'multi_user': True,
        },
    }


class DevelopmentConfig(BaseConfig):
    """Development configuration — SQLite / MySQL."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///shopmanager_db.db'
    )
    SQLALCHEMY_ECHO = False  # Set to True to log SQL queries
    SQLALCHEMY_ENGINE_OPTIONS = {} if 'sqlite' in SQLALCHEMY_DATABASE_URI else BaseConfig.SQLALCHEMY_ENGINE_OPTIONS


class ProductionConfig(BaseConfig):
    """Production configuration — Railway.app."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 40,
    }


class TestingConfig(BaseConfig):
    """Testing configuration — SQLite in-memory."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    RATELIMIT_ENABLED = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
