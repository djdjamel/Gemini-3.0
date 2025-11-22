import pandas as pd

try:
    df = pd.read_excel("liste.xlsx")
    print("Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].to_dict() if not df.empty else "Empty")
    print("Data Types:", df.dtypes)
except Exception as e:
    print(f"Error reading excel: {e}")
