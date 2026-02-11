import argparse
from decimal import Decimal
from core import payroll, params
import json

def main():
    parser = argparse.ArgumentParser(description="Türk Bordro Motoru CLI (2026)")
    parser.add_argument("--mode", choices=["gross_to_net", "net_to_gross"], required=True, help="Hesaplama modu")
    parser.add_argument("--amount", type=str, required=True, help="Tutar (Brüt veya Hedef Net)")
    parser.add_argument("--cum_base", type=str, default="0", help="Kümülatif GV Matrahı (Varsayılan: 0)")
    parser.add_argument("--type", choices=["normal_4a", "emekli_sgdp"], default="normal_4a", help="Çalışan Tipi")
    
    args = parser.parse_args()
    
    year_params = params.load_params(2026)
    amount = Decimal(args.amount)
    cum_base = Decimal(args.cum_base)
    
    print(f"--- 2026 Bordro Hesabı ({args.mode}) ---")
    print(f"Girdi Tutar: {amount}")
    print(f"Çalışan: {args.type}")
    print("-" * 30)

    if args.mode == "gross_to_net":
        result = payroll.calculate_pay_slip(
            gross=amount,
            cum_tax_base_prev=cum_base,
            employee_type=args.type,
            year_params=year_params
        )
        # Decimal'ları string'e çevirerek güzel basalım
        print(json.dumps(result, default=str, indent=2, ensure_ascii=False))
        
    elif args.mode == "net_to_gross":
        gross = payroll.find_gross_salary(
            target_net=amount,
            cum_tax_base_prev=cum_base,
            employee_type=args.type,
            year_params=year_params
        )
        print(f"Hedef Net: {amount} TL")
        print(f"Gereken Brüt: {gross} TL")
        print("-" * 30)
        print("Sağlama (Brütten Nete):")
        result = payroll.calculate_pay_slip(gross, cum_base, args.type, year_params)
        print(f"Hesaplanan Net: {result['net']} TL")

if __name__ == "__main__":
    main()
