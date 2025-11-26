from database.connection import pg_engine as engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('missing_items')]
print(f"Columns in missing_items: {columns}")
