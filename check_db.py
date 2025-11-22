import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import config
import sys

def fix_database():
    default_uri = config.POSTGRES_URI.rsplit('/', 1)[0] + '/postgres'
    
    try:
        # Connect to default DB
        conn = psycopg2.connect(default_uri)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Try connecting to target DB
        try:
            print(f"Connecting to {config.PG_DB}...")
            conn_target = psycopg2.connect(config.POSTGRES_URI)
            conn_target.close()
            print("Connection successful!")
            return True
        except psycopg2.OperationalError:
            print("Connection to target DB failed. Recreating...")
            
            # Drop and Recreate
            try:
                cur.execute(f"DROP DATABASE IF EXISTS {config.PG_DB};")
                cur.execute(f"CREATE DATABASE {config.PG_DB};")
                print("Database recreated.")
                return True
            except Exception as e:
                print(f"Recreation failed: {e}")
                return False
        finally:
            conn.close()

    except Exception as e:
        print(f"Critical error: {e}")
        return False

if __name__ == "__main__":
    fix_database()
