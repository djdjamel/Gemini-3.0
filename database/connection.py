from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import config
import pyodbc
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL Connection
try:
    pg_engine = create_engine(config.POSTGRES_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
except Exception as e:
    logger.error(f"Error creating PostgreSQL engine: {e}")
    pg_engine = None
    SessionLocal = None

def init_db():
    if pg_engine:
        Base.metadata.create_all(bind=pg_engine)
        logger.info("PostgreSQL tables created.")
        
        # Populate locations if empty
        from populate_locations import populate_locations
        populate_locations()

def get_db():
    if not SessionLocal:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQL Server Connection (XpertPharm)
def get_xpertpharm_connection():
    try:
        conn = pyodbc.connect(config.SQL_SERVER_CONNECTION_STRING)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to SQL Server: {e}")
        return None

def get_product_from_xpertpharm(barcode):
    conn = get_xpertpharm_connection()
    if not conn:
        return None
    
    query = """
    select ST.[ID_STOCK] ID_STOCK,ST.[CODE_PRODUIT] CODE_PRODUIT,ST.[QUANTITE]  QUANTITE ,ST.[LOT] LOT ,ST.[DATE_PEREMPTION] expiry_date ,ST.[CODE_BARRE_LOT] barcode ,ST.[CREATED_ON] CREATED_ON  ,[XPERTPHARM5_7091_BOURENANE].dbo.GET_DESIGNATION_PRODUIT(p.DESIGNATION, p.DOSAGE, p.UNITE, p.CONDIT, f.DESIGNATION) AS designation  FROM [XPERTPHARM5_7091_BOURENANE].[dbo].[STK_STOCK] ST  INNER JOIN [XPERTPHARM5_7091_BOURENANE].[dbo].[STK_PRODUITS] p ON ST.CODE_PRODUIT = p.CODE_PRODUIT  LEFT JOIN [XPERTPHARM5_7091_BOURENANE].[dbo].[BSE_PRODUIT_FORMES] f ON f.CODE=p.CODE_FORME WHERE ST.[CODE_BARRE_LOT] = ?
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, barcode)
        row = cursor.fetchone()
        if row:
            # Map result to a dictionary
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Error querying XpertPharm: {e}")
        return None
    finally:
        conn.close()
