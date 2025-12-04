# 🔍 Compatibilité et Dépendances - Gravity Stock Manager

## ⚠️ COMPATIBILITÉ WINDOWS

### ❌ Windows 7 - NON COMPATIBLE

**L'application N'EST PAS compatible avec Windows 7** pour les raisons suivantes :

1. **PyQt6** : Nécessite Windows 10 ou supérieur
2. **Python 3.10+** : Support officiel seulement pour Windows 10+
3. **Bibliothèques système** : Certaines API utilisées ne sont pas disponibles sur Windows 7

### ✅ Systèmes Compatibles

- **Windows 10** (toutes versions) ✅
- **Windows 11** ✅
- **Windows Server 2016+** ✅

**Versions 32-bit :** Non supportées (l'exe est compilé en 64-bit uniquement)

---

## 📦 DÉPENDANCES INCLUSES DANS L'EXÉCUTABLE

PyInstaller **inclut automatiquement** toutes ces bibliothèques dans l'exe :

### ✅ Bibliothèques Python Intégrées
- ✅ **PyQt6** - Interface graphique
- ✅ **SQLAlchemy** - ORM base de données
- ✅ **psycopg2-binary** - Connexion PostgreSQL
- ✅ **pyodbc** - Connexion SQL Server/XpertPharm
- ✅ **python-barcode** - Génération codes-barres
- ✅ **reportlab** - Génération PDF
- ✅ **pyttsx3** - Synthèse vocale
- ✅ **pandas** - Manipulation données
- ✅ **openpyxl** - Lecture/écriture Excel
- ✅ **Pillow** - Traitement d'images
- ✅ **numpy** - Calculs scientifiques (dépendance de pandas)

### ✅ Bibliothèques Système Windows
- ✅ **win32com** - Intégration Windows
- ✅ **pywin32** - API Windows
- ✅ **comtypes** - COM Windows

**Résultat :** L'exécutable contient **TOUT** sauf PostgreSQL et les pilotes ODBC.

---

## 🔧 DÉPENDANCES EXTERNES REQUISES

Ces composants **doivent être installés** sur le PC de destination :

### 1. ⚠️ PostgreSQL (OBLIGATOIRE)
**Sur PC Serveur uniquement :**
- Version minimale : **PostgreSQL 14**
- Téléchargement : https://www.postgresql.org/download/windows/
- **Taille :** ~200 MB

**Configuration :**
```
Installer avec les options par défaut
Port : 5432
Créer un superutilisateur
```

### 2. ⚠️ SQL Server ODBC Driver (OBLIGATOIRE si XpertPharm)
**Pour la connexion XpertPharm :**
- **ODBC Driver 17 for SQL Server**
- Téléchargement : https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- **Taille :** ~15 MB

**Vérification :**
```
Panneau de configuration → Outils d'administration → Sources de données ODBC (64 bits)
```

### 3. ℹ️ Brother Printer Driver (OPTIONNEL)
**Si utilisation de l'imprimante Brother QL-820NWB :**
- **Brother QL-820NWB Driver**
- Téléchargement : https://support.brother.com
- **Taille :** ~50 MB

**Note :** L'application fonctionne sans imprimante, mais l'impression d'étiquettes sera désactivée.

### 4. ℹ️ Microsoft Visual C++ Redistributable (GÉNÉRALEMENT PRÉ-INSTALLÉ)
**Peut être nécessaire pour pyodbc et psycopg2 :**
- **Visual C++ Redistributable 2015-2022 (x64)**
- Téléchargement : https://aka.ms/vs/17/release/vc_redist.x64.exe
- **Taille :** ~25 MB

**Vérification :**
La plupart des PC Windows 10/11 l'ont déjà installé.

---

## 🎯 CHECKLIST D'INSTALLATION POUR VOTRE AMI

### Configuration Minimale PC
- ✅ Windows 10 ou 11 (64-bit)
- ✅ 4 GB RAM minimum (8 GB recommandé)
- ✅ 2 GB d'espace disque libre
- ✅ Connexion réseau (pour multi-postes)

### Étapes d'Installation

#### Sur PC SERVEUR :
1. ✅ Installer **PostgreSQL 14+**
2. ✅ Installer **ODBC Driver 17** (si XpertPharm)
3. ✅ Extraire le ZIP de Gravity
4. ✅ Modifier `config.py`
5. ✅ Lancer `GravityStockManager.exe`
6. ✅ Sélectionner "Serveur" au premier lancement

#### Sur PC CLIENT :
1. ✅ Installer **ODBC Driver 17** (si XpertPharm)
2. ✅ Extraire le ZIP de Gravity
3. ✅ Modifier `config.py` (pointer vers le serveur)
4. ✅ Lancer `GravityStockManager.exe`
5. ✅ Sélectionner "Client" au premier lancement

**Note :** PostgreSQL n'est **PAS** nécessaire sur les PC clients.

---

## 🧪 VÉRIFICATION DES DÉPENDANCES

### Script de Test (à créer)
Créez un fichier `test_dependencies.bat` :

```batch
@echo off
echo ========================================
echo Verification des dependances Gravity
echo ========================================
echo.

echo [1/3] Verification PostgreSQL...
where psql >nul 2>&1
if %errorlevel% == 0 (
    echo    [OK] PostgreSQL installe
) else (
    echo    [X] PostgreSQL NON installe
)

echo [2/3] Verification ODBC Driver...
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server" >nul 2>&1
if %errorlevel% == 0 (
    echo    [OK] ODBC Driver 17 installe
) else (
    echo    [X] ODBC Driver 17 NON installe
)

echo [3/3] Verification Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% == 0 (
    echo    [OK] Visual C++ Redistributable installe
) else (
    echo    [?] Visual C++ Redistributable peut-etre manquant
)

echo.
echo Verification terminee.
pause
```

---

## 📊 TAILLE DE L'EXÉCUTABLE

- **GravityStockManager.exe** : ~500 MB
  - PyQt6 : ~200 MB
  - Pandas/NumPy : ~150 MB
  - Autres librairies : ~150 MB

**C'est normal !** Tout est inclus pour fonctionner sans Python.

---

## ❓ FAQ - DÉPENDANCES

### Q: Pourquoi l'exe est si gros (500 MB) ?
**R:** Parce qu'il contient Python complet + toutes les bibliothèques. C'est le prix de l'indépendance (pas besoin d'installer Python).

