"""
Script pour générer un fichier SQL d'import des emplacements
À exécuter AVANT de créer le package pour votre ami
"""
from database.connection import get_db
from database.models import Location

def generate_sql_import():
    with get_db() as db:
        if not db:
            print("Erreur de connexion à la base de données")
            return
        
        # Récupérer tous les emplacements
        locations = db.query(Location).order_by(Location.id).all()
        
        if not locations:
            print("Aucun emplacement trouvé dans la base de données")
            return
        
        # Générer le fichier SQL
        output_file = 'dist/import_emplacements.sql'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- Script d'importation des emplacements\n")
            f.write("-- À exécuter dans PostgreSQL après l'installation\n\n")
            
            for loc in locations:
                label = loc.label.replace("'", "''")  # Échapper les apostrophes
                barcode = loc.barcode.replace("'", "''") if loc.barcode else ''
                
                f.write(f"INSERT INTO locations (label, barcode) VALUES ('{label}', '{barcode}');\n")
        
        print(f"✅ {len(locations)} emplacements exportés vers {output_file}")
        print(f"\n➡️ Incluez ce fichier dans le ZIP pour votre ami")
        print(f"\n📋 Votre ami pourra l'importer avec pgAdmin ou psql :")
        print(f"   psql -U gravity_user -d gravity_db -f import_emplacements.sql")

if __name__ == "__main__":
    generate_sql_import()
