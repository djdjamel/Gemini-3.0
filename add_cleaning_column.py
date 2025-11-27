from database.connection import pg_engine
from sqlalchemy import text
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column():
    if not pg_engine:
        logger.error("No PostgreSQL engine available.")
        return

    with pg_engine.connect() as conn:
        try:
            # Check if column exists
            check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='cleaning';")
            result = conn.execute(check_query).fetchone()
            
            if not result:
                logger.info("Adding cleaning column to products table...")
                conn.execute(text("ALTER TABLE products ADD COLUMN cleaning BOOLEAN DEFAULT FALSE;"))
                conn.commit()
                logger.info("Column added successfully.")
            else:
                logger.info("Column cleaning already exists.")
                
        except Exception as e:
            logger.error(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
