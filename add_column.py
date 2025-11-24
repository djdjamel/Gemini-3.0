from database.connection import get_db, pg_engine as engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN last_supply_date TIMESTAMP"))
            conn.commit()
            print("Column 'last_supply_date' added successfully.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    add_column()
