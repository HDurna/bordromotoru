"""
Bordro Motoru - Masaüstü Uygulaması (PyWebView)
Tarayıcıda değil, bağımsız pencerede çalışır.
"""
import webview
import json
import os
import webbrowser
from decimal import Decimal
from core import payroll, params
from core.analyzer import extract_text_from_pdf, parse_payslip, analyze_payslip

# Global referans (dosya diyalogu için)
_window = None

class BordroAPI:
    """JavaScript <-> Python köprüsü. Frontend'den çağrılır."""
    
    def __init__(self):
        self._year_params = None
        self._params_path = None
    
    def _get_params(self, year=2026):
        if self._year_params is None:
            self._year_params = params.load_params(year)
        return self._year_params
    
    def _get_params_path(self, year=2026):
        if self._params_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            self._params_path = os.path.join(base, "data", f"params_{year}.json")
        return self._params_path
    
    def calculate(self, mode, amount, cum_base, employee_type):
        try:
            year_params = self._get_params()
            amount = Decimal(str(amount))
            cum_base = Decimal(str(cum_base))
            
            if mode == 'gross_to_net':
                result = payroll.calculate_pay_slip(
                    gross=amount, cum_tax_base_prev=cum_base,
                    employee_type=employee_type, year_params=year_params
                )
            elif mode == 'net_to_gross':
                gross = payroll.find_gross_salary(
                    target_net=amount, cum_tax_base_prev=cum_base,
                    employee_type=employee_type, year_params=year_params
                )
                result = payroll.calculate_pay_slip(
                    gross=gross, cum_tax_base_prev=cum_base,
                    employee_type=employee_type, year_params=year_params
                )
                result['found_gross'] = str(gross)
            else:
                return json.dumps({"success": False, "error": "Geçersiz mod"})
            
            serializable = {k: str(v) for k, v in result.items()}
            return json.dumps({"success": True, "data": serializable})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def calculate_annual(self, gross, employee_type):
        try:
            year_params = self._get_params()
            gross_d = Decimal(str(gross))
            cum_base = Decimal("0")
            months = []
            for month in range(1, 13):
                result = payroll.calculate_pay_slip(
                    gross=gross_d, cum_tax_base_prev=cum_base,
                    employee_type=employee_type, year_params=year_params, month=month
                )
                cum_base = result["cum_tax_base_new"]
                serializable = {k: str(v) for k, v in result.items()}
                serializable["month"] = month
                months.append(serializable)
            return json.dumps({"success": True, "data": months})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def get_params_info(self):
        try:
            p = self._get_params()
            return json.dumps(p, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def save_params(self, params_json_str):
        try:
            new_params = json.loads(params_json_str)
            path = self._get_params_path(new_params.get("year", 2026))
            with open(path, "w", encoding="utf-8") as f:
                json.dump(new_params, f, indent=2, ensure_ascii=False)
            self._year_params = None
            self._params_path = None
            return json.dumps({"success": True})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    # ===== BORDRO ANALİZ =====
    def open_pdf_dialog(self):
        """Dosya seçme diyalogu açar ve PDF yolunu döndürür."""
        global _window
        try:
            # webview.FileDialog.OPEN (OPEN_DIALOG deprecated)
            dialog_type = getattr(webview, 'FileDialog', None)
            if dialog_type:
                open_type = dialog_type.OPEN
            else:
                open_type = webview.OPEN_DIALOG  # eski sürüm fallback
            result = _window.create_file_dialog(
                open_type,
                allow_multiple=False,
                file_types=('PDF Dosyaları (*.pdf)',)
            )
            if result and len(result) > 0:
                return json.dumps({"success": True, "path": result[0]})
            return json.dumps({"success": False, "error": "Dosya seçilmedi"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def analyze_pdf(self, pdf_path):
        """PDF bordro dosyasını analiz eder."""
        try:
            if not os.path.exists(pdf_path):
                return json.dumps({"success": False, "error": "Dosya bulunamadı"})
            
            # 1. PDF'den metin çıkar
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text or len(raw_text.strip()) < 20:
                return json.dumps({
                    "success": False,
                    "error": "PDF'den metin çıkarılamadı. Dosya taranmış bir görüntü olabilir."
                })
            
            # 2. Alanları parse et
            parsed = parse_payslip(raw_text)
            
            # 3. Analiz ve yorumla
            year_params = self._get_params()
            analysis = analyze_payslip(parsed, year_params)
            analysis["raw_text_preview"] = raw_text[:2000]  # İlk 2000 karakter
            analysis["filename"] = os.path.basename(pdf_path)
            
            return json.dumps({"success": True, "data": analysis})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def analyze_manual(self, values_json):
        """Kullanıcının manuel girdiği değerlerle analiz yapar."""
        try:
            vals = json.loads(values_json)
            
            # Manuel girişten parsed dict oluştur
            parsed = {}
            field_map = {
                "gross": "gross", "net": "net", "sgk": "sgk_employee",
                "unemp": "unemployment_employee", "gv": "income_tax",
                "dv": "stamp_tax", "sgk_base": "sgk_base", "cum": "cum_tax_base"
            }
            
            for input_key, field_key in field_map.items():
                val = vals.get(input_key, 0)
                if val and float(val) > 0:
                    parsed[field_key] = Decimal(str(val))
            
            if not parsed:
                return json.dumps({
                    "success": False,
                    "error": "En az bir alan doldurulmalıdır."
                })
            
            parsed["detected_month"] = None
            parsed["detected_year"] = None
            parsed["_generic_pairs"] = []
            
            critical = ["gross", "net", "sgk_employee", "income_tax"]
            found = sum(1 for f in critical if f in parsed)
            parsed["_parse_confidence"] = found / len(critical)
            parsed["_found_fields"] = [k for k in parsed if isinstance(parsed[k], Decimal)]
            parsed["_missing_critical"] = [f for f in critical if f not in parsed]
            
            year_params = self._get_params()
            analysis = analyze_payslip(parsed, year_params)
            analysis["filename"] = "Manuel Giriş"
            analysis["raw_text_preview"] = ""
            
            return json.dumps({"success": True, "data": analysis})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def open_external_url(self, url):
        """Varsayılan tarayıcıda URL açar (sosyal linkler için)."""
        try:
            webbrowser.open(url)
            return json.dumps({"success": True})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


def get_html_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "templates", "desktop.html")


if __name__ == '__main__':
    api = BordroAPI()
    
    _window = webview.create_window(
        title='Bordro Motoru 2026',
        url=get_html_path(),
        js_api=api,
        width=1280,
        height=900,
        min_size=(1000, 700),
        resizable=True,
        text_select=True,
    )
    
    webview.start(debug=False)
