# 🖥️💻 Configuration Serveur/Client - Gravity Stock Manager

## 📋 Vue d'Ensemble

L'application Gravity supporte maintenant deux modes de fonctionnement :

- **🖥️ Mode SERVEUR** : Héberge la base de données, crée les tables, importe les emplacements
- **💻 Mode CLIENT** : Se connecte à la base de données existante, ne fait aucune modification structurelle

## 🎯 Pourquoi Cette Distinction ?

Dans une installation multi-postes :
- Un seul PC doit créer les tables PostgreSQL
- Les autres PC doivent simplement se connecter à la base existante
- Évite les conflits et duplications de données

## 🚀 Fonctionnement

### Premier Lancement

Au tout premier lancement de l'application, une boîte de dialogue s'affiche :

```
⚙️ Configuration du Type de Poste

Ce PC sera-t-il utilisé comme serveur ou client ?

📌 SERVEUR :
• Héberge la base de données PostgreSQL
• Crée les tables et importe les emplacements
• Un seul PC serveur par installation

💻 CLIENT :
• Se connecte à la base de données du serveur
• Ne crée pas de tables
• Plusieurs PC clients peuvent se connecter

[🖥️ Serveur]  [💻 Client]
```

### Choix SERVEUR 🖥️

Lorsque l'utilisateur sélectionne "Serveur" :

1. ✅ Création du fichier `server_config.json` avec `{"is_server": true}`
2. ✅ Création de toutes les tables PostgreSQL
3. ✅ Import automatique des emplacements depuis `emplacements_a_importer.xlsx`
4. ✅ Message dans les logs : `🖥️ SERVER MODE: Creating database tables...`

### Choix CLIENT 💻

Lorsque l'utilisateur sélectionne "Client" :

1. ✅ Création du fichier `server_config.json` avec `{"is_server": false}`
2. ✅ Vérification de la connexion à la base de données existante
3. ❌ Aucune création de tables
4. ❌ Aucun import d'emplacements
5. ✅ Message dans les logs : `💻 CLIENT MODE: Connecting to existing database...`

## 📁 Fichier de Configuration

### Emplacement
`server_config.json` (à la racine de l'application)

### Contenu
```json
{
    "is_server": true
}
```
ou
```json
{
    "is_server": false
}
```

### Important
- Ce fichier est créé automatiquement au premier lancement
- Il est exclu de Git (`.gitignore`)
- **Chaque PC aura son propre fichier de configuration**

## 🔄 Modifier la Configuration

Pour reconfigurer un PC (passer de serveur à client ou vice-versa) :

### Méthode 1 : Supprimer le fichier
1. Fermer l'application
2. Supprimer le fichier `server_config.json`
3. Relancer l'application
4. La boîte de dialogue apparaîtra à nouveau

### Méthode 2 : Éditer manuellement
1. Fermer l'application
2. Ouvrir `server_config.json` avec un éditeur de texte
3. Changer `true` en `false` (ou vice-versa)
4. Sauvegarder et relancer l'application

## 🏢 Scénario d'Installation Multi-Postes

### Configuration Recommandée

**PC 1 (Serveur - Pharmacie principale)** :
```
1. Installer PostgreSQL localement
2. Lancer l'application
3. Sélectionner "Serveur"
4. Les tables sont créées
5. Les 240 emplacements sont importés
```

**PC 2, 3, 4... (Clients)** :
```
1. Modifier config.py pour pointer vers le PC serveur :
   DB_HOST = "192.168.1.100"  # IP du PC serveur
2. Lancer l'application
3. Sélectionner "Client"
4. Connexion à la base du serveur
```

### Exemple de Configuration Réseau

**config.py sur PC SERVEUR :**
```python
DB_HOST = "localhost"  # Base locale
DB_PORT = "5432"
DB_NAME = "gravity_db"
```

**config.py sur PC CLIENT :**
```python
DB_HOST = "192.168.1.100"  # IP du serveur
DB_PORT = "5432"
DB_NAME = "gravity_db"
```

## 🔍 Détection du Mode

Le système détecte automatiquement le mode via :

```python
from server_config import is_server_mode

mode = is_server_mode()
# Returns:
#   True  = Mode serveur
#   False = Mode client
#   None  = Non configuré (premier lancement)
```

## 📝 Logs à Surveiller

### En Mode Serveur
```
INFO:__main__:Initializing database...
INFO:database.connection:🖥️ SERVER MODE: Creating database tables...
INFO:database.connection:PostgreSQL tables created.
INFO:database.connection:Auto-import: Reading locations from 'emplacements_a_importer.xlsx'...
INFO:database.connection:✅ Auto-import: Successfully imported 240 locations
```

### En Mode Client
```
INFO:__main__:Initializing database...
INFO:database.connection:💻 CLIENT MODE: Connecting to existing database...
INFO:database.connection:Successfully connected to database.
```

## ⚠️ Erreurs Courantes

### "Server mode not configured yet"
- **Cause** : Le fichier `server_config.json` n'existe pas
- **Solution** : Normal au premier lancement, la boîte de dialogue s'affichera

### "Failed to connect to database" (Mode Client)
- **Cause** : Ne peut pas se connecter au serveur PostgreSQL
- **Solutions** :
  - Vérifier que PostgreSQL tourne sur le serveur
  - Vérifier l'IP dans `config.py`
  - Vérifier le pare-feu (port 5432 ouvert)
  - Vérifier que PostgreSQL accepte les connexions réseau

### Tables manquantes (Mode Client)
- **Cause** : Le serveur n'a jamais été configuré en mode serveur
- **Solution** : Configurer d'abord le PC principal en mode serveur

## 🎯 Recommandations

1. **Toujours configurer le PC principal en SERVEUR en premier**
2. **Vérifier la connexion réseau avant de configurer les clients**
3. **Documenter quel PC est le serveur**
4. **Sauvegarder régulièrement la base PostgreSQL du serveur**
5. **Ne pas changer un serveur en client après la configuration initiale**

---

**Version :** 1.0  
**Créé le :** 2025-12-03  
**Mis à jour :** 2025-12-03
