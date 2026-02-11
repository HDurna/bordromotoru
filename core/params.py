import json
import os
from decimal import Decimal
from typing import Dict, Any, Optional

# Rakamları Decimal'a çevirmek için yardımcı
def _decimal_hook(obj):
    for key, value in obj.items():
        if isinstance(value, float):
            obj[key] = Decimal(str(value))
        elif isinstance(value, int) and key not in ["year", "up_to"]:
             # year ve up_to (eğer int ise) hariç parasal değerleri Decimal yapalım
             # Ancak tarife limitleri (up_to) bazen int gelir, bunları da Decimal yapmak hesapta kolaylık sağlar
             pass
    return obj

def load_params(year: int, data_dir: str = None) -> Dict[str, Any]:
    """
    Belirtilen yıl için parametre dosyasını yükler.
    """
    if data_dir is None:
        # Varsayılan olarak projenin 'data' klasörüne bak
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_path, "data")
    
    filename = f"params_{year}.json"
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Parametre dosyası bulunamadı: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # JSON verilerini Decimal'a dönüştürme (float hassasiyet kaybını önlemek için manuel parsing önerilir 
    # ancak basitlik adına burada recursive dönüşüm yapacağız veya parse_float kullanacağız)
    # Standart json.load float döndürür. Decimal için parse_float argümanı en temizidir.
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f, parse_float=Decimal)
    
    return data

def get_rate(params: Dict, employee_type: str, rate_key: str) -> Decimal:
    """Belirli bir çalışan tipi için oranı döndürür."""
    try:
        val = params["rates"][employee_type][rate_key]
        return Decimal(str(val)) if not isinstance(val, Decimal) else val
    except KeyError:
        raise ValueError(f"Geçersiz çalışan tipi veya oran anahtarı: {employee_type} -> {rate_key}")

def get_tariff(params: Dict) -> list:
    """Vergi tarifesini döndürür."""
    # up_to değerlerinin Decimal olduğundan emin olalım
    tariff = []
    for dilute in params["income_tax_tariff"]:
        up_to = dilute["up_to"]
        if up_to is not None:
            up_to = Decimal(str(up_to))
        rate = Decimal(str(dilute["rate"]))
        tariff.append({"up_to": up_to, "rate": rate})
    return tariff