### Q: Peut-on réduire la taille ?
**R:** Oui, en utilisant `--onedir` au lieu de `--onefile`, mais cela créera un dossier avec plusieurs fichiers (moins pratique).

### Q: Faut-il installer Python sur le PC de destination ?
**R:** **Non !** L'exe contient tout Python. C'est justement l'intérêt de PyInstaller.

### Q: Que se passe-t-il si PostgreSQL n'est pas installé ?
**R:** L'application démarre mais ne peut pas se connecter. Message d'erreur affiché.

### Q: Peut-on utiliser PostgreSQL à distance ?
**R:** **Oui !** Sur les PC clients, il suffit de pointer `DB_HOST` vers le serveur.

### Q: Windows 7 est vraiment incompatible ?
**R:** **Oui, malheureusement.** PyQt6 ne supporte que Windows 10+. Aucune solution de contournement possible.

---

## 🚀 PACKAGE RECOMMANDÉ POUR DISTRIBUTION

Créez un ZIP contenant :
```
GravityStockManager_v1.0/
├── GravityStockManager.exe
├── emplacements_a_importer.xlsx
├── config.py (EXEMPLE, pas vos vrais mots de passe)
├── README.md
├── LISEZMOI.txt
├── DEPENDENCIES.md (ce fichier)
├── test_dependencies.bat
└── Liens_Telechargement.txt
```

**Liens_Telechargement.txt :**
```
TÉLÉCHARGEMENTS NÉCESSAIRES

1. PostgreSQL (PC Serveur uniquement)
   https://www.postgresql.org/download/windows/

2. ODBC Driver 17 for SQL Server
   https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

3. Brother QL-820NWB Driver (optionnel)
   https://support.brother.com

4. Visual C++ Redistributable (si nécessaire)
   https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

**Version :** 1.0  
**Dernière mise à jour :** 2025-12-04  
**Compatibilité :** Windows 10/11 uniquement (64-bit)
