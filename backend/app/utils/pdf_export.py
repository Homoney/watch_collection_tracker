from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from typing import List, Optional
import os


def format_currency(amount: Optional[float], currency: str) -> str:
    """Format currency for display"""
    if amount is None:
        return "N/A"
    return f"{currency} {amount:,.2f}"


def format_date(date_str: Optional[str]) -> str:
    """Format date for display"""
    if not date_str:
        return "N/A"
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str


def generate_watch_pdf(watch_data: dict, storage_path: str = "/app/storage") -> BytesIO:
    """
    Generate a PDF document for a single watch.

    Args:
        watch_data: Watch data dictionary from database
        storage_path: Base path for uploaded images

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        spaceBefore=20
    )

    # Title
    brand_name = watch_data.get('brand', {}).get('name', 'Unknown')
    model = watch_data.get('model', 'Unknown Model')
    title = Paragraph(f"{brand_name} {model}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))

    # Primary Image
    images = watch_data.get('images', [])
    if images:
        primary_image = next((img for img in images if img.get('is_primary')), images[0])
        image_path = os.path.join(storage_path, 'uploads', primary_image['file_path'])

        if os.path.exists(image_path):
            try:
                img = Image(image_path, width=4*inch, height=4*inch, kind='proportional')
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))
            except:
                pass

    # Basic Information Section
    elements.append(Paragraph("Basic Information", heading_style))

    basic_data = [
        ['Brand:', brand_name],
        ['Model:', model],
    ]

    if watch_data.get('reference_number'):
        basic_data.append(['Reference Number:', watch_data['reference_number']])
    if watch_data.get('serial_number'):
        basic_data.append(['Serial Number:', watch_data['serial_number']])
    if watch_data.get('movement_type'):
        basic_data.append(['Movement Type:', watch_data['movement_type'].get('name', 'N/A')])
    if watch_data.get('condition'):
        basic_data.append(['Condition:', watch_data['condition'].replace('_', ' ').title()])

    basic_table = Table(basic_data, colWidths=[2*inch, 4*inch])
    basic_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#1f2937')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(basic_table)
    elements.append(Spacer(1, 0.2*inch))

    # Specifications Section
    if any([watch_data.get('case_diameter'), watch_data.get('case_thickness'),
            watch_data.get('lug_width'), watch_data.get('water_resistance'),
            watch_data.get('power_reserve')]):

        elements.append(Paragraph("Specifications", heading_style))

        spec_data = []
        if watch_data.get('case_diameter'):
            spec_data.append(['Case Diameter:', f"{watch_data['case_diameter']} mm"])
        if watch_data.get('case_thickness'):
            spec_data.append(['Case Thickness:', f"{watch_data['case_thickness']} mm"])
        if watch_data.get('lug_width'):
            spec_data.append(['Lug Width:', f"{watch_data['lug_width']} mm"])
        if watch_data.get('water_resistance'):
            spec_data.append(['Water Resistance:', f"{watch_data['water_resistance']} m"])
        if watch_data.get('power_reserve'):
            spec_data.append(['Power Reserve:', f"{watch_data['power_reserve']} hours"])

        spec_table = Table(spec_data, colWidths=[2*inch, 4*inch])
        spec_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(spec_table)
        elements.append(Spacer(1, 0.2*inch))

    # Purchase Information Section
    elements.append(Paragraph("Purchase Information", heading_style))

    purchase_data = [
        ['Purchase Date:', format_date(watch_data.get('purchase_date'))],
        ['Purchase Price:', format_currency(watch_data.get('purchase_price'), watch_data.get('purchase_currency', 'USD'))],
    ]

    if watch_data.get('retailer'):
        purchase_data.append(['Retailer:', watch_data['retailer']])

    purchase_table = Table(purchase_data, colWidths=[2*inch, 4*inch])
    purchase_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#1f2937')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(purchase_table)
    elements.append(Spacer(1, 0.2*inch))

    # Market Value Section
    if watch_data.get('current_market_value'):
        elements.append(Paragraph("Current Market Value", heading_style))

        value_data = [
            ['Current Value:', format_currency(
                watch_data['current_market_value'],
                watch_data.get('current_market_currency', 'USD')
            )],
            ['Last Updated:', format_date(watch_data.get('last_value_update'))],
        ]

        value_table = Table(value_data, colWidths=[2*inch, 4*inch])
        value_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(value_table)
        elements.append(Spacer(1, 0.2*inch))

    # Service History Section
    service_history = watch_data.get('service_history', [])
    if service_history:
        elements.append(Paragraph("Service History", heading_style))

        service_data = [['Date', 'Provider', 'Type', 'Cost']]
        for service in service_history:
            service_data.append([
                format_date(service.get('service_date')),
                service.get('provider', 'N/A'),
                service.get('service_type', 'N/A'),
                format_currency(service.get('cost'), service.get('cost_currency', 'USD'))
            ])

        service_table = Table(service_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.2*inch])
        service_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(service_table)
        elements.append(Spacer(1, 0.2*inch))

    # Notes Section
    if watch_data.get('notes'):
        elements.append(Paragraph("Notes", heading_style))
        notes_style = ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12
        )
        notes = Paragraph(watch_data['notes'].replace('\n', '<br/>'), notes_style)
        elements.append(notes)

    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} by Watch Collection Tracker",
        footer_style
    )
    elements.append(footer)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_collection_pdf(watches: List[dict], collection_name: str = "My Collection", storage_path: str = "/app/storage") -> BytesIO:
    """
    Generate a PDF document for a collection of watches.

    Args:
        watches: List of watch data dictionaries
        collection_name: Name of the collection
        storage_path: Base path for uploaded images

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    title = Paragraph(collection_name, title_style)
    elements.append(title)

    # Summary
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    summary = Paragraph(f"Total Watches: {len(watches)}", subtitle_style)
    elements.append(summary)
    elements.append(Spacer(1, 0.3*inch))

    # Calculate total value
    total_purchase = sum(w.get('purchase_price', 0) or 0 for w in watches)
    total_current = sum(w.get('current_market_value', 0) or 0 for w in watches)

    if total_purchase > 0:
        summary_data = [
            ['Total Purchase Price:', f"USD {total_purchase:,.2f}"],
            ['Total Current Value:', f"USD {total_current:,.2f}"],
            ['Total Gain/Loss:', f"USD {(total_current - total_purchase):+,.2f}"],
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))

    # Watch list
    for i, watch in enumerate(watches):
        if i > 0:
            elements.append(PageBreak())

        # Generate individual watch content (without header/footer)
        brand_name = watch.get('brand', {}).get('name', 'Unknown')
        model = watch.get('model', 'Unknown Model')

        heading_style = ParagraphStyle(
            'WatchHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=20
        )
        watch_title = Paragraph(f"{brand_name} {model}", heading_style)
        elements.append(watch_title)

        # Add watch image if available
        images = watch.get('images', [])
        if images:
            primary_image = next((img for img in images if img.get('is_primary')), images[0])
            image_path = os.path.join(storage_path, 'uploads', primary_image['file_path'])

            if os.path.exists(image_path):
                try:
                    img = Image(image_path, width=3*inch, height=3*inch, kind='proportional')
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.2*inch))
                except:
                    pass

        # Watch details table
        watch_data = []

        if watch.get('reference_number'):
            watch_data.append(['Reference:', watch['reference_number']])
        if watch.get('purchase_price'):
            watch_data.append(['Purchase Price:', format_currency(watch['purchase_price'], watch.get('purchase_currency', 'USD'))])
        if watch.get('current_market_value'):
            watch_data.append(['Current Value:', format_currency(watch['current_market_value'], watch.get('current_market_currency', 'USD'))])
        if watch.get('purchase_date'):
            watch_data.append(['Purchase Date:', format_date(watch['purchase_date'])])

        if watch_data:
            details_table = Table(watch_data, colWidths=[2*inch, 3.5*inch])
            details_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONT', (1, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
                ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#374151')),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(details_table)

    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} by Watch Collection Tracker",
        footer_style
    )
    elements.append(footer)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
