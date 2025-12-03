import os
import socket
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL (Local)
    PG_HOST = os.getenv("PG_HOST") or "localhost"
    PG_PORT = os.getenv("PG_PORT") or "5432"
    PG_DB = os.getenv("PG_DB") or "gravity_stock"
    PG_USER = os.getenv("PG_USER") or "postgres"
    PG_PASSWORD = os.getenv("PG_PASSWORD") or "gigigi2009"

    # App Settings
    IS_SERVER = os.getenv("IS_SERVER", "false").lower() == "true"
    STATION_NAME = os.getenv("STATION_NAME") or socket.gethostname()

    # SQL Server (XpertPharm)
    SQL_SERVER = os.getenv("SQL_SERVER") or "DESKTOP-25MV5BR\SQLEXPRESS"
    SQL_DB = os.getenv("SQL_DB") or "XPERTPHARM5_7091_BOURENANE"
    SQL_USER = os.getenv("SQL_USER") or "sa"
    SQL_PASSWORD = os.getenv("SQL_PASSWORD") or "ounmadhr"
    SQL_DRIVER = os.getenv("SQL_DRIVER") or "ODBC Driver 17 for SQL Server"

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
