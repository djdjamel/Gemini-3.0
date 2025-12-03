# 🎯 Comment Fonctionne l'Auto-Import des Emplacements

## 📋 Résumé

Votre application **importe automatiquement** les emplacements au premier lancement si le fichier Excel est présent.

## 🔄 Fonctionnement Automatique

### Lors du Premier Lancement (Chez Votre Ami)

1. ✅ L'application démarre
2. ✅ PostgreSQL crée les tables (vides)
3. ✅ Le système détecte que `locations` est vide
4. ✅ Le système cherche le fichier `emplacements_a_importer.xlsx`
5. ✅ **Si trouvé** : Import automatique de tous les emplacements
6. ✅ **Si non trouvé** : Continue normalement (table vide)

### Message de Confirmation

Au lancement, votre ami verra :
```
INFO:database.connection:PostgreSQL tables created.
INFO:database.connection:Auto-import: Reading locations from 'emplacements_a_importer.xlsx'...
INFO:database.connection:✅ Auto-import: Successfully imported 240 locations from 'emplacements_a_importer.xlsx'
Successfully added 240 locations.
```

## 📦 Fichiers à Inclure dans le ZIP

Pour que l'auto-import fonctionne, votre ZIP doit contenir :

```
GravityStockManager/
├── GravityStockManager.exe          ✅
├── emplacements_a_importer.xlsx     ✅ IMPORTANT !
├── config.py                         ✅
├── README.md                         ✅
└── LISEZMOI.txt                      ✅
```

## ⚠️ Points Importants

### 1. Emplacement du Fichier Excel
Le fichier `emplacements_a_importer.xlsx` doit être **dans le même dossier** que l'exécutable.

### 2. Import Unique
L'auto-import se fait **UNE SEULE FOIS** :
- ✅ Si la table `locations` est vide → Import
- ❌ Si la table `locations` contient déjà des emplacements → Aucun import

### 3. Régénérer le Fichier Excel

Si vous ajoutez de nouveaux emplacements, régénérez le fichier :
```bash
python export_locations.py
```
Cela créera un nouveau fichier dans `dist/`

## 🔧 Pour Vous (Développeur)

### Exporter les Emplacements Actuels
```bash
cd C:\Users\acer\Documents\Gravity
python export_locations.py
```

Résultat : `dist/emplacements_a_importer.xlsx` (240 emplacements)

### Recompiler l'Exécutable avec le Fichier Excel
```bash
python -m PyInstaller Gravity.spec --clean
```

Le fichier Excel sera **intégré dans l'exécutable** et extrait automatiquement au premier lancement.

## 🧪 Tester l'Auto-Import

Pour tester sur votre machine :

1. **Créer une nouvelle base de données test :**
```sql
CREATE DATABASE gravity_test;
```

2. **Modifier temporairement config.py :**
```python
DB_NAME = "gravity_test"
```

3. **Placer le fichier Excel dans le dossier de l'exe**

4. **Lancer l'application**

5. **Vérifier les logs** → Doit afficher "Successfully added 240 locations"

## 📞 Dépannage

### "File 'emplacements_a_importer.xlsx' not found"
- Le fichier Excel n'est pas dans le bon dossier
- Solution : Copier le fichier à côté de l'exe

### "Locations table already contains X locations"
- La table n'est pas vide
- Solution : Normal, l'import ne se fait qu'une fois

### "Auto-import failed: ..."
- Problème de lecture du fichier Excel
- Vérifier que le fichier n'est pas corrompu
- Vérifier les colonnes (doivent être `label` et `barcode`)

---

**Version :** 1.0  
**Créé le :** 2025-12-03
