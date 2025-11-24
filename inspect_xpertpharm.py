from database.connection import get_xpertpharm_connection

def inspect_columns():
    conn = get_xpertpharm_connection()
    if not conn:
        print("Could not connect to XpertPharm.")
        return

    try:
        cursor = conn.cursor()
        # Query to get column names for STK_STOCK
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'STK_STOCK'
        ORDER BY COLUMN_NAME
        """
        cursor.execute(query)
        columns = [row[0] for row in cursor.fetchall()]
        print("Columns in STK_STOCK:")
        for col in columns:
            print(f"- {col}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_columns()
