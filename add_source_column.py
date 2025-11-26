from database.connection import pg_engine as engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE missing_items ADD COLUMN source VARCHAR(50) DEFAULT 'Inconnu'"))
        conn.commit()
        print("Column 'source' added to 'missing_items'.")
    except Exception as e:
        print(f"Error (maybe column exists?): {e}")
