"""
Bordro Analiz Modülü
PDF bordro dosyasını okur, alanları parse eder,
hesaplama motoruyla karşılaştırır ve sade Türkçe yorumlar üretir.

Karakter kodlama sorunu: Bazı PDF'lerde Türkçe harfler bozuk gelir.
Ý→İ/I, Þ→Ş, Ð→Ğ, ý→ı  — Normalize fonksiyonu bunu düzeltir.
"""
import re
import pdfplumber
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, List, Tuple


# ===== KARAKTERLERİ NORMALİZE ET =====
def normalize_turkish(text: str) -> str:
    """PDF'den gelen bozuk Türkçe karakterleri düzeltir."""
    replacements = {
        'Ý': 'İ', 'ý': 'ı', 'Þ': 'Ş', 'þ': 'ş',
        'Ð': 'Ğ', 'ð': 'ğ', 'Ö': 'Ö', 'ö': 'ö',
        'Ü': 'Ü', 'ü': 'ü', 'Ç': 'Ç', 'ç': 'ç',
        '\xad': '-',  # soft hyphen
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


# ===== PARA PARSE =====
def parse_money_turkish(text: str) -> Optional[Decimal]:
    """Türk bordro formatındaki sayıları parse eder.
    Desteklenen formatlar:
      - 62 339.83  (boşluklu binlik, noktalı ondalık)
      - 1.234,56   (noktalı binlik, virgüllü ondalık)
      - 1234.56    (standart)
      - 4 725.14   (boşluklu binlik)
    """
    if not text:
        return None
    
    cleaned = text.strip().replace('₺', '').replace('TL', '').strip()
    if not cleaned:
        return None
    
    negative = False
    if cleaned.startswith('-') or cleaned.startswith('('):
        negative = True
        cleaned = cleaned.replace('-', '').replace('(', '').replace(')', '').strip()
    
    try:
        # Format 1: Boşluklu binlik (62 339.83)
        if ' ' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace(' ', '')
            result = Decimal(cleaned)
        # Format 2: Türkçe (1.234,56)
        elif ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
            result = Decimal(cleaned)
        # Format 3: Sadece virgül (1234,56)
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
            result = Decimal(cleaned)
        # Format 4: Boşluklu binlik ondalıksız (4 725)
        elif ' ' in cleaned:
            cleaned = cleaned.replace(' ', '')
            result = Decimal(cleaned)
        else:
            result = Decimal(cleaned)
        
        return -result if negative else result
    except (InvalidOperation, ValueError):
        return None


# ===== ANAHTAR KELİME HARİTASI =====
# Her alan için olası etiketler (normalize edilmiş metin üzerinde çalışır)
FIELD_PATTERNS = {
    "gross": [
        r"TOPLAM\s*BR[ÜU]T\s*GEL[İI]R\s*:\s*([\d\s]+\.?\d*)",
        r"BR[ÜU]T\s*[ÜU]CRET\s*:\s*([\d\s]+\.?\d*)",
        r"BRÜT\s*MAAŞ\s*:\s*([\d\s]+\.?\d*)",
    ],
    "net": [
        r"NET\s*KAZAN[ÇC]\s*:\s*([\d\s]+\.?\d*)",
        r"NET\s*[ÖO]DENEN\s*:\s*([\d\s]+\.?\d*)",
        r"NET\s*[ÜU]CRET\s*:\s*([\d\s]+\.?\d*)",
        r"ELE\s*GE[ÇC]EN\s*:\s*([\d\s]+\.?\d*)",
    ],
    "sgk_employee": [
        r"SGK\s*PR[İI]M[İI]\s*:\s*([\d\s]+\.?\d*)",
        r"SGK\s*[İI][ŞS][ÇC][İI]\s*:\s*([\d\s]+\.?\d*)",
        r"SİGORTA\s*PRİMİ\s*:\s*([\d\s]+\.?\d*)",
    ],
    "unemployment_employee": [
        r"[İI][ŞS]S[İI]Z[\.\s]*S[İI]G[\.\s]*[İI][ŞS][ÇC][İI]\s*PR[İI]M\s*:\s*([\d\s]+\.?\d*)",
        r"İŞSİZLİK\s*SİG\s*:\s*([\d\s]+\.?\d*)",
        r"İŞSİZLİK\s*PRİMİ\s*:\s*([\d\s]+\.?\d*)",
    ],
    "income_tax": [
        r"GEL[İI]R\s*VERG[İI]S[İI]\s*:\s*([\d\s]+\.?\d*)",
        r"G\.V\.\s*:\s*([\d\s]+\.?\d*)",
    ],
    "stamp_tax": [
        r"DAMGA\s*VERG[İI]S[İI]\s*:\s*([\d\s]+\.?\d*)",
        r"D\.V\.\s*:\s*([\d\s]+\.?\d*)",
    ],
    "sgk_base": [
        r"SGK\s*MATRAH[İI]\s*:\s*([\d\s]+\.?\d*)",
    ],
    "income_tax_base": [
        r"GEL[İI]R\s*VERG[İI]S[İI]\s*MAT[\.\s]*:\s*([\d\s]+\.?\d*)",
        r"G\.V\.\s*MAT\s*:\s*([\d\s]+\.?\d*)",
    ],
    "cum_tax_base": [
        r"K[ÜU]M[\.\s]*GEL[İI]R\s*VER[\.\s]*MAT[\.\s]*:\s*([\d\s]+\.?\d*)",
        r"KÜMÜLATİF\s*MATRAH\s*:\s*([\d\s]+\.?\d*)",
    ],
    "income_tax_exemption": [
        r"G\.V\.\s*[İI]ST[İI]SNA\s*TUTARI\s*:\s*([\d\s]+\.?\d*)",
        r"GEL[İI]R\s*VERG[İI]S[İI]\s*[İI]ST[İI]SNA\s*:\s*([\d\s]+\.?\d*)",
    ],
    "stamp_tax_exemption": [
        r"D\.V\.\s*[İI]ST[İI]SNA\s*TUTARI\s*:\s*([\d\s]+\.?\d*)",
        r"DAMGA\s*VERG[İI]S[İI]\s*[İI]ST[İI]SNA\s*:\s*([\d\s]+\.?\d*)",
    ],
    "net_paid": [
        r"NET\s*[ÖO]DENEN\s*:\s*([\d\s]+\.?\d*)",
    ],
    "bes_amount": [
        r"BES\s*TUTARI\s*:\s*([\d\s]+\.?\d*)",
    ],
    "sgk_days": [
        r"SGK\s*G[ÜU]N\s*:\s*(\d+)",
    ],
    "deductions_misc": [
        r"MUHTEL[İI]F\s*KES[İI]NT[İI]LER\s*:\s*([\d\s]+\.?\d*)",
    ],
    "child_benefit": [
        r"[ÇC]OCUK\s*PARASI\s*:\s*([\d\s]+\.?\d*)",
    ],
    "fuel_allowance": [
        r"YAKACAK\s*([\d\s]+\.?\d*)",
    ],
    "unit_wage": [
        r"BR[İI]M\s*[ÜU]CRET\s*:\s*([\d\s]+\.?\d*)",
    ],
}

# Türkçe ay isimleri
MONTH_NAMES_MAP = {
    "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "haziran": 6, "temmuz": 7, "ağustos": 8, "eylül": 9,
    "ekim": 10, "kasım": 11, "aralık": 12,
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF'den metin çıkarır ve Türkçe karakterleri normalize eder."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            
            # Tabloları da çıkar
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        cells = [str(c).strip() if c else "" for c in row]
                        full_text += " | ".join(cells) + "\n"
    
    # Türkçe karakter düzeltmesi
    full_text = normalize_turkish(full_text)
    return full_text


def detect_period(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Metinden bordro dönemini (ay/yıl) tespit eder."""
    # Format: 12/2025, 01/2026 vb.
    match = re.search(r"(\d{1,2})\s*/\s*(20\d{2})\s*AYI", text, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Format: OCAK 2026
    for name, num in MONTH_NAMES_MAP.items():
        if name.upper() in text.upper():
            year_match = re.search(r"20(2[4-9]|3[0-9])", text)
            if year_match:
                return num, int(year_match.group(0))
    
    # Sadece yıl
    year_match = re.search(r"20(2[4-9]|3[0-9])", text)
    year = int(year_match.group(0)) if year_match else None
    return None, year


def parse_payslip(text: str) -> Dict:
    """Bordro metnini parse ederek alanları çıkarır."""
    result = {}
    
    for field_name, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_value = match.group(1).strip()
                val = parse_money_turkish(raw_value)
                if val is not None and val >= 0:
                    result[field_name] = val
                    break
    
    # Dönem tespiti
    month, year = detect_period(text)
    result["detected_month"] = month
    result["detected_year"] = year
    
    # NET ÜCRET 0.00 geldiğinde, NET KAZANÇ veya NET ÖDENEN kullanılmalı
    if result.get("net", Decimal("0")) == Decimal("0"):
        for alt_key in ["net_paid"]:
            if alt_key in result and result[alt_key] > 0:
                result["net"] = result[alt_key]
                break
    
    # Jenerik etiket:değer çıkarma (tanınmayan formatlar için fallback)
    result["_generic_pairs"] = extract_generic_pairs(text)
    
    # Kritik alanların bulunma durumu
    critical_fields = ["gross", "net", "sgk_employee", "income_tax"]
    found_critical = sum(1 for f in critical_fields if f in result)
    result["_parse_confidence"] = found_critical / len(critical_fields)
    result["_found_fields"] = [k for k in result if not k.startswith("_") and k not in ("detected_month", "detected_year") and isinstance(result[k], Decimal)]
    result["_missing_critical"] = [f for f in critical_fields if f not in result]
    
    return result


def extract_generic_pairs(text: str) -> List[Dict]:
    """Metindeki tüm etiket:sayı çiftlerini jenerik olarak çıkarır.
    Tanınmayan bordro formatları için fallback olarak kullanılır."""
    pairs = []
    # Pattern: ETIKET: 1 234.56 veya ETİKET: 1.234,56
    pattern = r'([A-ZÇĞİÖŞÜa-zçğıöşü\.\s]{3,40})\s*:\s*([\d][\d\s\.\,]+\d)'
    
    for match in re.finditer(pattern, text):
        label = match.group(1).strip()
        raw_val = match.group(2).strip()
        val = parse_money_turkish(raw_val)
        
        # Geçerli sayıları filtrele (çok büyük veya çok küçük olmayanlar)
        if val is not None and val > Decimal("0") and val < Decimal("99999999"):
            # Sicil no, TC no gibi sayıları atla
            if val > Decimal("9999999999"):  # 10+ haneli → muhtemelen sicil no
                continue
            # Zaten bilinen alanlarla eşleşmiyorsa ekle
            pairs.append({
                "label": label,
                "value": str(val),
                "raw": raw_val
            })
    
    # En fazla 20 çift döndür
    return pairs[:20]


def analyze_payslip(parsed: Dict, year_params: Dict) -> Dict:
    """Parse edilmiş bordroyu analiz eder ve yorumlar üretir."""
    from core import payroll
    
    findings = []
    warnings = []
    explanations = []
    
    gross = parsed.get("gross")
    net = parsed.get("net")
    sgk = parsed.get("sgk_employee")
    unemp = parsed.get("unemployment_employee")
    income_tax = parsed.get("income_tax")
    stamp_tax = parsed.get("stamp_tax")
    cum_base = parsed.get("cum_tax_base")
    sgk_base = parsed.get("sgk_base")
    gv_base = parsed.get("income_tax_base")
    gv_exemption = parsed.get("income_tax_exemption")
    dv_exemption = parsed.get("stamp_tax_exemption")
    bes = parsed.get("bes_amount")
    sgk_days = parsed.get("sgk_days")
    child = parsed.get("child_benefit")
    fuel = parsed.get("fuel_allowance")
    misc_deductions = parsed.get("deductions_misc")
    unit_wage = parsed.get("unit_wage")
    net_paid = parsed.get("net_paid")
    
    min_wage = Decimal(str(year_params.get("min_wage_gross", 0)))
    month = parsed.get("detected_month")
    year = parsed.get("detected_year")
    
    MONTH_TR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    
    period_str = ""
    if month and year:
        period_str = f"{MONTH_TR[month-1]} {year}"
    
    # ===== GENEL BİLGİ =====
    if gross:
        explanations.append(f"💰 {period_str} dönemi toplam brüt geliriniz **{gross:,.2f} TL** olarak görünüyor.")
    
    if unit_wage:
        explanations.append(f"📋 Birim ücretiniz (aylık baz maaş): **{unit_wage:,.2f} TL**")
        if fuel and fuel > 0:
            explanations.append(f"🔥 Yakacak yardımı: **{fuel:,.2f} TL** — Bu tutar brüt gelire dahil edilmiştir.")
    
    if net:
        explanations.append(f"🏦 Net kazancınız (BES kesintisi öncesi): **{net:,.2f} TL**")
    
    if net_paid and net_paid != net:
        explanations.append(f"💳 Net ödenen (BES sonrası elinize geçen): **{net_paid:,.2f} TL**")
    
    if bes and bes > 0:
        explanations.append(f"🏛️ BES (Bireysel Emeklilik) kesintisi: **{bes:,.2f} TL** — Bu tutar net kazançtan düşülerek net ödenen bulunur.")
    
    if gross and net:
        deduction_total = gross - net
        rate = (deduction_total / gross * 100).quantize(Decimal("0.1"))
        explanations.append(f"📊 Toplam kesinti (vergi+sigorta): **{deduction_total:,.2f} TL** (brüt gelirinizin **%{rate}**'si)")
    
    if sgk_days:
        explanations.append(f"📅 SGK gün sayısı: **{sgk_days}** gün")
    
    # ===== SGK ANALİZİ =====
    if sgk:
        explanations.append(f"🏥 SGK primi (işçi payı): **{sgk:,.2f} TL**")
        
        if sgk_base:
            sgk_rate_actual = (sgk / sgk_base * 100).quantize(Decimal("0.1"))
            explanations.append(f"   → SGK matrahı: {sgk_base:,.2f} TL × %{sgk_rate_actual} = {sgk:,.2f} TL")
            
            expected_sgk_rate = Decimal(str(year_params.get("rates", {}).get("normal_4a", {}).get("sgk_employee", "0.14")))
            expected_sgk = (sgk_base * expected_sgk_rate).quantize(Decimal("0.01"))
            diff = abs(sgk - expected_sgk)
            
            sgk_ceiling = Decimal(str(year_params.get("sgk_ceiling_monthly", 0)))
            if sgk_base < gross and sgk_ceiling > 0:
                if abs(sgk_base - sgk_ceiling) < Decimal("100"):
                    explanations.append(f"📌 Brüt geliriniz SGK tavanını aşıyor. SGK matrahı tavandan ({sgk_ceiling:,.2f} TL) hesaplanmış.")
            
            if diff <= Decimal("5"):
                findings.append(f"✅ SGK primi doğru (%{(expected_sgk_rate*100).quantize(Decimal('0.1'))} × {sgk_base:,.2f} = {expected_sgk:,.2f} TL)")
            else:
                warnings.append(f"⚠️ SGK primi beklentimizle uyuşmuyor. Bordroda: {sgk:,.2f}, Beklenen: {expected_sgk:,.2f} (Fark: {diff:,.2f} TL)")
    
    # ===== İŞSİZLİK =====
    if unemp:
        explanations.append(f"📋 İşsizlik sigortası (işçi payı): **{unemp:,.2f} TL**")
        
        if sgk_base:
            expected_unemp_rate = Decimal(str(year_params.get("rates", {}).get("normal_4a", {}).get("unemployment_employee", "0.01")))
            expected_unemp = (sgk_base * expected_unemp_rate).quantize(Decimal("0.01"))
            diff = abs(unemp - expected_unemp)
            if diff <= Decimal("5"):
                findings.append(f"✅ İşsizlik sigortası doğru (%{(expected_unemp_rate*100).quantize(Decimal('0.1'))} × {sgk_base:,.2f} = {expected_unemp:,.2f} TL)")
            else:
                warnings.append(f"⚠️ İşsizlik sigortası farkı: Bordroda {unemp:,.2f}, Beklenen {expected_unemp:,.2f} (Fark: {diff:,.2f} TL)")
    
    # ===== GELİR VERGİSİ =====
    if income_tax:
        explanations.append(f"💸 Gelir vergisi: **{income_tax:,.2f} TL**")
        
        if gv_exemption:
            explanations.append(f"🛡️ GV istisnası (asgari ücret): **{gv_exemption:,.2f} TL** — Bu tutar verginizden düşülmüştür.")
        
        if gv_base:
            explanations.append(f"   → GV matrahı (aylık): {gv_base:,.2f} TL")
    
    # ===== KÜMÜLATİF VERGİ DİLİMİ =====
    if cum_base:
        tariff = year_params.get("income_tax_tariff", [])
        current_bracket = None
        for i, bracket in enumerate(tariff):
            limit = bracket.get("up_to")
            rate = Decimal(str(bracket.get("rate", 0)))
            if limit is None or cum_base <= Decimal(str(limit)):
                current_bracket = (i + 1, rate)
                break
        
        if current_bracket:
            bracket_num, bracket_rate = current_bracket
            pct = (bracket_rate * 100).quantize(Decimal("0.1"))
            explanations.append(f"📈 Kümülatif GV matrahı: **{cum_base:,.2f} TL** → Şu an **{bracket_num}. dilimdesiniz (%{pct})**")
            
            # Sonraki dilime ne kadar kaldığını hesapla
            for bracket in tariff:
                limit = bracket.get("up_to")
                if limit and cum_base < Decimal(str(limit)):
                    remaining = Decimal(str(limit)) - cum_base
                    next_rate = Decimal(str(bracket.get("rate", 0))) * 100
                    explanations.append(f"   → Bir sonraki dilime (%{next_rate.quantize(Decimal('0.1'))}) **{remaining:,.2f} TL** kaldı.")
                    break
            
            if bracket_num >= 2:
                explanations.append("💡 Yılın başında %15 ile başlayan verginiz, kümülatif matrahınız arttıkça üst dilimlere geçer. Yıl sonuna doğru daha fazla vergi kesilmesi normaldir.")
    
    # ===== DAMGA VERGİSİ =====
    if stamp_tax:
        explanations.append(f"📝 Damga vergisi: **{stamp_tax:,.2f} TL**")
        if dv_exemption:
            explanations.append(f"🛡️ DV istisnası (asgari ücret): **{dv_exemption:,.2f} TL**")
        
        if gross:
            stamp_rate = Decimal(str(year_params.get("stamp_rate", "0.00759")))
            expected_dv_gross = (gross * stamp_rate).quantize(Decimal("0.01"))
            
            if dv_exemption:
                expected_dv_net = max(expected_dv_gross - dv_exemption, Decimal("0"))
            else:
                min_wage_dv = (min_wage * stamp_rate).quantize(Decimal("0.01"))
                expected_dv_net = max(expected_dv_gross - min_wage_dv, Decimal("0"))
            
            diff = abs(stamp_tax - expected_dv_net)
            if diff <= Decimal("5"):
                findings.append(f"✅ Damga vergisi doğru görünüyor ({stamp_tax:,.2f} TL)")
            else:
                warnings.append(f"⚠️ Damga vergisi farkı: Bordroda {stamp_tax:,.2f}, Beklenen ~{expected_dv_net:,.2f} (Fark: {diff:,.2f} TL)")
    
    # ===== MUHTELİF KESİNTİLER =====
    if misc_deductions and misc_deductions > 0:
        explanations.append(f"🔧 Muhtelif kesintiler (icra, nafaka, avans vb.): **{misc_deductions:,.2f} TL** — Bu yasal kesintilerdir ve brütten düşülür.")
    
    if child and child > 0:
        explanations.append(f"👶 Çocuk parası: **{child:,.2f} TL** — Bu tutar vergiden muaftır.")
    
    # ===== DOĞRULAMA =====
    if gross and sgk and income_tax:
        try:
            # Motor ile hesapla
            calc_result = payroll.calculate_pay_slip(
                gross=gross,
                cum_tax_base_prev=(cum_base - gv_base) if cum_base and gv_base else Decimal("0"),
                employee_type="normal_4a",
                year_params=year_params,
                month=month or 1
            )
            calc_net = calc_result.get("net", Decimal("0"))
            
            if net:
                diff = abs(net - calc_net)
                if diff <= Decimal("100"):
                    findings.append(f"✅ Net kazanç hesaplamamızla büyük ölçüde uyuşuyor (Motor: {calc_net:,.2f} TL, Bordro: {net:,.2f} TL)")
                else:
                    explanation = "Fark, ek ödemeler (yakacak, ikramiye), fazla mesai, özel indirimler veya farklı SGK matrahı kaynaklı olabilir."
                    warnings.append(
                        f"⚠️ Net kazançta fark var. Bordro: {net:,.2f} TL, Motor: {calc_net:,.2f} TL "
                        f"(Fark: {diff:,.2f} TL). {explanation}"
                    )
        except Exception as e:
            warnings.append(f"⚠️ Doğrulama hesaplaması yapılamadı: {str(e)}")
    
    # ===== PARSE DURUMU DEĞERLENDİRMESİ =====
    confidence = parsed.get("_parse_confidence", 0)
    found_fields = parsed.get("_found_fields", [])
    missing_critical = parsed.get("_missing_critical", [])
    generic_pairs = parsed.get("_generic_pairs", [])
    
    CRITICAL_LABELS = {
        "gross": "Brüt Ücret", "net": "Net Ücret",
        "sgk_employee": "SGK Primi", "income_tax": "Gelir Vergisi"
    }
    
    if confidence < 0.5:
        # Yarıdan azı bulundu — uyarı göster
        missing_names = [CRITICAL_LABELS.get(f, f) for f in missing_critical]
        if missing_names:
            warnings.append(
                f"⚠️ Bordro formatı tam tanınamadı. Şu kritik alanlar bulunamadı: "
                f"**{', '.join(missing_names)}**. Bordronuzun formatı farklı olabilir."
            )
        
        if generic_pairs:
            explanations.append(
                "🔎 Bordro formatı standart kalıplarımızla tam eşleşmedi, "
                "ancak aşağıda metinden çıkarılabilen etiket-değer çiftleri listelenmektedir. "
                "Bu değerlerden bordronuzu yorumlayabilirsiniz."
            )
    elif confidence < 1.0:
        missing_names = [CRITICAL_LABELS.get(f, f) for f in missing_critical]
        if missing_names:
            explanations.append(
                f"ℹ️ Bordronuzun çoğu alanı başarıyla okundu. Bulunamayan: **{', '.join(missing_names)}**"
            )
    else:
        findings.append("✅ Bordronun tüm kritik alanları başarıyla okundu.")
    
    # ===== SONUÇ =====
    return {
        "parsed_fields": {k: str(v) for k, v in parsed.items() if isinstance(v, Decimal)},
        "detected_month": parsed.get("detected_month"),
        "detected_year": parsed.get("detected_year"),
        "explanations": explanations,
        "findings": findings,
        "warnings": warnings,
        "verification": None,
        "generic_pairs": generic_pairs if confidence < 0.75 else [],
        "parse_confidence": confidence,
    }
