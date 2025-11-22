def is_location_barcode(barcode: str) -> bool:
    """
    Checks if the barcode is a location barcode.
    Location barcodes start with '000' and are 7 digits long.
    """
    return barcode.startswith("000") and len(barcode) == 7 and barcode.isdigit()

def parse_location_barcode(barcode: str) -> str:
    """
    Parses a location barcode (000XXYY) into a readable label (e.g., A1).
    XX: Letter part (ASCII - 64). Special cases: 27=DD, 28=II, 29=JJ, 30=KK.
    YY: Numeric part (Floor/Level).
    """
    if not is_location_barcode(barcode):
        return None

    xx = int(barcode[3:5])
    yy = int(barcode[5:7])

    letter_part = ""
    if xx == 27:
        letter_part = "DD"
    elif xx == 28:
        letter_part = "II"
    elif xx == 29:
        letter_part = "JJ"
    elif xx == 30:
        letter_part = "KK"
    else:
        # Standard A-Z
        # 1 -> A (65)
        letter_part = chr(xx + 64)

    return f"{letter_part}{yy}"

def generate_location_barcode(label: str) -> str:
    """
    Generates a barcode from a label (e.g., A1 -> 0000101).
    Reverse of parse_location_barcode.
    """
    # This is a helper for testing or printing
    import re
    match = re.match(r"([A-Z]+)(\d+)", label)
    if not match:
        return None
    
    letters = match.group(1)
    numbers = int(match.group(2))
    
    xx = 0
    if letters == "DD":
        xx = 27
    elif letters == "II":
        xx = 28
    elif letters == "JJ":
        xx = 29
    elif letters == "KK":
        xx = 30
    elif len(letters) == 1:
        xx = ord(letters) - 64
    else:
        return None # Unknown format
        
    return f"000{xx:02d}{numbers:02d}"
