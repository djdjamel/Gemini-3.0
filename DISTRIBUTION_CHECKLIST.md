# Checklist de Distribution - Gravity Stock Manager

## ✅ Avant d'Envoyer à Votre Ami

### Fichiers à Inclure dans le ZIP :
- [ ] `GravityStockManager.exe` (dans le dossier `dist/`)
- [ ] `config.py` (exemple de configuration)
- [ ] `README.md` (guide complet)
- [ ] `LISEZMOI.txt` (démarrage rapide)
- [ ] Dossier `assets/` (si vous avez des images/icônes)

### Vérifications Importantes :
- [ ] L'exécutable se lance correctement sur VOTRE machine
- [ ] Tester avec une base PostgreSQL vierge pour simuler la première installation
- [ ] Vérifier que `config.py` contient des exemples (pas vos vrais mots de passe !)
- [ ] Ajouter une note sur les prérequis (PostgreSQL, accès XpertPharm)

### Informations à Communiquer à Votre Ami :
1. **PostgreSQL** :
   - Version minimale : 14
   - Doit créer une base de données `gravity_db`
   - Doit créer un utilisateur avec les droits appropriés

2. **XpertPharm** :
   - Nom/adresse du serveur
   - Nom de la base de données
   - Identifiants d'accès (si authentification SQL)

3. **Imprimante** :
   - Modèle : Brother QL-820NWB
   - Pilote à télécharger sur le site Brother
   - Connexion USB ou réseau

### Fichiers Générés par PyInstaller (Ne PAS Inclure) :
- `build/` (dossier temporaire)
- `__pycache__/` (cache Python)
- `*.spec` (fichier de configuration PyInstaller)
- `gravity.log` (logs de votre utilisation)

### Commande pour Créer le ZIP :
Aller dans le dossier `dist/` et créer une archive avec :
- GravityStockManager.exe
- config.py (EXEMPLE)
- README.md
- LISEZMOI.txt
- assets/ (si existe)

Nom suggéré : `GravityStockManager_v1.0_Setup.zip`

## 📞 Support Post-Installation

Préparez-vous à aider votre ami pour :
- Configuration PostgreSQL (création de base, utilisateur)
- Configuration `config.py` (paramètres réseau, mots de passe)
- Test de connexion XpertPharm
- Configuration de l'imprimante

## 🔄 Mises à Jour Futures

Pour les mises à jour :
1. Recompiler avec PyInstaller
2. Envoyer UNIQUEMENT le nouveau `.exe`
3. Demander à votre ami de NE PAS remplacer le `config.py` existant
