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
    """Initialize database - only create tables if in server mode"""
    if not pg_engine:
        return
    
    # Check server mode
    from server_config import is_server_mode
    server_mode = is_server_mode()
    
    if server_mode is None:
        # First run - will be configured in main.py
        logger.info("Server mode not configured yet. Skipping database initialization.")
        return
    
    if server_mode:
        # SERVER MODE: Create tables and import locations
        logger.info("🖥️ SERVER MODE: Creating database tables...")
        Base.metadata.create_all(bind=pg_engine)
        logger.info("PostgreSQL tables created.")
        
        # Auto-import locations if empty and Excel file exists
        auto_import_locations()
    else:
        # CLIENT MODE: Just verify connection, don't create tables
        logger.info("💻 CLIENT MODE: Connecting to existing database...")
        try:
            # Test connection
            with get_db() as db:
                if db:
                    logger.info("Successfully connected to database.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")

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

def auto_import_locations():
    """
    Automatically import locations from Excel file if:
    1. The locations table is empty
    2. The file 'emplacements_a_importer.xlsx' exists
    """
    import os
    import pandas as pd
    from .models import Location
    
    excel_file = 'emplacements_a_importer.xlsx'
    
    # Check if file exists
    if not os.path.exists(excel_file):
        logger.info(f"Auto-import: File '{excel_file}' not found. Skipping auto-import.")
        return
    
    try:
        with get_db() as db:
            if not db:
                return
            
            # Check if locations table is empty
            location_count = db.query(Location).count()
            if location_count > 0:
                logger.info(f"Auto-import: Locations table already contains {location_count} locations. Skipping auto-import.")
                return
            
            # Read Excel file
            logger.info(f"Auto-import: Reading locations from '{excel_file}'...")
            df = pd.read_excel(excel_file)
            
            # Validate columns
            if 'label' not in df.columns or 'barcode' not in df.columns:
                logger.error("Auto-import: Excel file must contain 'label' and 'barcode' columns.")
                return
            
            # Import locations
            imported_count = 0
            for _, row in df.iterrows():
                label = str(row['label']).strip()
                barcode = str(row['barcode']).strip() if pd.notna(row['barcode']) else ''
                
                if label:  # Only import if label is not empty
                    location = Location(label=label, barcode=barcode)
                    db.add(location)
                    imported_count += 1
            
            db.commit()
            logger.info(f"✅ Auto-import: Successfully imported {imported_count} locations from '{excel_file}'")
            print(f"Successfully added {imported_count} locations.")
            
    except Exception as e:
        logger.error(f"Auto-import error: {e}")
        print(f"Auto-import failed: {e}")

def log_event(event_type, details=None, source=None, delay=None):
    """Helper to log events to the database"""
    from .models import EventLog
    import socket
    try:
        with get_db() as db:
            if db:
                log = EventLog(
                    event_type=event_type,
                    details=str(details) if details else None,
                    source=source,
                    machine_name=socket.gethostname(),
                    delay=delay
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
