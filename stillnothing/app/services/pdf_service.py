"""
app/services/pdf_service.py — PDF generation using ReportLab
Generates professional GST invoices and report PDFs.
"""
import io
import os
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.colors import HexColor

# Brand Colors
PRIMARY_COLOR = HexColor('#1E40AF')    # Blue
SECONDARY_COLOR = HexColor('#3B82F6')
ACCENT_COLOR = HexColor('#10B981')     # Green
DARK_COLOR = HexColor('#1F2937')
LIGHT_BG = HexColor('#F8FAFC')
BORDER_COLOR = HexColor('#E2E8F0')
TEXT_MUTED = HexColor('#6B7280')


def _build_styles():
    styles = getSampleStyleSheet()
    custom = {
        'title': ParagraphStyle(
            'BillTitle', fontSize=22, leading=26,
            textColor=PRIMARY_COLOR, fontName='Helvetica-Bold',
            alignment=TA_RIGHT
        ),
        'subtitle': ParagraphStyle(
            'BillSubtitle', fontSize=9, leading=12,
            textColor=TEXT_MUTED, fontName='Helvetica',
            alignment=TA_RIGHT
        ),
        'store_name': ParagraphStyle(
            'StoreName', fontSize=14, leading=18,
            textColor=DARK_COLOR, fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ),
        'store_detail': ParagraphStyle(
            'StoreDetail', fontSize=8, leading=11,
            textColor=TEXT_MUTED, fontName='Helvetica',
            alignment=TA_LEFT
        ),
        'section_header': ParagraphStyle(
            'SectionHeader', fontSize=8, leading=10,
            textColor=colors.white, fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ),
        'label': ParagraphStyle(
            'Label', fontSize=8, leading=10,
            textColor=TEXT_MUTED, fontName='Helvetica',
        ),
        'value': ParagraphStyle(
            'Value', fontSize=9, leading=11,
            textColor=DARK_COLOR, fontName='Helvetica-Bold',
        ),
        'normal': ParagraphStyle(
            'Normal2', fontSize=8, leading=10,
            textColor=DARK_COLOR, fontName='Helvetica',
        ),
        'amount': ParagraphStyle(
            'Amount', fontSize=10, leading=12,
            textColor=DARK_COLOR, fontName='Helvetica-Bold',
            alignment=TA_RIGHT
        ),
        'total_amount': ParagraphStyle(
            'TotalAmount', fontSize=14, leading=17,
            textColor=colors.white, fontName='Helvetica-Bold',
            alignment=TA_RIGHT
        ),
    }
    return custom


