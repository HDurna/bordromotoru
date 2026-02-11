import unittest
from decimal import Decimal
from core import payroll, params

class TestPayrollCases(unittest.TestCase):
    
    def setUp(self):
        # 2026 parametrelerini yükle
        self.params_2026 = params.load_params(2026)
        self.min_wage = Decimal(str(self.params_2026["min_wage_gross"]))
        self.ceiling = Decimal(str(self.params_2026["sgk_ceiling_monthly"]))

    def test_case_01_min_wage_net(self):
        """Asgari ücretlinin net hesabını kontrol et."""
        # Kümülatif matrah 0 varsayalım (Ocak ayı)
        res = payroll.calculate_pay_slip(
            gross=self.min_wage,
            cum_tax_base_prev=Decimal("0"),
            employee_type="normal_4a",
            year_params=self.params_2026
        )
        # Asgari ücrette GV ve DV istisnası olduğu için;
        # Gelir vergisi net ödeme = 0 olmalı
        # Damga vergisi net ödeme = 0 olmalı
        self.assertEqual(res["income_tax_net"], Decimal("0.00"))
        self.assertEqual(res["stamp_tax_net"], Decimal("0.00"))
        
        # Net = Brüt - SGK - İşsizlik
        sgk = self.min_wage * Decimal("0.14")
        unemp = self.min_wage * Decimal("0.01")
        expected_net = self.min_wage - sgk - unemp
        self.assertEqual(res["net"], expected_net.quantize(Decimal("0.01")))

    def test_case_02_high_salary_ceiling(self):
        """Tavanı aşan maaş testi."""
        gross = self.ceiling + Decimal("10000")
        res = payroll.calculate_pay_slip(
            gross=gross,
            cum_tax_base_prev=Decimal("0"),
            employee_type="normal_4a",
            year_params=self.params_2026
        )
        
        # PEK tavan olmalı
        self.assertEqual(res["pek"], self.ceiling.quantize(Decimal("0.01")))
        
        # SGK tavan üzerinden hesaplanmalı
        expected_sgk = self.ceiling * Decimal("0.14")
        self.assertEqual(res["sgk_employee"], expected_sgk.quantize(Decimal("0.01")))

    def test_case_03_tax_bracket_transition(self):
        """Vergi dilimi geçişi kontrolü."""
        # Diyelim ki limit 150.000 TL.
        # Önceki kümülatif 140.000 TL olsun.
        # Bu ay matrah 20.000 TL olsun (Toplam 160.000 - dilimi geçti).
        # Vergi: (10.000 * %15) + (10.000 * %20) = 1500 + 2000 = 3500 TL (İstisna hariç brüt vergi)
        
        gross = Decimal("30000") # Yaklaşık bir brüt
        # Matrahını bulalım: 30000 * 0.85 = 25500
        # Biz manuel matrah belirleyemiyoruz fonksiyonda, o yüzden gross veriyoruz.
        
        # Kümülatif matrahı sınıra yakın verelim.
        # İlk dilim 150,000.
        cum_base = Decimal("140000")
        
        res = payroll.calculate_pay_slip(
            gross=Decimal("40000"), # PEK tavanın altında. Matrah ~34,000
            cum_tax_base_prev=cum_base,
            employee_type="normal_4a",
            year_params=self.params_2026
        )
        
        # Sadece Income Tax Gross'u kontrol edelim.
        # Matrah = 40000 - (40000*0.15) = 34000
        # Dilimler: 140,000 dolu.
        # 1. dilimden kalan hak: 150,000 - 140,000 = 10,000. (Oran %15) -> 1500 TL
        # Kalan matrah: 34,000 - 10,000 = 24,000. (Oran %20 - 2. dilim 350k'ya kadar) -> 4800 TL
        # Toplam Brüt Vergi = 1500 + 4800 = 6300 TL.
        
        matrah = res["income_tax_base_month"]
        # Hesaplanan matrah üzerinden doğrulama yapalım, gross'tan manuel hesapladık ama kuruş farkı olabilir.
        
        # Beklenen:
        remaining_in_first = Decimal("150000") - cum_base # 10000
        if matrah > remaining_in_first:
            part1 = remaining_in_first
            part2 = matrah - remaining_in_first
            expected_tax = (part1 * Decimal("0.15")) + (part2 * Decimal("0.20"))
        else:
            expected_tax = matrah * Decimal("0.15")
            
        self.assertAlmostEqual(res["income_tax_gross"], expected_tax, places=2)

    def test_case_04_net_to_gross(self):
        """Netten Brüte doğrulama (Round-trip)."""
        target_net = Decimal("50000.00")
        cum_base = Decimal("0")
        
        found_gross = payroll.find_gross_salary(
            target_net=target_net,
            cum_tax_base_prev=cum_base,
            employee_type="normal_4a",
            year_params=self.params_2026
        )
        
        # Bulunan brütü tekrar nete çevir
        res = payroll.calculate_pay_slip(
            gross=found_gross,
            cum_tax_base_prev=cum_base,
            employee_type="normal_4a",
            year_params=self.params_2026
        )
        
        # Tolerans 0.01
        self.assertTrue(abs(res["net"] - target_net) <= Decimal("0.02"), f"Hedef: {target_net}, Hesaplanan: {res['net']}")

    def test_case_05_retired_sgdp(self):
        """Emekli çalışan (SGDP) testi."""
        gross = Decimal("50000")
        res = payroll.calculate_pay_slip(
            gross=gross,
            cum_tax_base_prev=Decimal("0"),
            employee_type="emekli_sgdp",
            year_params=self.params_2026
        )
        
        # İşsizlik 0 olmalı
        self.assertEqual(res["unemployment_employee"], Decimal("0.00"))
        
        # SGK %7.5
        expected_sgdp = gross * Decimal("0.075")
        self.assertEqual(res["sgk_employee"], expected_sgdp.quantize(Decimal("0.01")))

if __name__ == '__main__':
    unittest.main()
