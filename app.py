from flask import Flask, render_template, request, jsonify
from decimal import Decimal
from core import payroll, params
import json

app = Flask(__name__)

# Özelleştirilmiş JSON Encoder (Decimal desteği için)
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        mode = data.get('mode')
        amount = Decimal(str(data.get('amount')))
        cum_base = Decimal(str(data.get('cum_base', '0')))
        employee_type = data.get('employee_type', 'normal_4a')
        year = int(data.get('year', 2026))

        year_params = params.load_params(year)

        if mode == 'gross_to_net':
            result = payroll.calculate_pay_slip(
                gross=amount,
                cum_tax_base_prev=cum_base,
                employee_type=employee_type,
                year_params=year_params
            )
            return jsonify({
                "success": True,
                "data": result,
                "input_gross": str(amount),
                "visual_data": {
                    "net": str(result['net']),
                    "taxes": str(result['income_tax_net'] + result['stamp_tax_net']),
                    "sgk": str(result['sgk_employee'] + result['unemployment_employee'])
                }
            })

        elif mode == 'net_to_gross':
            gross = payroll.find_gross_salary(
                target_net=amount,
                cum_tax_base_prev=cum_base,
                employee_type=employee_type,
                year_params=year_params
            )
            
            # Detayları göstermek için tekrar hesapla
            result = payroll.calculate_pay_slip(
                gross=gross,
                cum_tax_base_prev=cum_base,
                employee_type=employee_type,
                year_params=year_params
            )
            
            return jsonify({
                "success": True,
                "data": result,
                "input_net": str(amount),
                "found_gross": str(gross),
                "visual_data": {
                    "net": str(result['net']),
                    "taxes": str(result['income_tax_net'] + result['stamp_tax_net']),
                    "sgk": str(result['sgk_employee'] + result['unemployment_employee'])
                }
            })
            
        else:
            return jsonify({"success": False, "error": "Geçersiz mod"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
