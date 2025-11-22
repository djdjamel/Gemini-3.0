from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import os
import tempfile
import subprocess

def generate_parcel_pdf(items, filename):
    """
    Generates a PDF with labels for the given items.
    items: List of dicts with 'designation', 'expiry_date', 'barcode', 'print_date'
    A4 page, 4 labels per page (2x2 or 1x4? Requirement says "peut contenir 4 étiquettes").
    Let's assume 2x2 for A4. A4 is 210x297mm.
    """
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Layout configuration (Approximate for 4 labels)
    # Let's say 2 columns, 2 rows.
    col_width = width / 2
    row_height = height / 2
    
    for i, item in enumerate(items):
        if i > 0 and i % 4 == 0:
            c.showPage()
            
        # Calculate position
        pos_in_page = i % 4
        col = pos_in_page % 2
        row = 1 - (pos_in_page // 2) # 1 for top, 0 for bottom
        
        x = col * col_width
        y = row * row_height
        
        # Draw Label Content
        # Margin
        margin = 10 * mm
        x += margin
        y += margin
        
        # Content area
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y + 120*mm, item['designation'][:30]) # Truncate if too long
        
        c.setFont("Helvetica", 12)
        c.drawString(x, y + 105*mm, f"Exp: {item['expiry_date']}")
        c.drawString(x, y + 95*mm, f"Imprimé le: {item['print_date']}")
        
        # Barcode
        barcode_value = item['barcode']
        barcode = code128.Code128(barcode_value, barHeight=20*mm, barWidth=0.5*mm)
        barcode.drawOn(c, x, y + 60*mm)
        
        c.drawString(x, y + 55*mm, barcode_value)
        
        # Draw border for debugging/cutting
        c.rect(col * col_width + 5*mm, row * row_height + 5*mm, col_width - 10*mm, row_height - 10*mm)

    c.save()

def print_pdf(filename):
    """
    Sends the PDF to the default printer.
    """
    if os.name == 'nt': # Windows
        os.startfile(filename, "print")
    else:
        subprocess.run(["lp", filename])
