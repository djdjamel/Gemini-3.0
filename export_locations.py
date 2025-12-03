"""
Script pour exporter les emplacements vers Excel
À exécuter AVANT de créer le package pour votre ami
"""
from database.connection import get_db
from database.models import Location
import pandas as pd

def export_locations_to_excel():
    with get_db() as db:
        if not db:
            print("Erreur de connexion à la base de données")
            return
        
        # Récupérer tous les emplacements
        locations = db.query(Location).all()
        
        if not locations:
            print("Aucun emplacement trouvé dans la base de données")
            return
        
        # Créer un DataFrame
        data = []
        for loc in locations:
            data.append({
                'label': loc.label,
                'barcode': loc.barcode
            })
        
        df = pd.DataFrame(data)
        
        # Exporter vers Excel
        output_file = 'dist/emplacements_a_importer.xlsx'
        df.to_excel(output_file, index=False)
        
        print(f"✅ {len(locations)} emplacements exportés vers {output_file}")
        print(f"📋 Colonnes : label, barcode")
        print(f"\n➡️ Incluez ce fichier dans le ZIP pour votre ami")
        print(f"➡️ Il pourra l'importer via l'onglet 'Emplacements'")

if __name__ == "__main__":
    export_locations_to_excel()
