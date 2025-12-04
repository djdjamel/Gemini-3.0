@echo off
chcp 65001 >nul
echo ========================================
echo Vérification des Dépendances Gravity
echo ========================================
echo.

echo [1/4] Vérification de Windows...
ver | findstr /i "10\." >nul 2>&1
if %errorlevel% == 0 (
    echo    ✅ Windows 10 détecté
) else (
    ver | findstr /i "11\." >nul 2>&1
    if %errorlevel% == 0 (
        echo    ✅ Windows 11 détecté
    ) else (
        echo    ❌ Windows 10/11 NON détecté
        echo    ⚠️  L'application nécessite Windows 10 ou 11
    )
)

echo [2/4] Vérification PostgreSQL...
set PG_FOUND=0

REM Méthode 1: Vérifier dans le PATH
where psql >nul 2>&1
if %errorlevel% == 0 (
    set PG_FOUND=1
    echo    ✅ PostgreSQL installé ^(détecté dans PATH^)
    for /f "tokens=*" %%i in ('psql --version 2^>nul') do echo       %%i
    goto :pg_done
)

REM Méthode 2: Vérifier dans le registre
reg query "HKLM\SOFTWARE\PostgreSQL\Installations" >nul 2>&1
if %errorlevel% == 0 (
    set PG_FOUND=1
    echo    ✅ PostgreSQL installé ^(détecté dans registre^)
    for /f "skip=2 tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\PostgreSQL\Installations" /s /v "Version" 2^>nul ^| findstr "Version"') do (
        echo       Version: %%b
        goto :pg_done
    )
)

REM Méthode 3: Vérifier dans les chemins d'installation courants
if exist "C:\Program Files\PostgreSQL\*" (
    set PG_FOUND=1
    echo    ✅ PostgreSQL installé ^(détecté dans C:\Program Files\PostgreSQL^)
    for /d %%d in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%d\bin\psql.exe" (
            echo       Trouvé dans: %%d
            goto :pg_done
        )
    )
)

if %PG_FOUND% == 0 (
    echo    ❌ PostgreSQL NON installé
    echo       Télécharger: https://www.postgresql.org/download/windows/
)

:pg_done

echo [3/4] Vérification ODBC Driver for SQL Server...
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server" >nul 2>&1
if %errorlevel% == 0 (
    echo    ✅ ODBC Driver 17 installé
) else (
    reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server" >nul 2>&1
    if %errorlevel% == 0 (
        echo    ✅ ODBC Driver 18 installé
    ) else (
        echo    ❌ ODBC Driver NON installé
        echo       Télécharger: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
    )
)

echo [4/4] Vérification Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% == 0 (
    echo    ✅ Visual C++ Redistributable installé
) else (
    echo    ⚠️  Visual C++ Redistributable peut être manquant
    echo       Télécharger si nécessaire: https://aka.ms/vs/17/release/vc_redist.x64.exe
)

echo.
echo ========================================
echo Vérification terminée
echo ========================================
echo.
pause
