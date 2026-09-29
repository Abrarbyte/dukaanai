"""
app/routes/product.py — Product management endpoints
POST /api/stores/<store_id>/products
GET  /api/stores/<store_id>/products
GET  /api/stores/<store_id>/products/<product_id>
PUT  /api/stores/<store_id>/products/<product_id>
DELETE /api/stores/<store_id>/products/<product_id>
POST /api/stores/<store_id>/products/import
GET  /api/stores/<store_id>/products/template
GET  /api/stores/<store_id>/products/low-stock
"""
import io
from flask import Blueprint, request, send_file
from app import db
from app.models.product import Product
from app.utils.auth_helper import token_required, get_current_user, verify_store_access, check_product_limit
from app.utils.validators import validate_product_data
from app.utils.helpers import (
    success_response, error_response, validation_error_response,
    paginate_query, get_pagination_params,
    generate_excel_template, parse_excel_products
)

product_bp = Blueprint('product', __name__)


@product_bp.route('/<int:store_id>/products', methods=['POST'])
@token_required
def create_product(store_id):
    """Add a new product to the store."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Check plan product limit
    allowed, msg = check_product_limit(user, store_id)
    if not allowed:
        return error_response(msg, 403, upgrade_required=True)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = validate_product_data(data)
    if not valid:
        return validation_error_response(errors)

    # Check for duplicate barcode within store
    if cleaned.get('barcode'):
        existing = Product.query.filter_by(store_id=store_id, barcode=cleaned['barcode'], is_active=True).first()
        if existing:
            return error_response(f"A product with barcode '{cleaned['barcode']}' already exists", 409)

    product = Product(store_id=store_id, **cleaned)
    db.session.add(product)

    # Update onboarding
    if user.onboarding and not user.onboarding.products_added:
        user.onboarding.products_added = True
        user.onboarding.stock_entered = True
        if user.onboarding.step_completed < 2:
            user.onboarding.step_completed = 2

    db.session.commit()
    return success_response(data={'product': product.to_dict()}, message="Product added", status_code=201)


@product_bp.route('/<int:store_id>/products', methods=['GET'])
@token_required
def list_products(store_id):
    """
    List products with search, filter, and pagination.
    Query params: page, per_page, search, category, low_stock, sort
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    page, per_page = get_pagination_params()
    query = Product.query.filter_by(store_id=store_id, is_active=True)

    # Search
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.category.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
            )
        )

    # Filter by category
    category = request.args.get('category', '').strip()
    if category:
        query = query.filter(Product.category == category)

    # Filter low stock only
    if request.args.get('low_stock') == '1':
        query = query.filter(Product.current_stock <= Product.min_stock_alert)

    # Sort
    sort = request.args.get('sort', 'name')
    sort_map = {
        'name': Product.name.asc(),
        'stock': Product.current_stock.asc(),
        'price': Product.selling_price.desc(),
        'margin': Product.selling_price.desc(),  # Approximate
        'created': Product.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.name.asc()))

    result = paginate_query(query, page, per_page)

    # Get all categories for this store (for filter dropdown)
    categories = db.session.query(Product.category).filter(
        Product.store_id == store_id,
        Product.is_active == True,
        Product.category != None
    ).distinct().all()

    return success_response(data={
        'products': [p.to_dict() for p in result['items']],
        'pagination': result['pagination'],
        'categories': [c[0] for c in categories if c[0]],
    })


