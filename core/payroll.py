from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from core import params, tax

def round_decimal(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_pay_slip(
    gross: Decimal,
    cum_tax_base_prev: Decimal,
    employee_type: str,
    year_params: Dict[str, Any],
    month: int = 1
) -> Dict[str, Any]:
    """
    Belirli bir brüt maaş ve kümülatif matrah için aylık bordro hesaplar.
    """
    # 1. Sabitler ve Oranlar
    constants = year_params
    rates = params.get_rate
    
    sgk_ceiling = Decimal(str(constants["sgk_ceiling_monthly"]))
    min_wage_gross = Decimal(str(constants["min_wage_gross"]))
    stamp_rate = Decimal(str(constants["stamp_rate"]))
    tariff = params.get_tariff(constants)
    
    # 2. PEK (Prime Esas Kazanç)
    pek = min(gross, sgk_ceiling)
    
    # 3. SGK ve İşsizlik Kesintileri
    rate_unemp = rates(constants, employee_type, "unemployment_employee")
    
    if employee_type == "normal_4a":
        rate_sgk = rates(constants, employee_type, "sgk_employee")
    elif employee_type == "emekli_sgdp":
        rate_sgk = rates(constants, employee_type, "sgdp_employee")
    else:
        # Varsayılan veya hata
        raise ValueError(f"Geçersiz çalışan tipi: {employee_type}")
    
    sgk_amount = pek * rate_sgk
    unemployment_amount = pek * rate_unemp
    
    # 4. Gelir Vergisi Matrahı (Aylık)
    # Damga vergisi matrahtan düşülmez.
    income_tax_base_month = gross - sgk_amount - unemployment_amount
    
    # 5. Kümülatif Matrah Takibi
    cum_tax_base_new = cum_tax_base_prev + income_tax_base_month
    
    # 6. Gelir Vergisi (İstisna Öncesi Brüt)
    # Kümülatif vergi hesabı: tax(yeni_kumulatif) - tax(eski_kumulatif)
    income_tax_gross = tax.calculate_income_tax_cumulative(
        cum_tax_base_prev, 
        income_tax_base_month, 
        tariff
    )
    
    # 7. Asgari Ücret Vergi İstisnası (Kümülatif Mantıkla)
    # 2026 Varsayımı: Standart çalışan oranlarıyla (14% + 1%) asgari ücretin matrahı bulunur.
    min_wage_tax_base = min_wage_gross * (1 - Decimal("0.14") - Decimal("0.01"))
    
    # İstisna tutarı = Asgari ücretlinin (o kümülatif noktada) ödeyeceği vergi
    income_tax_exemption = tax.calculate_income_tax_cumulative(
        cum_tax_base_prev,
        min_wage_tax_base,
        tariff
    )
    
    # Ödenecek Gelir Vergisi (Eksiye düşemez)
    income_tax_net = max(Decimal("0"), income_tax_gross - income_tax_exemption)
    
    # 8. Damga Vergisi & İstisnası
    # İstisna: Asgari ücrete isabet eden damga vergisi
    # Damga vergisi genelde brüt üstünden: gross * rate
    stamp_tax_calc = tax.calculate_stamp_tax(
        gross, 
        stamp_rate, 
        exemption_amount=(min_wage_gross * stamp_rate)
    )
    
    # 9. Net Maaş
    net_salary = gross - sgk_amount - unemployment_amount - income_tax_net - stamp_tax_calc["net"]
    
    return {
        "gross": round_decimal(gross),
        "pek": round_decimal(pek),
        "sgk_employee": round_decimal(sgk_amount),
        "unemployment_employee": round_decimal(unemployment_amount),
        "income_tax_base_month": round_decimal(income_tax_base_month),
        "cum_tax_base_prev": round_decimal(cum_tax_base_prev),
        "cum_tax_base_new": round_decimal(cum_tax_base_new),
        "income_tax_gross": round_decimal(income_tax_gross),
        "income_tax_exemption": round_decimal(income_tax_exemption),
        "income_tax_net": round_decimal(income_tax_net),
        "stamp_tax_gross": stamp_tax_calc["gross"],
        "stamp_tax_exemption": stamp_tax_calc["exemption"],
        "stamp_tax_net": stamp_tax_calc["net"],
        "net": round_decimal(net_salary)
    }

def find_gross_salary(
    target_net: Decimal,
    cum_tax_base_prev: Decimal,
    employee_type: str,
    year_params: Dict[str, Any],
    month: int = 1,
    tolerance: Decimal = Decimal("0.01")
) -> Decimal:
    """
    Netten brüte hesaplama (Binary Search).
    """
    # Alt sınır: Hedef net (Vergisiz olsa bile net brütten büyük olamaz -istisnalar hariç ama genelde böyle-)
    # Üst sınır: Hedef netin 3 katı (Güvenli aralık)
    low = target_net
    high = target_net * 3
    
    # Brüt asgari ücretin altında olamaz
    min_wage = Decimal(str(year_params["min_wage_gross"]))
    if low < min_wage:
        low = min_wage # En azından asgari ücreti dene
        if high < min_wage: 
            high = min_wage * 2

    # Binary search (max 50 iterasyon)
    best_gross = low
    min_diff = Decimal("999999")
    
    for _ in range(50):
        mid = (low + high) / 2
        # Virgülden sonra 2 hane ile çalışalım ki sonsuz döngü olmasın
        mid = round_decimal(mid)
        
        result = calculate_pay_slip(mid, cum_tax_base_prev, employee_type, year_params, month)
        net_calc = result["net"]
        
        diff = net_calc - target_net
        
        if abs(diff) < min_diff:
            min_diff = abs(diff)
            best_gross = mid
            
        if abs(diff) <= tolerance:
            return mid
        
        if net_calc < target_net:
            low = mid
        else:
            high = mid
            
    return best_gross
