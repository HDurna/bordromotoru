from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

def round_decimal(value: Decimal) -> Decimal:
    """Standart 2 hane yuvarlama."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_total_tax_liability(cumulative_base: Decimal, tariff: list) -> Decimal:
    """
    Sıfırdan başlayarak verilen kümülatif matrahın toplam vergisini hesaplar.
    Bu yöntem dilim geçişlerini otomatik yönetir.
    """
    total_tax = Decimal("0")
    remaining_base = cumulative_base
    previous_limit = Decimal("0")

    for bracket in tariff:
        limit = bracket["up_to"]
        rate = bracket["rate"]

        # Bu dilimin genişliği (limit None ise sonsuz)
        if limit is None:
            # Son dilim
            tax_in_bracket = remaining_base * rate
            total_tax += tax_in_bracket
            break
        else:
            bracket_width = limit - previous_limit
            
            if remaining_base > bracket_width:
                # Bu dilimi tamamen dolduruyor
                total_tax += bracket_width * rate
                remaining_base -= bracket_width
                previous_limit = limit
            else:
                # Bu dilimde bitiyor
                total_tax += remaining_base * rate
                remaining_base = Decimal("0")
                break
    
    return total_tax

def calculate_income_tax_cumulative(
    cum_base_prev: Decimal, 
    current_month_base: Decimal, 
    tariff: list
) -> Decimal:
    """
    Kümülatif yönteme göre o ayın vergisini hesaplar.
    Formül: Vergi(Eski + Yeni) - Vergi(Eski)
    """
    cum_base_new = cum_base_prev + current_month_base
    tax_total_new = calculate_total_tax_liability(cum_base_new, tariff)
    tax_total_prev = calculate_total_tax_liability(cum_base_prev, tariff)
    
    return tax_total_new - tax_total_prev

def calculate_stamp_tax(gross: Decimal, rate: Decimal, exemption_amount: Decimal = Decimal("0")) -> Dict[str, Decimal]:
    """
    Damga vergisi hesaplar.
    Döndürür: { 'gross': ..., 'exemption': ..., 'net': ... }
    """
    gross_tax = gross * rate
    # İstisna vergi tutarı (genelde asgari ücretin damga vergisi kadardır)
    # Ancak parametre olarak direkt istisna tutarı (TL) mi yoksa matrah (TL) mı geldiğine dikkat edilmeli.
    # Bu fonksiyonda 'exemption_amount' direkt düşülecek vergi tutarı olarak kabul edelim.
    
    net_tax = max(Decimal("0"), gross_tax - exemption_amount)
    
    return {
        "gross": round_decimal(gross_tax),
        "exemption": round_decimal(exemption_amount),
        "net": round_decimal(net_tax)
    }
