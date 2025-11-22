import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL (Local)
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = os.getenv("PG_PORT", "5432")
    PG_DB = os.getenv("PG_DB", "gravity_stock")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "gigigi2009")

    # SQL Server (XpertPharm)
    SQL_SERVER = os.getenv("SQL_SERVER", "DESKTOP-25MV5BR\SQLEXPRESS")
    SQL_DB = os.getenv("SQL_DB", "XPERTPHARM5_7091_BOURENANE")
    SQL_USER = os.getenv("SQL_USER", "sa")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD", "ounmadhr")
    SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")

    @property
    def POSTGRES_URI(self):
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"

    @property
    def SQL_SERVER_CONNECTION_STRING(self):
        return (
            f"DRIVER={{{self.SQL_DRIVER}}};"
            f"SERVER={self.SQL_SERVER};"
            f"DATABASE={self.SQL_DB};"
            f"UID={self.SQL_USER};"
            f"PWD={self.SQL_PASSWORD}"
        )

config = Config()
