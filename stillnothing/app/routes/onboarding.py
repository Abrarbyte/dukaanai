"""
app/routes/onboarding.py — Onboarding wizard endpoints
GET  /api/onboarding/status
PUT  /api/onboarding/step
POST /api/onboarding/complete
POST /api/onboarding/skip
"""
from flask import Blueprint, request
from app import db
from app.models.onboarding import Onboarding
from app.utils.auth_helper import token_required, get_current_user
from app.utils.helpers import success_response, error_response

onboarding_bp = Blueprint('onboarding', __name__)


@onboarding_bp.route('/status', methods=['GET'])
@token_required
def get_status():
    """Get onboarding status for the current user."""
    user = get_current_user()
    onboarding = user.onboarding

    if not onboarding:
        # Create record if missing
        onboarding = Onboarding(user_id=user.id)
        db.session.add(onboarding)
        db.session.commit()

    # Determine next step
    next_step = None
    if not onboarding.store_created:
        next_step = {
            'step': 1,
            'action': 'create_store',
            'title': 'Set up your store',
            'description': 'Enter your store name, type, address, and GST number',
        }
    elif not onboarding.products_added:
        next_step = {
            'step': 2,
            'action': 'add_products',
            'title': 'Add your products',
            'description': 'Add products manually, import from Excel, or scan barcodes',
        }
    elif not onboarding.first_sale_recorded:
        next_step = {
            'step': 3,
            'action': 'record_sale',
            'title': 'Record your first sale',
            'description': 'Make your first sale to see everything in action',
        }
    elif not onboarding.is_onboarded:
        next_step = {
            'step': 4,
            'action': 'complete',
            'title': 'Setup Complete!',
            'description': "You're all set. Explore your dashboard!",
        }

    return success_response(data={
        'onboarding': onboarding.to_dict(),
        'next_step': next_step,
        'progress_pct': min(100, onboarding.step_completed * 25),
        'steps': [
            {
                'step': 1,
                'title': 'Create Store',
                'completed': onboarding.store_created,
                'action': 'create_store',
            },
            {
                'step': 2,
                'title': 'Add Products',
                'completed': onboarding.products_added,
                'action': 'add_products',
            },
            {
                'step': 3,
                'title': 'Enter Opening Stock',
                'completed': onboarding.stock_entered,
                'action': 'set_stock',
            },
            {
                'step': 4,
                'title': 'Dashboard Ready',
                'completed': onboarding.is_onboarded,
                'action': 'complete',
            },
        ],
    })


@onboarding_bp.route('/step', methods=['PUT'])
@token_required
def update_step():
    """Update onboarding step progress."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    step = data.get('step', 0)

    onboarding = user.onboarding
    if not onboarding:
        onboarding = Onboarding(user_id=user.id)
        db.session.add(onboarding)

    if isinstance(step, int) and 0 <= step <= 4:
        if step > onboarding.step_completed:
            onboarding.step_completed = step

        # Update granular flags
        if step >= 1:
            onboarding.store_created = True
        if step >= 2:
            onboarding.products_added = True
            onboarding.stock_entered = True
        if step >= 3:
            onboarding.stock_entered = True
        if step >= 4:
            onboarding.is_onboarded = True

    db.session.commit()
    return success_response(data={'onboarding': onboarding.to_dict()}, message=f"Step {step} completed")


@onboarding_bp.route('/complete', methods=['POST'])
@token_required
def complete_onboarding():
    """Mark onboarding as fully complete."""
    user = get_current_user()
    onboarding = user.onboarding

    if not onboarding:
        onboarding = Onboarding(user_id=user.id)
        db.session.add(onboarding)

    onboarding.is_onboarded = True
    onboarding.step_completed = 4
    onboarding.store_created = True
    onboarding.products_added = True
    onboarding.stock_entered = True
    onboarding.first_sale_recorded = True
    db.session.commit()

    return success_response(
        data={'onboarding': onboarding.to_dict()},
        message="Onboarding complete! Welcome to ShopManager 🎉"
    )


@onboarding_bp.route('/skip', methods=['POST'])
@token_required
def skip_onboarding():
    """Allow user to skip onboarding and go straight to dashboard."""
    user = get_current_user()
    onboarding = user.onboarding

    if not onboarding:
        onboarding = Onboarding(user_id=user.id)
        db.session.add(onboarding)

    onboarding.skipped = True
    onboarding.is_onboarded = True
    onboarding.step_completed = 4
    db.session.commit()

    return success_response(
        data={'onboarding': onboarding.to_dict()},
        message="Onboarding skipped. You can always set up your store from Settings."
    )
