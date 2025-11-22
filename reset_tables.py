from database.connection import get_db, pg_engine
from database.models import Base, SupplyList, SupplyListItem
from sqlalchemy import text

def reset_supply_tables():
    if not pg_engine:
        print("No PostgreSQL engine.")
        return

    print("Dropping supply_list_items and supply_lists tables...")
    with pg_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS supply_list_items CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS supply_lists CASCADE"))
        conn.commit()
    
    print("Recreating tables...")
    Base.metadata.create_all(bind=pg_engine)
    print("Tables recreated successfully.")

if __name__ == "__main__":
    reset_supply_tables()
