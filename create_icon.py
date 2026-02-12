from PIL import Image
import os

def create_ico():
    img_path = r"templates/dis-logo.png"
    ico_path = r"static/img/app.ico"
    
    if not os.path.exists(img_path):
        print(f"HATA: {img_path} bulunamadı!")
        return

    img = Image.open(img_path)
    # Icon boyutları: 256, 128, 64, 48, 32, 16
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"✅ Başarılı: {ico_path} oluşturuldu.")

if __name__ == "__main__":
    create_ico()
