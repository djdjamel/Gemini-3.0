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

from contextlib import contextmanager

@contextmanager
def get_db():
    if not SessionLocal:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_event(event_type, details=None, source=None):
    """Helper to log events to the database"""
    from .models import EventLog
    try:
        with get_db() as db:
            if db:
                log = EventLog(
                    event_type=event_type,
                    details=str(details) if details else None,
                    source=source
                )
                db.add(log)
                db.commit()
    except Exception as e:
        logger.error(f"Failed to log event {event_type}: {e}")

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

def get_lots_by_product_code(product_code):
    conn = get_xpertpharm_connection()
    if not conn:
        return []
    
    query = """
    SELECT ST.[QUANTITE], ST.[CODE_BARRE_LOT], ST.[DATE_PEREMPTION], ST.[CREATED_ON] as DATE_ACHAT
    FROM [XPERTPHARM5_7091_BOURENANE].[dbo].[STK_STOCK] ST
    WHERE ST.[CODE_PRODUIT] = ? AND ST.[QUANTITE] > 0
    ORDER BY ST.[DATE_PEREMPTION] ASC
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, product_code)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        logger.error(f"Error querying XpertPharm lots: {e}")
        return []
    finally:
        conn.close()

def get_latest_invoices():
    conn = get_xpertpharm_connection()
    if not conn:
        return []
    
    query = """
    SELECT TOP 20 [CODE_DOC],[DATE_DOC],[CODE_FACTURE],[TYPE_DOC],[TOTAL_TTC],[STATUS_DOC],a.[CREATED_ON] ,[NOM_TIERS] 
    From [XPERTPHARM5_7091_BOURENANE].[dbo].[ACH_DOCUMENT] a  
    inner join [XPERTPHARM5_7091_BOURENANE].[dbo].[TRS_TIERS]  t on a.CODE_TIERS = t.CODE_TIERS  
    Where  [NOM_TIERS] != 'ARRIVAGE'  
    Order by [CREATED_ON] desc
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        logger.error(f"Error querying XpertPharm invoices: {e}")
        return []
    finally:
        conn.close()

def get_invoice_details(code_doc):
    conn = get_xpertpharm_connection()
    if not conn:
        return []
    
    query = """
    select ST.[ID_STOCK] ID_STOCK,ST.[CODE_PRODUIT] CODE_PRODUIT,ST.[QUANTITE]  QUANTITE ,ST.[LOT] LOT ,ST.[DATE_PEREMPTION] DATE_PEREMPTION ,ST.[CODE_BARRE_LOT] CODE_BARRE_LOT ,ST.[CREATED_ON] CREATED_ON , ST.DESIGNATION_PRODUIT AS DESIGNATION_PRODUIT   
    FROM [XPERTPHARM5_7091_BOURENANE].[dbo].[View_ACH_DOCUMENT_DETAIL] ST  
    WHERE ST.[CODE_DOC] = ?    
    ORDER BY DESIGNATION_PRODUIT 
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, code_doc)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        logger.error(f"Error querying XpertPharm invoice details: {e}")
        return []
    finally:
        conn.close()

def check_newer_barcodes(barcode, product_code, created_on):
    """Check if there are newer barcodes for the same product.
    
    Args:
        barcode: The scanned barcode
        product_code: The product code
        created_on: The creation date of the scanned barcode
        
    Returns:
        int: Count of newer barcodes (with created_on >= scanned barcode's date)
    """
    conn = get_xpertpharm_connection()
    if not conn:
        return 0
    
    query = """
    SELECT COUNT(*) as newer_count
    FROM [XPERTPHARM5_7091_BOURENANE].[dbo].[STK_STOCK]
    WHERE [CODE_PRODUIT] = ? 
    AND [CREATED_ON] >= ?
    AND [CODE_BARRE_LOT] != ?
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (product_code, created_on, barcode))
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0
    except Exception as e:
        logger.error(f"Error checking newer barcodes: {e}")
        return 0
    finally:
        conn.close()

def get_all_products_from_xpertpharm():
    """Fetch all products (Code, Designation) from XpertPharm for caching."""
    conn = get_xpertpharm_connection()
    if not conn:
        return []
    
    query = """
    SELECT p.CODE_PRODUIT, 
           [XPERTPHARM5_7091_BOURENANE].dbo.GET_DESIGNATION_PRODUIT(p.DESIGNATION, p.DOSAGE, p.UNITE, p.CONDIT, f.DESIGNATION) AS designation 
    FROM [XPERTPHARM5_7091_BOURENANE].[dbo].[STK_PRODUITS] p 
    LEFT JOIN [XPERTPHARM5_7091_BOURENANE].[dbo].[BSE_PRODUIT_FORMES] f ON f.CODE=p.CODE_FORME
    WHERE p.ACTIF = 1
    ORDER BY designation
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        logger.error(f"Error fetching all products from XpertPharm: {e}")
        return []
    finally:
        conn.close()
