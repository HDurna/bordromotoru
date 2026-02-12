import PyInstaller.__main__
import os
import shutil

# Daha önceki buildleri temizle
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

print("🚀 Bordro Motoru derleniyor...")

# PyInstaller parametreleri
PyInstaller.__main__.run([
    'desktop_app.py',
    '--name=BordroMotoru',
    '--onedir',         # Klasör modu (en güvenli, en az AV uyarısı)
    '--windowed',       # Konsol penceresi açılmaz
    '--clean',
    # Veri dosyalarını ekle: Kaynak;Hedef
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--add-data=data;data',
    '--add-data=core;core',
    # İkon (Otomatik oluşturulan .ico dosyası)
    '--icon=static/img/app.ico', 
])

print("\n✅ Derleme tamamlandı!")
print("📂 Uygulamanız şurada hazır: dist/BordroMotoru/BordroMotoru.exe")
print("⚠️ Dağıtım için 'dist/BordroMotoru' klasörünün tamamını ZIP yapıp paylaşın.")
