"""
app/routes/bills.py — Billing system with GST invoices
POST /api/stores/<store_id>/bills
GET  /api/stores/<store_id>/bills
GET  /api/stores/<store_id>/bills/<bill_id>
GET  /api/stores/<store_id>/bills/<bill_id>/pdf
POST /api/stores/<store_id>/bills/<bill_id>/whatsapp
"""
import io
from flask import Blueprint, request, send_file
from app import db
from app.models.bill import Bill
from app.models.sale import Sale
from app.models.product import Product
from app.models.customer import Customer
from app.models.udhaar import Udhaar
from app.utils.auth_helper import token_required, get_current_user, verify_store_access, check_feature_access
from app.utils.helpers import (
    success_response, error_response, validation_error_response,
    paginate_query, get_pagination_params, round_half_up
)

bills_bp = Blueprint('bills', __name__)


def _calculate_bill_totals(items: list, discount: float, discount_type: str, store_tax_rate: float) -> dict:
    """Calculate all bill amounts from line items."""
    subtotal = sum(
        float(item.get('unit_price', item.get('selling_price', 0))) * int(item.get('quantity', item.get('qty', 1)))
        for item in items
    )

    # Discount
    if discount_type == 'percent':
        discount_amount = round_half_up(subtotal * discount / 100)
    else:
        discount_amount = discount

    taxable_amount = max(0.0, subtotal - discount_amount)

    # GST = CGST + SGST (intra-state) or IGST (inter-state)
    # Using store tax_rate: half CGST, half SGST
    gst_total = round_half_up(taxable_amount * store_tax_rate / 100)
    cgst = round_half_up(gst_total / 2)
    sgst = round_half_up(gst_total / 2)
    igst = 0.0  # Phase 3: detect inter-state

    total = taxable_amount + gst_total

    return {
        'subtotal': subtotal,
        'discount': discount_amount,
        'taxable_amount': taxable_amount,
        'cgst_amount': cgst,
        'sgst_amount': sgst,
        'igst_amount': igst,
        'gst_amount': gst_total,
        'total_amount': total,
    }


@bills_bp.route('/<int:store_id>/bills', methods=['POST'])
@token_required
def create_bill(store_id):
    """
    Generate a bill/invoice.
    Records individual sales, updates stock, and generates PDF.
    """
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    # Check GST billing plan access
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    items = data.get('items', [])
    if not items:
        return error_response("At least one item is required", 400)

    # Check GST billing feature
    apply_gst = data.get('apply_gst', False)
    if apply_gst:
        ok, msg = check_feature_access(user, 'gst_billing')
        if not ok:
            apply_gst = False  # Silently disable; or return error — design choice

    discount = float(data.get('discount', 0))
    discount_type = data.get('discount_type', 'flat')
    payment_mode = data.get('payment_mode', 'cash')
    amount_paid = float(data.get('amount_paid', 0))
    tax_rate = store.tax_rate if apply_gst else 0.0

    # Validate and enrich items
    enriched_items = []
    stock_errors = []
    for item in items:
        product_id = item.get('product_id')
        qty = int(item.get('quantity', item.get('qty', 1)))
        override_price = item.get('unit_price', item.get('selling_price'))

        product = None
        if product_id:
            product = Product.query.filter_by(id=product_id, store_id=store_id, is_active=True).first()

        if product:
            unit_price = float(override_price) if override_price else float(product.selling_price)
            purchase_price = float(product.purchase_price)
            name = item.get('name', product.name)
            hsn_code = item.get('hsn_code', product.hsn_code or '')
            prod_tax_rate = product.tax_rate if apply_gst else 0.0

            if product.current_stock < qty:
                stock_errors.append(f"'{product.name}': only {product.current_stock} {product.unit} available")
                continue
        else:
            # Manual item (no product record)
            unit_price = float(override_price or 0)
            purchase_price = 0.0
            name = item.get('name', 'Item')
            hsn_code = item.get('hsn_code', '')
            prod_tax_rate = 0.0

        item_discount = float(item.get('discount', 0))
        item_total = (unit_price * qty) - item_discount

        enriched_items.append({
            'product_id': product_id,
            'name': name,
            'quantity': qty,
            'unit_price': unit_price,
            'purchase_price': purchase_price,
            'discount': item_discount,
            'tax_rate': prod_tax_rate,
            'total': item_total,
            'hsn_code': hsn_code,
        })

    if stock_errors:
        return error_response("Stock issues: " + "; ".join(stock_errors), 400)

    if not enriched_items:
        return error_response("No valid items to bill", 400)

    # Calculate totals
    totals = _calculate_bill_totals(enriched_items, discount, discount_type, tax_rate)
    total_amount = totals['total_amount']
    amount_due = max(0.0, total_amount - amount_paid)

    payment_status = 'paid' if amount_due <= 0 else ('partial' if amount_paid > 0 else 'unpaid')

    # Customer info
    customer_id = data.get('customer_id')
    customer = None
    if customer_id:
        customer = Customer.query.filter_by(id=customer_id, store_id=store_id, is_active=True).first()

    # Generate invoice number
    invoice_number = store.get_next_invoice_number()

    # Create bill
    bill = Bill(
        store_id=store_id,
        customer_id=customer_id,
        invoice_number=invoice_number,
        bill_items=enriched_items,
        subtotal=totals['subtotal'],
        discount=totals['discount'],
        discount_type=discount_type,
        taxable_amount=totals['taxable_amount'],
        cgst_amount=totals['cgst_amount'],
        sgst_amount=totals['sgst_amount'],
        igst_amount=totals['igst_amount'],
        gst_amount=totals['gst_amount'],
        total_amount=total_amount,
        amount_paid=amount_paid,
        amount_due=amount_due,
        payment_mode=payment_mode,
        payment_status=payment_status,
        customer_name=customer.name if customer else data.get('customer_name'),
        customer_phone=customer.phone if customer else data.get('customer_phone'),
        customer_address=customer.address if customer else data.get('customer_address'),
        customer_gstin=customer.gstin if customer else data.get('customer_gstin'),
        note=data.get('note'),
        terms=data.get('terms'),
    )
    db.session.add(bill)
    db.session.flush()  # Get bill.id

    # Deduct stock & record individual sales
    for item in enriched_items:
        product_id = item.get('product_id')
        if product_id:
            product = Product.query.get(product_id)
            if product:
                product.current_stock -= item['quantity']
                sale = Sale(
                    store_id=store_id,
                    product_id=product_id,
                    product_name_snapshot=item['name'],
                    quantity_sold=item['quantity'],
                    purchase_price_at_sale=item['purchase_price'],
                    selling_price=item['unit_price'],
                    discount=item['discount'],
                    total_amount=item['total'],
                    profit=(item['unit_price'] - item['purchase_price']) * item['quantity'] - item['discount'],
                    payment_mode=payment_mode,
                    customer_id=customer_id,
                    customer_name=bill.customer_name,
                    customer_phone=bill.customer_phone,
                    bill_id=bill.id,
                )
                db.session.add(sale)

    # Update customer stats
    if customer:
        customer.total_purchases = float(customer.total_purchases) + total_amount
        customer.total_orders += 1
        if payment_mode == 'credit' or payment_status in ('unpaid', 'partial'):
            credit_amount = amount_due
            customer.udhaar_balance = float(customer.udhaar_balance) + credit_amount
            # Create udhaar entry
            udhaar = Udhaar(
                customer_id=customer.id,
                store_id=store_id,
                amount=credit_amount,
                type='given',
                note=f"Bill #{invoice_number}",
                bill_id=bill.id,
            )
            db.session.add(udhaar)

    # Generate PDF
    try:
        from app.services.pdf_service import generate_bill_pdf
        generate_bill_pdf(bill, store, save_to_disk=True)
    except Exception:
        pass  # PDF generation failure shouldn't block the API

    db.session.commit()

    return success_response(
        data={'bill': bill.to_dict()},
        message=f"Bill #{invoice_number} created successfully",
        status_code=201
    )


