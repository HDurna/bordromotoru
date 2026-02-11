# 🧠 Brainstorm: Bordro Parametrelerinin Otomatik Güncellenmesi & Masaüstü Uygulaması

### Bağlam
Türkiye'de bordro hesaplaması için gereken parametreler (asgari ücret, gelir vergisi dilimleri, SGK tavanı, damga vergisi oranı) yılda en az 1 kez, bazen yıl ortasında da değişir. Şu anda bu parametreler `params_2026.json` dosyasında elle tutulmaktadır. Amaç: bu parametreleri güncel tutma sürecini otomize etmek ve uygulamayı masaüstünde bağımsız çalıştırmak.

---

### Option A: Web Scraping ile Otomatik Parametre Çekme 🕷️
Resmi kaynakları (gib.gov.tr, sgk.gov.tr, Resmi Gazete) veya güvenilir muhasebe sitelerini (muhasebetr.com vb.) periyodik olarak kazıyarak parametreleri otomatik çekmek.

✅ **Artıları:**
- Tam otomasyon (İnsan müdahalesi gerekmez)
- Yılbaşı ve ara zam dönemlerinde anında güncelleme
- Çoklu kaynak doğrulaması mümkün (2+ kaynaktan çapraz kontrol)

❌ **Eksileri:**
- Kaynak sitelerdeki HTML yapısı her zaman değişebilir (kırılgan)
- Resmi kurumlarda API yok (SGK/GİB doğrudan veri API'si sunmuyor)
- Yasal belirsizlik (bazı siteler scraping'e izin vermeyebilir)
- Yanlış veri çekme riski (hatalı parse sonucu bordro hatalı hesaplanır)

📊 **Efor:** Yüksek (sürekli bakım gerektirir)

---

### Option B: Yarı-Otomatik Güncelleme (Önerilen) ✏️
Kullanıcıya, uygulama içinden parametreleri kolayca güncelleyebileceği bir "Parametre Yönetimi" ekranı sunmak. Ek olarak, bilinen güvenilir kaynaklardan (örn. muhasebetr.com) "kontrol et" butonu ile mevcut parametreleri karşılaştırma yapabilecek bir mekanizma kurmak.

✅ **Artıları:**
- Güvenilir: Son onay daima kullanıcıda
- Bakım yükü düşük (scraper kırılma riski yok)
- Kullanıcı istediği parametre setini elle girebilir (özel senaryolar)
- "Kontrol Et" butonu ile olası güncellemeleri öneri olarak gösterebilir
- Hata riski minimum (insan doğrulaması var)

❌ **Eksileri:**
- Tamamen "hands-free" değil
- Yılda 1-2 kez kullanıcının müdahale etmesi gerekir

📊 **Efor:** Düşük-Orta

---

### Option C: Uzak Sunucu + Push Güncelleme ☁️
Bir sunucuda (VPS / Firebase / Supabase) merkezi parametre deposu tutmak. Yönetici yılbaşında parametreleri sunucuya yükler; masaüstü uygulamalar başlangıçta veya periyodik olarak bu sunucudan güncel parametreleri çeker.

✅ **Artıları:**
- Tüm kullanıcılar aynı anda güncellenir
- Merkezi yönetim (1 kez güncelle, herkes görsün)
- İleride SaaS modeline dönüştürülebilir

❌ **Eksileri:**
- Sunucu maliyeti ve bakımı gerekir
- İnternet bağımlılığı (Çevrimdışı çalışamaz — fallback gerekir)
- MVP fazında overkill

📊 **Efor:** Orta-Yüksek

---

## 💡 Önerim

**Option B (Yarı-Otomatik Güncelleme)** — MVP için en mantıklısı budur.

**Neden?**
1. Bordro parametreleri yılda sadece 1-2 kez değişir; tam otomasyon overkill.
2. Resmi bir API yoktur; scraping kırılgan ve risklidir.
3. Kullanıcının kontrolünde olması, bordro gibi hassas bir alanda güven verir.
4. İleride Option C'ye (sunucu tabanlı) geçiş kolayca yapılabilir (params.json formatı aynı kalır).

**Uygulama Planı:**
- Masaüstü uygulamada "Ayarlar / Parametreler" sekmesi ekle.
- JSON dosyasını okuyup düzenlenebilir form olarak göster.
- "Kaydet" ile JSON dosyasını güncelle.
- İlerleyen versiyonlarda: "Güncellemeleri Kontrol Et" butonu (web'den karşılaştırma).

---

## Parametrelerin Bağımlılık Haritası

| Parametre | Kaynağı | Değişim Sıklığı | Bağımlılıklar |
|---|---|---|---|
| Asgari Ücret (Brüt) | Asgari Ücret Tespit Komisyonu / Resmi Gazete | Yılda 1 (bazen 2) | SGK Tavanı, GV İstisnası, DV İstisnası |
| SGK Tavanı | Asgari Ücret x 7.5 (otomatik hesaplanabilir) | Asgari ücretle birlikte | PEK hesabı |
| Gelir Vergisi Dilimleri | GİB / Maliye Bakanlığı (yeniden değerleme oranına göre) | Yılda 1 | Kümülatif vergi hesabı |
| Damga Vergisi Oranı | GİB | Nadiren değişir (son yıllarda sabit) | DV hesabı |
| SGK İşçi Oranları | SGK | Çok nadiren değişir (%14, %1 uzun süredir aynı) | SGK kesintisi |
| SGDP Oranı | SGK | Çok nadiren değişir | Emekli çalışan kesintisi |

**Kritik İlişki:** Asgari ücret değişince → SGK tavanı, GV istisnası ve DV istisnası otomatik etkilenir. Bu nedenle kodda `min_wage_gross` tek kaynak olarak kullanılmalı; diğerleri bundan türetilmelidir.

Hangi yöne gitmek istersiniz?
