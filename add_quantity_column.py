from database.connection import pg_engine as engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE missing_items ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1"))
        conn.commit()
        print("Column 'quantity' added to 'missing_items'.")

if __name__ == "__main__":
    add_column()
