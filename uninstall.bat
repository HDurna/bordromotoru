@echo off
chcp 65001 >nul 2>&1
title Bordro Motoru - Kaldirma
color 0C

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║                                              ║
echo  ║     🧮  BORDRO MOTORU                       ║
echo  ║         Kaldirma Sihirbazi                   ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.

set INSTALL_DIR=%LOCALAPPDATA%\BordroMotoru

if not exist "%INSTALL_DIR%" (
    echo  ℹ️  Bordro Motoru zaten kurulu degil.
    pause
    exit /b 0
)

set /p CONFIRM="  Bordro Motoru'nu kaldirmak istiyor musunuz? (E/H): "
if /i not "%CONFIRM%"=="E" (
    echo  İptal edildi.
    pause
    exit /b 0
)

echo.
echo  [1/3] Uygulama dosyalari siliniyor...
rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
echo  ✅ Dosyalar silindi.

echo  [2/3] Masaustu kisayolu siliniyor...
del "%USERPROFILE%\Desktop\Bordro Motoru.lnk" >nul 2>&1
echo  ✅ Kisayol silindi.

echo  [3/3] Baslangic menusu kisayolu siliniyor...
rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Bordro Motoru" >nul 2>&1
echo  ✅ Baslangic menusu temizlendi.

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║                                              ║
echo  ║  ✅ Bordro Motoru basariyla kaldirildi.      ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
