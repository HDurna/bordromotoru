@echo off
chcp 65001 >nul 2>&1
title Bordro Motoru - Kurulum
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║                                              ║
echo  ║     🧮  BORDRO MOTORU v1.0.0                ║
echo  ║         Kurulum Sihirbazi                    ║
echo  ║                                              ║
echo  ║     Gelistirici: Hikmet Durna                ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ===== PYTHON KONTROLÜ =====
echo  [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ❌ Python bulunamadi!
    echo  Lutfen Python 3.10+ yukleyin: https://www.python.org/downloads/
    echo  Kurulumda "Add Python to PATH" secenegini isaretlemeyi unutmayin!
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  ✅ Python %PYVER% bulundu.

:: ===== KURULUM DIZINI =====
echo  [2/5] Kurulum dizini hazirlaniyor...
set INSTALL_DIR=%LOCALAPPDATA%\BordroMotoru
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo  📁 Konum: %INSTALL_DIR%

:: ===== DOSYALARI KOPYALA =====
echo  [3/5] Dosyalar kopyalaniyor...
xcopy /E /I /Y /Q "%~dp0core" "%INSTALL_DIR%\core" >nul 2>&1
xcopy /E /I /Y /Q "%~dp0data" "%INSTALL_DIR%\data" >nul 2>&1
xcopy /E /I /Y /Q "%~dp0templates" "%INSTALL_DIR%\templates" >nul 2>&1
xcopy /E /I /Y /Q "%~dp0static" "%INSTALL_DIR%\static" >nul 2>&1
copy /Y "%~dp0desktop_app.py" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "%~dp0app.py" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "%~dp0cli.py" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "%~dp0requirements.txt" "%INSTALL_DIR%\" >nul 2>&1
echo  ✅ Dosyalar kopyalandi.

:: ===== BAĞIMLILIKLAR =====
echo  [4/5] Python kutuphaneleri yukleniyor (bu biraz surabilir)...
pip install -q -r "%INSTALL_DIR%\requirements.txt" >nul 2>&1
if %errorlevel% neq 0 (
    echo  ⚠️ Kutuphane yukleme hatasi. Manuel olarak deneyin:
    echo     pip install -r requirements.txt
    pause
    exit /b 1
)
echo  ✅ Kutuphaneler yuklendi.

:: ===== MASAÜSTÜ KISAYOLU =====
echo  [5/5] Masaustu kisayolu olusturuluyor...

:: VBScript ile lnk kısayolu oluştur (güvenli, AV tetiklemez)
set SHORTCUT_VBS=%TEMP%\create_shortcut.vbs
(
echo Set WshShell = WScript.CreateObject^("WScript.Shell"^)
echo Set lnk = WshShell.CreateShortcut^(WshShell.SpecialFolders^("Desktop"^) ^& "\Bordro Motoru.lnk"^)
echo lnk.TargetPath = "pythonw.exe"
echo lnk.Arguments = """%INSTALL_DIR%\desktop_app.py"""
echo lnk.WorkingDirectory = "%INSTALL_DIR%"
echo lnk.Description = "Bordro Motoru - Bordro Hesaplama ve Analiz"
echo lnk.Save
) > "%SHORTCUT_VBS%"
cscript //nologo "%SHORTCUT_VBS%" >nul 2>&1
del "%SHORTCUT_VBS%" >nul 2>&1
echo  ✅ Masaustu kisayolu olusturuldu.

:: ===== BAŞLANGIÇ MENÜSÜ KISAYOLU =====
set START_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Bordro Motoru
if not exist "%START_DIR%" mkdir "%START_DIR%"
set STARTMENU_VBS=%TEMP%\create_startmenu.vbs
(
echo Set WshShell = WScript.CreateObject^("WScript.Shell"^)
echo Set lnk = WshShell.CreateShortcut^("%START_DIR%\Bordro Motoru.lnk"^)
echo lnk.TargetPath = "pythonw.exe"
echo lnk.Arguments = """%INSTALL_DIR%\desktop_app.py"""
echo lnk.WorkingDirectory = "%INSTALL_DIR%"
echo lnk.Description = "Bordro Motoru - Bordro Hesaplama ve Analiz"
echo lnk.Save
) > "%STARTMENU_VBS%"
cscript //nologo "%STARTMENU_VBS%" >nul 2>&1
del "%STARTMENU_VBS%" >nul 2>&1

:: ===== TAMAMLANDI =====
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║                                              ║
echo  ║  ✅ Kurulum basariyla tamamlandi!            ║
echo  ║                                              ║
echo  ║  Masaustundeki "Bordro Motoru" simgesine     ║
echo  ║  cift tiklayarak uygulamayi baslatin.        ║
echo  ║                                              ║
echo  ║  Konum: %LOCALAPPDATA%\BordroMotoru          ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.

set /p LAUNCH="  Uygulamayi simdi baslatmak ister misiniz? (E/H): "
if /i "%LAUNCH%"=="E" (
    echo  🚀 Uygulama baslatiliyor...
    start "" pythonw "%INSTALL_DIR%\desktop_app.py"
)

echo.
echo  Pencereyi kapatabilirsiniz.
pause >nul
