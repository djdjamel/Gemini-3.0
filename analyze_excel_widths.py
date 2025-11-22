import openpyxl

try:
    wb = openpyxl.load_workbook("liste.xlsx")
    ws = wb.active
    
    widths = {}
    for col in ws.column_dimensions:
        widths[col] = ws.column_dimensions[col].width
        
    print("Column Widths:", widths)
    
    # Also check if there are any specific styles for dates
except Exception as e:
    print(f"Error reading excel: {e}")
