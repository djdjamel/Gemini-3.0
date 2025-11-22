from database.connection import get_db
from database.models import Location
from utils.barcode_utils import generate_location_barcode

def populate_locations():
    db = next(get_db())
    
    # Requirement:
    # 1. A to Z with floors 1 to 8 (A1..A8, B1..B8, ..., Z1..Z8)
    # 2. DD, II, JJ, KK with floors 1 to 8
    
    # Standard A-Z
    letters = [chr(i) for i in range(65, 91)] # A-Z
    
    # Special letters
    special_letters = ["DD", "II", "JJ", "KK"]
    
    all_letters = letters + special_letters
    
    count = 0
    for letter in all_letters:
        for floor in range(1, 9): # 1 to 8
            label = f"{letter}{floor}"
            barcode = generate_location_barcode(label)
            
            if not barcode:
                print(f"Skipping invalid label: {label}")
                continue
                
            # Check if exists
            existing = db.query(Location).filter(Location.label == label).first()
            if not existing:
                loc = Location(label=label, barcode=barcode)
                db.add(loc)
                count += 1
    
    try:
        db.commit()
        print(f"Successfully added {count} locations.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")

if __name__ == "__main__":
    populate_locations()
