from database.connection import pg_engine as engine
from database.models import Base

Base.metadata.create_all(bind=engine)
print("Tables created/updated.")