@bills_bp.route('/<int:store_id>/bills', methods=['GET'])
@token_required
def list_bills(store_id):
    """List bills with search and date filters."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    page, per_page = get_pagination_params()
    query = Bill.query.filter_by(store_id=store_id, is_cancelled=False)

    # Filter by payment status
    status = request.args.get('status')
    if status in ['paid', 'partial', 'unpaid']:
        query = query.filter(Bill.payment_status == status)

    # Search by invoice number or customer name
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Bill.invoice_number.ilike(f'%{search}%'),
                Bill.customer_name.ilike(f'%{search}%'),
            )
        )

    query = query.order_by(Bill.created_at.desc())
    result = paginate_query(query, page, per_page)

    return success_response(data={
        'bills': [b.to_dict() for b in result['items']],
        'pagination': result['pagination'],
    })


@bills_bp.route('/<int:store_id>/bills/<int:bill_id>', methods=['GET'])
@token_required
def get_bill(store_id, bill_id):
    """Get bill details."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    bill = Bill.query.filter_by(id=bill_id, store_id=store_id).first()
    if not bill:
        return error_response("Bill not found", 404)

    return success_response(data={
        'bill': bill.to_dict(),
        'store': store.to_dict(),
    })


@bills_bp.route('/<int:store_id>/bills/<int:bill_id>/pdf', methods=['GET'])
@token_required
def download_bill_pdf(store_id, bill_id):
    """Download bill as PDF."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    bill = Bill.query.filter_by(id=bill_id, store_id=store_id).first()
    if not bill:
        return error_response("Bill not found", 404)

    from app.services.pdf_service import generate_bill_pdf
    pdf_bytes = generate_bill_pdf(bill, store, save_to_disk=False)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Invoice_{bill.invoice_number}.pdf"
    )


@bills_bp.route('/<int:store_id>/bills/<int:bill_id>/whatsapp', methods=['GET'])
@token_required
def get_whatsapp_link(store_id, bill_id):
    """Get WhatsApp share link for the bill."""
    user = get_current_user()
    store = verify_store_access(store_id, user)
    if not store:
        return error_response("Store not found or access denied", 404)

    bill = Bill.query.filter_by(id=bill_id, store_id=store_id).first()
    if not bill:
        return error_response("Bill not found", 404)

    from app.services.whatsapp_service import get_bill_whatsapp_link
    link = get_bill_whatsapp_link(bill, store)

    bill.whatsapp_sent = True
    db.session.commit()

    return success_response(data={
        'whatsapp_link': link,
        'invoice_number': bill.invoice_number,
        'customer_phone': bill.customer_phone,
    })
