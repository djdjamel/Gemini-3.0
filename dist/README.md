# Gravity Stock Manager - Guide d'Installation

## 📋 Prérequis Système

### Logiciels Requis :
- **Windows 10/11** (64-bit)
- **PostgreSQL 14+** (serveur de base de données)
- **SQL Server** ou accès à **XpertPharm** (base de données pharmacie)
- **Imprimante Brother QL-820NWB** (pour l'impression d'étiquettes)

### Pilotes :
- Pilote d'imprimante Brother QL-820NWB installé et configuré

##  🚀 Installation Rapide

### 1. Extraction
- Extraire le fichier ZIP dans un dossier de votre choix
- Exemple : `C:\GravityStockManager\`

### 2. Configuration PostgreSQL
Avant le premier lancement, créer une base de données PostgreSQL :

```sql
-- Ouvrir pgAdmin ou psql
CREATE DATABASE gravity_db;
CREATE USER gravity_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE gravity_db TO gravity_user;
```

### 3. Configuration des Connexions
Ouvrir le fichier `config.py` et modifier les paramètres :

```python
# === PostgreSQL (Base de données locale) ===
DB_HOST = "localhost"           # Adresse de votre serveur PostgreSQL
DB_PORT = "5432"                # Port PostgreSQL (5432 par défaut)
DB_USER = "gravity_user"        # Utilisateur PostgreSQL
DB_PASSWORD = "votre_mot_de_passe"  # Mot de passe
DB_NAME = "gravity_db"          # Nom de la base de données

# === XpertPharm (SQL Server) ===
XPERTPHARM_SERVER = "VOTRE_SERVEUR\\XPERTPHARM"  # Adresse du serveur XpertPharm
XPERTPHARM_DATABASE = "XPERTPHARM5_7091_BOURENANE"  # Nom de la base
XPERTPHARM_USER = "votre_utilisateur"  # Si authentification SQL Server
XPERTPHARM_PASSWORD = "votre_mot_de_passe"  # Si authentification SQL Server
```

### 4. Premier Lancement
1. Double-cliquer sur `GravityStockManager.exe`
2. L'application créera automatiquement toutes les tables nécessaires
3. Au premier lancement, un message confirmera la création des tables

## 🔐 Accès aux Onglets Protégés

Certains onglets nécessitent un mot de passe :
- **Statistiques**
- **Rotation**
- **Paramètres**

**Mot de passe :** L'heure actuelle au format HHMM
- Exemple : S'il est **14:35**, le mot de passe est **1435**
- Le mot de passe change automatiquement chaque minute

## 📌 Configuration Initiale

### Importer les Emplacements
1. Aller dans l'onglet **Emplacements**
2. Utiliser le bouton "Importer" pour charger vos emplacements depuis un fichier Excel

### Connecter l'Imprimante
1. Aller dans l'onglet **Paramètres**
2. Vérifier que l'imprimante Brother QL-820NWB est détectée
3. Sélectionner la bonne largeur d'étiquette (62mm recommandé)

## 🔧 Dépannage

### Erreur de Connexion PostgreSQL
- Vérifier que PostgreSQL est démarré (Services Windows)
- Vérifier les paramètres dans `config.py`
- Tester la connexion avec pgAdmin

### Erreur de Connexion XpertPharm
- Vérifier l'accès réseau au serveur XpertPharm
- Vérifier les identifiants dans `config.py`
- Contacter l'administrateur réseau si nécessaire

### L'Imprimante ne Fonctionne Pas
- Vérifier que l'imprimante est allumée et connectée (USB ou réseau)
- Installer/réinstaller le pilote Brother
- Redémarrer l'application

### L'Application ne Démarre Pas
- Vérifier que tous les fichiers ont été extraits correctement
- Exécuter en tant qu'administrateur (clic droit → "Exécuter en tant qu'administrateur")
- Consulter les logs dans le fichier `gravity.log`

## 📞 Support

Pour toute question ou problème :
- Consulter la documentation complète
- Vérifier le fichier `gravity.log` pour les erreurs
- Contacter le support technique

## 🎯 Raccourcis Clavier

- **F12** : Ouvrir/Fermer la recherche comptoir (recherche rapide flottante)

## 📝 Notes Importantes

1. **Sauvegarde** : Les données sont stockées dans PostgreSQL. Pensez à sauvegarder régulièrement votre base de données.
2. **Mises à jour** : Remplacer uniquement le fichier `.exe` lors des mises à jour (conserver `config.py` et le dossier `assets/`)
3. **Multi-postes** : Plusieurs postes peuvent utiliser la même base PostgreSQL en réseau.

---

**Version :** 1.0  
**Date :** Décembre 2024  
**Créé par :** Gravity Development Team
