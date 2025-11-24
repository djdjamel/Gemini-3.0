from database.connection import pg_engine as engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Create Nomenclature Table
            print("Creating 'nomenclature' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS nomenclature (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    designation VARCHAR(255) NOT NULL,
                    last_supply_date TIMESTAMP,
                    last_search_date TIMESTAMP,
                    last_edit_date TIMESTAMP
                );
            """))
            
            # 2. Populate Nomenclature from Products
            print("Populating 'nomenclature' from 'products'...")
            # We take the MAX last_supply_date and an arbitrary designation (MAX) for each code
            conn.execute(text("""
                INSERT INTO nomenclature (code, designation, last_supply_date)
                SELECT code, MAX(designation), MAX(last_supply_date)
                FROM products
                GROUP BY code
                ON CONFLICT (code) DO NOTHING;
            """))
            
            # 3. Drop Columns from Products
            print("Dropping columns from 'products'...")
            conn.execute(text("ALTER TABLE products DROP COLUMN IF EXISTS designation"))
            conn.execute(text("ALTER TABLE products DROP COLUMN IF EXISTS last_supply_date"))
            
            # 4. Add Foreign Key Constraint
            print("Adding FK constraint...")
            # Ensure all codes in products exist in nomenclature (should be true by step 2)
            conn.execute(text("""
                ALTER TABLE products 
                ADD CONSTRAINT fk_products_nomenclature 
                FOREIGN KEY (code) REFERENCES nomenclature(code);
            """))
            
            trans.commit()
            print("Migration successful!")
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
