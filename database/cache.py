from PyQt6.QtCore import QObject, pyqtSignal, QThread
import pandas as pd
from database.connection import get_all_products_from_xpertpharm
import logging

logger = logging.getLogger(__name__)

class CacheLoaderThread(QThread):
    loaded = pyqtSignal(object) # Emits DataFrame

    def run(self):
        try:
            data = get_all_products_from_xpertpharm()
            if data:
                df = pd.DataFrame(data)
                # Ensure columns are what we expect
                if 'CODE_PRODUIT' in df.columns and 'designation' in df.columns:
                    self.loaded.emit(df)
                else:
                    logger.error("Cache loader: Missing columns in data")
                    self.loaded.emit(pd.DataFrame())
            else:
                self.loaded.emit(pd.DataFrame())
        except Exception as e:
            logger.error(f"Cache loader error: {e}")
            self.loaded.emit(pd.DataFrame())

class ProductCache(QObject):
    _instance = None
    cache_updated = pyqtSignal()
    
    @staticmethod
    def instance():
        if ProductCache._instance is None:
            ProductCache._instance = ProductCache()
        return ProductCache._instance

    def __init__(self):
        super().__init__()
        self.products_df = pd.DataFrame()
        self.is_loading = False
        self._loader_thread = None

    def load_cache(self):
        if self.is_loading:
            return
        
        logger.info("Starting product cache load...")
        self.is_loading = True
        self._loader_thread = CacheLoaderThread()
        self._loader_thread.loaded.connect(self._on_cache_loaded)
        self._loader_thread.start()

    def reload_cache(self):
        logger.info("Reloading product cache...")
        self.load_cache()

    def _on_cache_loaded(self, df):
        self.products_df = df
        self.is_loading = False
        logger.info(f"Product cache loaded. {len(self.products_df)} products.")
        self.cache_updated.emit()

    def search(self, query):
        """
        Search for products matching the query (case-insensitive).
        Returns a list of tuples (code, designation).
        """
        if self.products_df.empty:
            return []
        
        if not query:
            return []

        try:
            # Filter
            mask = self.products_df['designation'].str.contains(query, case=False, na=False) | \
                   self.products_df['CODE_PRODUIT'].str.contains(query, case=False, na=False)
            
            results = self.products_df[mask].head(50) # Limit results
            return list(zip(results['CODE_PRODUIT'], results['designation']))
        except Exception as e:
            logger.error(f"Cache search error: {e}")
            return []

    def get_all_products(self):
        if self.products_df.empty:
            return []
        return list(zip(self.products_df['CODE_PRODUIT'], self.products_df['designation']))
