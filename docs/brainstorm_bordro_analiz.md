# 🧠 Brainstorm: Bordro Analiz & Yorumlama Sistemi

### Bağlam
Türkiye'de çalışanların büyük çoğunluğu bordrosunu okuyamaz. "Neden bu kadar kesildi?", "Vergi dilimi nedir?", "Geçen aydan neden farklı?" gibi soruları yanıtlayamaz. Amaç: Kullanıcının bordrosunu yüklemesi, sistemin otomatik okuması, doğrulaması ve **sade Türkçe** ile yorumlaması.

---

### Option A: PDF Metin Çıkarma (pdfplumber) 📄
PDF tabanlı bordro dosyalarından metin çıkarıp, regex ile alanları parse etmek.

✅ **Artıları:**
- Çoğu bordro dijital PDF olarak verilir (metin katmanı var)
- pdfplumber tablo yapısını bile algılar
- Hızlı, hafif, ek servis gerektirmez
- Offline çalışır (internet bağımlılığı yok)

❌ **Eksileri:**
- Taranmış/fotoğraf PDF'ler okunamaz
- Her işverenin bordro formatı farklı (parser esnekliği gerekir)
- Karmaşık tablolarda hatalı parse riski

📊 **Efor:** Orta

---

### Option B: OCR (Tesseract) + Görüntü İşleme 🔍
Hem PDF hem görüntü (JPG/PNG) dosyalarını OCR ile okuyup parse etmek.

✅ **Artıları:**
- Taranmış/fotoğraf bordroları da okunur
- Daha geniş dosya formatı desteği

❌ **Eksileri:**
- Tesseract kurulumu gerekir (EXE dağıtımında sorunlu)
- Türkçe karakter hataları (özellikle ₺, İ, Ş, Ğ)
- Yavaş (özellikle düşük kaliteli görüntülerde)
- Doğruluk düşük olabilir

📊 **Efor:** Yüksek

---

### Option C: Hibrit (PDF-first + OCR Fallback) 🔄
Önce metin çıkar; metin bulunamazsa OCR'a düş (ileride eklenebilir).

✅ **Artıları:**
- En iyi kullanıcı deneyimi
- MVP'de sadece PDF metin, ileride OCR eklenebilir

❌ **Eksileri:**
- İki farklı pipeline bakımı

📊 **Efor:** Orta (MVP'de sadece metin, OCR Phase 2)

---

## 💡 Önerim: Option A (PDF Metin) + Akıllı Yorumlama

**MVP Kapsamı:**
1. PDF yükleme arayüzü (drag & drop)
2. pdfplumber ile metin çıkarma
3. Regex + anahtar kelime ile alan tespiti (Brüt, Net, SGK, GV, DV vb.)
4. Motorumuzla karşılaştırma → Tutarsızlıkları tespit
5. Sade Türkçe açıklamalar:
   - "Bu ay brüt maaşınız X TL, elinize Y TL geçmiş."
   - "SGK kesintiniz Z TL — bu, brüt maaşınızın %14'ü."
   - "Gelir verginiz artmış çünkü kümülatif matrahınız 2. dilime geçmiş."
   - "⚠️ Damga vergisi hesaplamamızla tutarsız — 5,20 TL fark var."

---

## Bordro Anahtar Alanları (Parse Hedefleri)

| Alan | Olası Etiketler |
|---|---|
| Brüt Ücret | BRÜT ÜCRET, BRÜT MAAŞ, GROSS, Brüt Tutar |
| SGK İşçi | SGK PRIM, SGK İŞÇİ, WORKER SSI, Sigorta Primi |
| İşsizlik | İŞSİZLİK, UNEMPLOYMENT, İşsizlik Sigortası |
| Gelir Vergisi | GELİR VERGİSİ, G.V., INCOME TAX, GV Kesintisi |
| Damga Vergisi | DAMGA VERGİSİ, D.V., STAMP TAX |
| Net Ücret | NET ÜCRET, NET MAAŞ, NET, Ele Geçen |
| GV Matrahı | GV MATRAHI, VERGİ MATRAHI |
| Kümülatif Matrah | KÜMÜLATİF, TOPLAM MATRAH |