def generate_bill_pdf(bill, store, save_to_disk: bool = True) -> bytes:
    """
    Generate a professional GST invoice PDF.
    Args:
        bill: Bill model instance
        store: Store model instance
        save_to_disk: If True, save PDF to uploads/ folder and update bill.pdf_path
    Returns:
        PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=15*mm,
    )

    styles = _build_styles()
    story = []
    page_width = A4[0] - 30*mm  # usable width

    # ── Header ──────────────────────────────────────────────────────────────
    header_data = [[
        # Left: Store Info
        [
            Paragraph(store.store_name, styles['store_name']),
            Spacer(1, 2),
            Paragraph(store.address or '', styles['store_detail']),
            Paragraph(f"Phone: {store.phone or 'N/A'}", styles['store_detail']),
            Paragraph(f"Email: {store.email or 'N/A'}", styles['store_detail']),
            *(
                [Paragraph(f"GSTIN: {store.gst_number}", styles['store_detail'])]
                if store.gst_number else []
            ),
        ],
        # Right: Invoice Info
        [
            Paragraph("INVOICE", styles['title']),
            Paragraph(f"#{bill.invoice_number}", styles['subtitle']),
            Spacer(1, 4),
            Paragraph(f"Date: {bill.created_at.strftime('%d %b %Y') if bill.created_at else 'N/A'}", styles['subtitle']),
            Paragraph(f"Status: {bill.payment_status.upper()}", styles['subtitle']),
        ],
    ]]

    header_table = Table(header_data, colWidths=[page_width * 0.55, page_width * 0.45])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR))
    story.append(Spacer(1, 3*mm))

    # ── Bill To ─────────────────────────────────────────────────────────────
    if bill.customer_name:
        bill_to_data = [[
            [
                Paragraph("BILL TO", styles['label']),
                Paragraph(bill.customer_name, styles['value']),
                Paragraph(bill.customer_phone or '', styles['store_detail']),
                Paragraph(bill.customer_address or '', styles['store_detail']),
                *(
                    [Paragraph(f"GSTIN: {bill.customer_gstin}", styles['store_detail'])]
                    if bill.customer_gstin else []
                ),
            ],
            [
                Paragraph("PAYMENT MODE", styles['label']),
                Paragraph(bill.payment_mode.upper(), styles['value']),
            ],
        ]]
        bill_to_table = Table(bill_to_data, colWidths=[page_width * 0.6, page_width * 0.4])
        bill_to_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(bill_to_table)
        story.append(Spacer(1, 4*mm))

    # ── Items Table ──────────────────────────────────────────────────────────
    items_header = ['#', 'Product', 'HSN', 'Qty', 'Unit Price', 'Tax%', 'Amount']
    col_widths = [
        page_width * 0.05,
        page_width * 0.30,
        page_width * 0.12,
        page_width * 0.08,
        page_width * 0.15,
        page_width * 0.10,
        page_width * 0.20,
    ]

    items_data = [items_header]
    bill_items = bill.bill_items or []

    for i, item in enumerate(bill_items, 1):
        items_data.append([
            str(i),
            item.get('name', ''),
            item.get('hsn_code', ''),
            str(item.get('quantity', item.get('qty', 1))),
            f"₹{float(item.get('unit_price', item.get('selling_price', 0))):,.2f}",
            f"{item.get('tax_rate', 0)}%",
            f"₹{float(item.get('total', 0)):,.2f}",
        ])

    items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 1), (-1, -1), DARK_COLOR),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # ── Totals ───────────────────────────────────────────────────────────────
    totals_data = []

    def amount_row(label, amount, bold=False):
        style = styles['value'] if bold else styles['normal']
        return ['', '',
                Paragraph(label, style if not bold else styles['label']),
                Paragraph(f"₹{float(amount):,.2f}", styles['amount'])]

    totals_data.append(amount_row('Subtotal', bill.subtotal))
    if float(bill.discount) > 0:
        totals_data.append(amount_row('Discount', bill.discount))
    if float(bill.taxable_amount) > 0:
        totals_data.append(amount_row('Taxable Amount', bill.taxable_amount))
    if float(bill.cgst_amount) > 0:
        totals_data.append(amount_row('CGST', bill.cgst_amount))
        totals_data.append(amount_row('SGST', bill.sgst_amount))
    if float(bill.igst_amount) > 0:
        totals_data.append(amount_row('IGST', bill.igst_amount))

    # Grand total row with colored background
    total_row_data = [
        ['', '',
         Paragraph('TOTAL AMOUNT', ParagraphStyle('GTLabel', fontSize=10, fontName='Helvetica-Bold',
                                                   textColor=colors.white, alignment=TA_LEFT)),
         Paragraph(f"₹{float(bill.total_amount):,.2f}",
                   ParagraphStyle('GTAmt', fontSize=12, fontName='Helvetica-Bold',
                                  textColor=colors.white, alignment=TA_RIGHT))]
    ]

    totals_col_widths = [page_width * 0.3, page_width * 0.2, page_width * 0.25, page_width * 0.25]
    totals_table = Table(totals_data + total_row_data, colWidths=totals_col_widths)
    totals_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (2, -1), (-1, -1), 1, PRIMARY_COLOR),
        ('BACKGROUND', (0, -1), (-1, -1), PRIMARY_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(totals_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Thank you for your business! For queries, contact the store.",
        ParagraphStyle('Footer', fontSize=7, textColor=TEXT_MUTED,
                       fontName='Helvetica-Oblique', alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f"Generated by ShopManager • {datetime.now().strftime('%d %b %Y %H:%M')}",
        ParagraphStyle('FooterSub', fontSize=6, textColor=BORDER_COLOR,
                       fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()

    # Optionally save to disk
    if save_to_disk:
        try:
            upload_dir = os.path.join('uploads', 'bills')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"bill_{bill.invoice_number}.pdf"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            bill.pdf_path = filepath
        except Exception:
            pass  # Non-critical

    return pdf_bytes


def generate_report_pdf(report_data: dict, report_type: str = 'daily', store=None) -> bytes:
    """
    Generate a sales / P&L report PDF.
    report_data keys: period, total_sales, total_profit, total_orders, data (list of rows)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             leftMargin=15*mm, rightMargin=15*mm,
                             topMargin=15*mm, bottomMargin=15*mm)
    styles = _build_styles()
    story = []
    page_width = A4[0] - 30*mm

    # Title
    story.append(Paragraph(f"{report_type.capitalize()} Report", styles['title']))
    story.append(Paragraph(
        f"{store.store_name if store else 'Store'} • {report_data.get('period', '')}",
        styles['subtitle']
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR))
    story.append(Spacer(1, 4*mm))

    # Summary boxes
    summary = [
        ['Total Sales', f"₹{float(report_data.get('total_sales', 0)):,.2f}"],
        ['Total Profit', f"₹{float(report_data.get('total_profit', 0)):,.2f}"],
        ['Total Orders', str(report_data.get('total_orders', 0))],
    ]
    for label, val in summary:
        story.append(Paragraph(f"<b>{label}:</b> {val}", styles['normal']))
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 4*mm))

    # Data table
    rows = report_data.get('data', [])
    if rows:
        headers = list(rows[0].keys()) if rows else []
        table_data = [[str(h).replace('_', ' ').title() for h in headers]]
        for row in rows:
            table_data.append([str(row.get(h, '')) for h in headers])

        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)

    doc.build(story)
    return buffer.getvalue()
