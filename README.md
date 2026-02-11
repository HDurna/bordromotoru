# 🧮 Bordro Motoru

Türk iş hukuku ve SGK mevzuatına uygun bordro hesaplama ve analiz masaüstü uygulaması.

## ✨ Özellikler

- **Brüt → Net / Net → Brüt** hesaplama
- **12 Aylık Projeksiyon** — vergi dilimi geçişleri ile aylık detay
- **Bordro PDF Analizi** — PDF'den otomatik okuma, doğrulama ve sade Türkçe yorumlar
- **Manuel Giriş** — PDF okunamazsa kullanıcı kendi değerlerini girerek yorum alabilir
- **Tamamen Yerel** — hiçbir veri dışarı gönderilmez

## 🛠️ Teknolojiler

| Teknoloji | Kullanım |
|---|---|
| Python | Backend hesaplama motoru |
| PyWebView | Masaüstü pencere (native) |
| HTML/Tailwind CSS | Arayüz tasarımı |
| Chart.js | Grafikler |
| pdfplumber | PDF metin çıkarma |

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+

### Adımlar
```bash
git clone https://github.com/HDurna/bordromotoru.git
cd bordromotoru
pip install -r requirements.txt
python desktop_app.py
```

## 📁 Proje Yapısı

```
├── core/               # Hesaplama motoru
│   ├── payroll.py      # Brüt-net hesaplama
│   ├── params.py       # Yıl parametreleri
│   ├── tax.py          # Vergi hesaplama
│   └── analyzer.py     # Bordro PDF analizi
├── data/               # Parametre dosyaları
│   └── params_2026.json
├── templates/
│   └── desktop.html    # Ana UI
├── desktop_app.py      # PyWebView masaüstü uygulaması
├── app.py              # Flask web sunucu (alternatif)
└── cli.py              # Komut satırı arayüzü
```

## 👨‍💻 Geliştirici

**Hikmet Durna**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/hikmetdurna/)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/hikmetdurna/)

## ⚖️ Sorumluluk Reddi

Bu uygulama yalnızca bilgilendirme amaçlıdır. Hukuki veya mali danışmanlık niteliği taşımaz.
Bordronuzla ilgili kesin bilgi için şirketinizin İnsan Kaynakları / Muhasebe birimine danışınız.

## 📄 Lisans

Kişisel Kullanım — Tüm hakları saklıdır © 2026 Hikmet Durna
