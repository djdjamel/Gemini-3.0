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
            # This is a bit tricky in raw SQL across DBs, but for Postgres:
            check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='missing_items' AND column_name='is_deleted';")
            result = conn.execute(check_query).fetchone()
            
            if not result:
                logger.info("Adding is_deleted column to missing_items table...")
                conn.execute(text("ALTER TABLE missing_items ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;"))
                conn.commit()
                logger.info("Column added successfully.")
            else:
                logger.info("Column is_deleted already exists.")
                
        except Exception as e:
            logger.error(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
