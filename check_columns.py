from database.connection import pg_engine as engine
from sqlalchemy import text

def check_columns():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'products'"))
        columns = [row[0] for row in result]
        print(f"Columns in products: {columns}")

if __name__ == "__main__":
    check_columns()