@product_bp.route('/<int:store_id>/products/template', methods=['GET'])
@token_required
def download_template(store_id):
    """Download Excel template for bulk product import."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    excel_buffer = generate_excel_template()
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'products_template_{store.store_name}.xlsx'
    )


@product_bp.route('/<int:store_id>/products/import', methods=['POST'])
@token_required
def import_products(store_id):
    """Bulk import products from Excel file."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    if 'file' not in request.files:
        return error_response("Excel file is required (field: 'file')", 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error_response("File must be an Excel file (.xlsx or .xls)", 400)

    products_data, parse_errors = parse_excel_products(file.stream)
    if parse_errors and not products_data:
        return validation_error_response(parse_errors)

    # Check plan limits
    limits = user.get_plan_limits()
    max_products = limits.get('max_products')
    if max_products is not None:
        current_count = Product.query.filter_by(store_id=store_id, is_active=True).count()
        if current_count + len(products_data) > max_products:
            return error_response(
                f"Import would exceed your plan limit of {max_products} products. "
                f"Currently have {current_count}, importing {len(products_data)}. Upgrade your plan.",
                403, upgrade_required=True
            )

    imported = 0
    skipped = 0
    import_errors = list(parse_errors)  # Include parse errors in response

    for prod_data in products_data:
        try:
            # Check duplicate barcode
            if prod_data.get('barcode'):
                existing = Product.query.filter_by(
                    store_id=store_id, barcode=prod_data['barcode'], is_active=True
                ).first()
                if existing:
                    skipped += 1
                    import_errors.append(f"Skipped '{prod_data['name']}': barcode already exists")
                    continue

            product = Product(store_id=store_id, **prod_data)
            db.session.add(product)
            imported += 1
        except Exception as e:
            import_errors.append(f"Failed to import '{prod_data.get('name', 'unknown')}': {str(e)}")
            skipped += 1

    if imported > 0:
        if user.onboarding and not user.onboarding.products_added:
            user.onboarding.products_added = True
            if user.onboarding.step_completed < 2:
                user.onboarding.step_completed = 2
        db.session.commit()

    return success_response(
        data={'imported': imported, 'skipped': skipped, 'errors': import_errors},
        message=f"Import complete: {imported} products imported, {skipped} skipped",
        status_code=201 if imported > 0 else 200
    )


@product_bp.route('/<int:store_id>/products/low-stock', methods=['GET'])
@token_required
def low_stock_products(store_id):
    """Get all products at or below min stock alert."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    from app.services.alert_service import get_low_stock_alerts
    alerts = get_low_stock_alerts(store_id)
    return success_response(data={
        'low_stock_products': alerts,
        'total': len(alerts),
    })


@product_bp.route('/<int:store_id>/products/<int:product_id>', methods=['GET'])
@token_required
def get_product(store_id, product_id):
    """Get a single product's details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found", 404)

    # Include recent sales for this product
    from app.models.sale import Sale
    recent_sales = (
        Sale.query.filter_by(product_id=product_id, store_id=store_id)
        .order_by(Sale.created_at.desc())
        .limit(10)
        .all()
    )

    return success_response(data={
        'product': product.to_dict(),
        'recent_sales': [s.to_dict() for s in recent_sales],
    })


@product_bp.route('/<int:store_id>/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(store_id, product_id):
    """Update product details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found", 404)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    valid, cleaned, errors = validate_product_data(data)
    if not valid:
        return validation_error_response(errors)

    # Check barcode conflict (exclude current product)
    if cleaned.get('barcode') and cleaned['barcode'] != product.barcode:
        existing = Product.query.filter(
            Product.store_id == store_id,
            Product.barcode == cleaned['barcode'],
            Product.is_active == True,
            Product.id != product_id
        ).first()
        if existing:
            return error_response(f"Barcode '{cleaned['barcode']}' is already used by '{existing.name}'", 409)

    for field, value in cleaned.items():
        setattr(product, field, value)

    db.session.commit()
    return success_response(data={'product': product.to_dict()}, message="Product updated")


@product_bp.route('/<int:store_id>/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(store_id, product_id):
    """Soft-delete a product."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found", 404)

    product.is_active = False
    db.session.commit()
    return success_response(message=f"Product '{product.name}' deleted")


@product_bp.route('/<int:store_id>/products/<int:product_id>/adjust-stock', methods=['POST'])
@token_required
def adjust_stock(store_id, product_id):
    """Manually adjust stock (add/remove stock with reason)."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()
    if not product:
        return error_response("Product not found", 404)

    data = request.get_json(silent=True) or {}
    try:
        adjustment = int(data.get('adjustment', 0))  # Positive = add, negative = remove
    except (TypeError, ValueError):
        return error_response("Adjustment must be an integer", 400)

    new_stock = product.current_stock + adjustment
    if new_stock < 0:
        return error_response(
            f"Cannot reduce stock below 0. Current stock: {product.current_stock}",
            400
        )

    product.current_stock = new_stock
    db.session.commit()

    return success_response(
        data={'product': product.to_dict(), 'adjustment': adjustment, 'new_stock': new_stock},
        message=f"Stock adjusted by {'+' if adjustment >= 0 else ''}{adjustment}"
    )
