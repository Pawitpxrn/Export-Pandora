import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_sample_pdf():
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    os.makedirs(samples_dir, exist_ok=True)
    pdf_path = os.path.join(samples_dir, "sample_sales_report.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=10
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )

    story = [
        Paragraph("<b>Sales Transaction Report (รายงานสรุปการขาย)</b>", title_style),
        Paragraph("Report Date: 19/09/2026 &nbsp;&nbsp;|&nbsp;&nbsp; Branch: Bangkok Main Branch &nbsp;&nbsp;|&nbsp;&nbsp; Currency: THB", meta_style),
        Spacer(1, 15)
    ]

    # Sample table data
    header = ["No.", "Item Code", "Product Name", "Category", "Qty", "Unit Price", "Discount", "Total Amount"]
    
    rows = [
        ["1", "SKU-1001", "MacBook Pro 14 M3", "Hardware", "5", "59,900.00", "0.00", "299,500.00"],
        ["2", "SKU-1002", "Dell UltraSharp 27 Monitor", "Peripheral", "12", "15,500.00", "500.00", "185,500.00"],
        ["3", "SKU-1003", "Logitech MX Master 3S", "Accessory", "25", "3,890.00", "100.00", "96,250.00"],
        ["4", "SKU-1004", "Keychron K2 Pro Keyboard", "Accessory", "18", "4,290.00", "0.00", "77,220.00"],
        ["5", "SKU-1005", "Cisco Catalyst Switch 24P", "Network", "3", "28,000.00", "1,500.00", "82,500.00"],
        ["6", "SKU-1006", "Synology NAS 4-Bay DS923+", "Storage", "4", "21,500.00", "0.00", "86,000.00"],
        ["7", "SKU-1007", "Seagate IronWolf 8TB HDD", "Storage", "16", "6,900.00", "200.00", "108,800.00"],
        ["8", "SKU-1008", "APC Smart-UPS 1500VA", "Power", "6", "18,900.00", "900.00", "112,500.00"],
        ["9", "SKU-1009", "Samsung 990 Pro 2TB SSD", "Storage", "20", "5,800.00", "0.00", "116,000.00"],
        ["10", "SKU-1010", "Apple iPad Pro 11 M4", "Tablet", "8", "39,900.00", "1,000.00", "318,200.00"],
        ["11", "SKU-1011", "Sony WH-1000XM5 Headphone", "Audio", "10", "11,990.00", "500.00", "119,400.00"],
        ["12", "SKU-1012", "LG DualUp Ergo Monitor", "Peripheral", "7", "19,900.00", "400.00", "138,900.00"],
        ["13", "SKU-1013", "Ubiquiti UniFi U6-Pro AP", "Network", "15", "5,600.00", "0.00", "84,000.00"],
        ["14", "SKU-1014", "Herman Miller Aeron Chair", "Furniture", "4", "45,000.00", "2,000.00", "178,000.00"],
        ["15", "SKU-1015", "CalDigit TS4 Thunderbolt Dock", "Accessory", "9", "14,500.00", "300.00", "130,200.00"],
        ["16", "SKU-1016", "Lenovo ThinkPad X1 Carbon", "Hardware", "6", "62,000.00", "1,500.00", "370,500.00"],
        ["17", "SKU-1017", "Asus ROG Swift OLED 32", "Peripheral", "2", "38,500.00", "0.00", "77,000.00"],
        ["18", "SKU-1018", "Anker 737 Power Bank 24K", "Accessory", "30", "4,190.00", "200.00", "123,700.00"],
        ["19", "SKU-1019", "Epson EcoTank L3250 Printer", "Office", "5", "4,890.00", "0.00", "24,450.00"],
        ["20", "SKU-1020", "Steelcase Gesture Chair", "Furniture", "3", "38,000.00", "1,000.00", "113,000.00"],
        ["21", "SKU-1021", "Fortinet FortiGate 60F", "Security", "2", "32,000.00", "500.00", "63,500.00"],
        ["22", "SKU-1022", "Microsoft Surface Laptop 7", "Hardware", "8", "42,900.00", "1,200.00", "342,000.00"],
        ["23", "SKU-1023", "Shure MV7+ USB Microphone", "Audio", "14", "9,500.00", "300.00", "132,300.00"],
        ["24", "SKU-1024", "Elgato Stream Deck MK.2", "Peripheral", "11", "5,290.00", "150.00", "58,040.00"],
        ["25", "SKU-1025", "Bose QuietComfort Ultra", "Audio", "6", "13,900.00", "400.00", "83,000.00"]
    ]

    table_data = [header] + rows

    t = Table(table_data, colWidths=[30, 60, 150, 65, 30, 65, 55, 75])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        # Alternating background
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),      # No.
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),      # SKU
        ('ALIGN', (2, 1), (3, -1), 'LEFT'),        # Name & Cat
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),      # Numbers
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))

    story.append(t)
    doc.build(story)
    print(f"Generated sample PDF at: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_sample_pdf()
