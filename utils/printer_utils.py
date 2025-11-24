from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.lib.utils import simpleSplit
import os
import tempfile
import subprocess

def generate_parcel_pdf(items, filename):
    """
    Generates a PDF with labels for the given items.
    items: List of dicts with 'designation', 'expiry_date', 'barcode', 'print_date'
    Layout: A4 Landscape (297x210mm), 4 labels per page (2x2).
    """
    # A4 Landscape
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(filename, pagesize=landscape(A4))
    
    # Layout configuration
    # 2 columns, 2 rows
    col_width = page_width / 2
    row_height = page_height / 2
    
    # Margins inside each label cell
    margin_x = 5 * mm
    margin_y = 5 * mm
    
    for i, item in enumerate(items):
        if i > 0 and i % 4 == 0:
            c.showPage()
            
        # Calculate position
        pos_in_page = i % 4
        col = pos_in_page % 2
        row = 1 - (pos_in_page // 2) # 1 for top, 0 for bottom
        
        # Base coordinates for this cell
        cell_x = col * col_width
        cell_y = row * row_height
        
        # Workable area inside the cell
        x = cell_x + margin_x
        y = cell_y + margin_y
        w = col_width - 2 * margin_x
        h = row_height - 2 * margin_y
        
        # --- Content Drawing ---
        
        # 1. Designation (Top, Huge Font)
        font_name = "Helvetica-Bold"
        font_size = 72 # Start big
        c.setFont(font_name, font_size)
        
        designation = item['designation']
        
        # Wrap text
        # Ensure we use the correct width for splitting
        lines = simpleSplit(designation, font_name, font_size, w)
        
        # If more than 3 lines, reduce font size until it fits or truncate
        # Allow shrinking down to 40 to fit
        while len(lines) > 3 and font_size > 40:
            font_size -= 4
            c.setFont(font_name, font_size)
            lines = simpleSplit(designation, font_name, font_size, w)
            
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] += "..."
            
        # Draw Designation
        # Position: Top of the workable area, moving down
        # Tight spacing
        text_y = cell_y + row_height - margin_y - font_size
        for line in lines:
            c.drawString(x, text_y, line)
            text_y -= (font_size * 1.0) 
            
        # 2. Barcode (Bottom, Left Aligned)
        bc_height = 15 * mm 
        bc_y = cell_y + margin_y + 8 * mm 
        
        barcode_value = item['barcode']
        bc = code128.Code128(barcode_value, barHeight=bc_height, barWidth=0.65*mm)
        
        # Left align barcode
        bc_x = x 
        
        bc.drawOn(c, bc_x, bc_y)
        
        # Barcode Text (Left aligned under barcode)
        c.setFont("Helvetica", 16)
        c.drawCentredString(bc_x + bc.width / 2, cell_y + margin_y, barcode_value)
        
        # 3. Expiry Date (Bottom Right)
        # Format Expiry Date to MM/YY
        expiry_raw = item['expiry_date']
        try:
            # Assuming YYYY-MM-DD
            parts = expiry_raw.split('-')
            if len(parts) == 3:
                # parts[0]=YYYY, parts[1]=MM, parts[2]=DD
                expiry_str = f"{parts[1]}/{parts[0][2:]}" # MM/YY
            else:
                expiry_str = expiry_raw
        except:
            expiry_str = expiry_raw

        exp_font_size = 48
        c.setFont("Helvetica-Bold", exp_font_size)
        exp_text = f"E: {expiry_str}" # Changed from EXP to E
        exp_width = c.stringWidth(exp_text, "Helvetica-Bold", exp_font_size)
        
        # Right align: x + w - exp_width
        exp_x = x + w - exp_width
        exp_y = bc_y 
        
        c.drawString(exp_x, exp_y, exp_text)
        
        # 4. Print Date (Centered Above Barcode)
        # "la date d'impression doit doubler sa taille et situé en haut du code barre aligné au centre horizontale de l'étiquette"
        # Double size = 24 (was 12)
        print_font_size = 24
        c.setFont("Helvetica", print_font_size)
        print_text = f"Imp: {item['print_date']}"
        
        # Position: Above barcode. Barcode top is bc_y + bc_height.
        # Add some padding.
        print_y = bc_y + bc_height + 5 * mm
        
        # Center horizontally in the label
        c.drawCentredString(cell_x + col_width / 2, print_y, print_text)

        # Draw border for debugging/cutting
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(cell_x, cell_y, col_width, row_height)
        c.setStrokeColorRGB(0, 0, 0) # Reset

    c.save()

def print_pdf(filename):
    """
    Sends the PDF to the default printer.
    """
    if os.name == 'nt': # Windows
        os.startfile(filename, "print")
    else:
        subprocess.run(["lp", filename])

def preview_pdf(filename):
    """
    Opens the PDF in the default viewer for preview.
    """
    if os.name == 'nt': # Windows
        os.startfile(filename)
    else:
        # Linux/Mac (xdg-open is common)
        subprocess.run(["xdg-open", filename])

def print_pdf_with_dialog(filename):
    """
    Opens a native printer selection dialog and prints the PDF to the selected printer.
    """
    from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
    from PyQt6.QtWidgets import QApplication
    import sys
    
    # Ensure there is a QApplication instance (should be, but good practice)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    printer = QPrinter()
    dialog = QPrintDialog(printer)
    
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        printer_name = printer.printerName()
        
        if os.name == 'nt': # Windows
            import ctypes
            # ShellExecuteW(hwnd, operation, file, parameters, directory, show_cmd)
            # operation "printto" prints to a specific printer
            # parameters: "printer_name"
            # Note: printer_name might need quotes if it has spaces
            
            print(f"Printing to: {printer_name}")
            
            # Use ctypes to call ShellExecuteW
            # 0 = SW_HIDE
            ctypes.windll.shell32.ShellExecuteW(
                0, 
                "printto", 
                filename, 
                f'"{printer_name}"', 
                None, 
                0
            )
        else:
            # Linux/Mac fallback
            subprocess.run(["lp", "-d", printer_name, filename])
