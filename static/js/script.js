document.addEventListener('DOMContentLoaded', function () {

    // Mode Switching
    const modeBtns = document.querySelectorAll('.mode-btn');
    const modeInput = document.getElementById('mode');
    const amountLabel = document.getElementById('amountLabel');

    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // UI Toggle
            modeBtns.forEach(b => {
                b.classList.remove('bg-white', 'shadow-sm', 'text-primary');
                b.classList.add('text-gray-500', 'hover:bg-gray-50');
            });
            btn.classList.remove('text-gray-500', 'hover:bg-gray-50');
            btn.classList.add('bg-white', 'shadow-sm', 'text-primary');

            // Logic
            const mode = btn.dataset.mode;
            modeInput.value = mode;

            if (mode === 'gross_to_net') {
                amountLabel.textContent = 'Brüt Tutar (TL)';
            } else {
                amountLabel.textContent = 'Hedef Net Tutar (TL)';
            }
        });
    });

    // Form Submittion
    const form = document.getElementById('calcForm');
    const resultPanel = document.getElementById('resultPanel');
    const emptyState = document.getElementById('emptyState');
    let salaryChart = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Hesaplanıyor...';
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75');

        // Form verisini JSON'a çevir
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => data[key] = value);

        console.log("Sending data:", data);

        try {
            const response = await fetch('/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            console.log("Result:", result);

            if (result.success) {
                displayResults(result.data);
                resultPanel.classList.remove('hidden');
                emptyState.classList.add('hidden');
                // Smooth scroll to results on mobile
                if (window.innerWidth < 1024) {
                    resultPanel.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                alert('Hata: ' + result.error);
            }

        } catch (error) {
            console.error('Error:', error);
            alert('Bir hata oluştu. Sunucu çalışıyor mu?');
        } finally {
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75');
        }
    });

    function formatMoney(amount) {
        if (!amount) return '0.00 ₺';
        return new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount) + ' ₺';
    }

    function displayResults(d) {
        // Cards
        document.getElementById('res_net').textContent = formatMoney(d.net);
        document.getElementById('res_gross').textContent = formatMoney(d.gross);

        // Kesintiler toplamı: SGK + İşsizlik + GV + DV
        // API'den gelen veriler string olarak gelebilir, parseFloat güvenli.
        const sgkTotal = parseFloat(d.sgk_employee) + parseFloat(d.unemployment_employee);
        const taxTotal = parseFloat(d.income_tax_net) + parseFloat(d.stamp_tax_net);
        const totalDeduction = sgkTotal + taxTotal;

        const grossVal = parseFloat(d.gross);
        const deductionRate = grossVal > 0 ? (totalDeduction / grossVal) * 100 : 0;

        document.getElementById('res_deduction').textContent = formatMoney(totalDeduction);
        document.getElementById('res_deduction_rate').textContent = '%' + deductionRate.toFixed(1) + ' Kesinti Oranı';

        // Table
        const fields = [
            'gross', 'pek', 'sgk_employee', 'unemployment_employee',
            'income_tax_base_month', 'cum_tax_base_new',
            'income_tax_gross', 'income_tax_exemption', 'income_tax_net',
            'stamp_tax_gross', 'stamp_tax_exemption', 'stamp_tax_net'
        ];

        fields.forEach(field => {
            const el = document.getElementById('tbl_' + field.replace('employee', '').replace('income_tax', 'gv').replace('stamp_tax', 'dv').replace('base_month', 'base'));
            // ID eşleşmesi biraz karışık oldu, manuel set edelim daha temiz
        });

        // Manuel Mapping
        document.getElementById('tbl_gross').textContent = formatMoney(d.gross);
        document.getElementById('tbl_pek').textContent = formatMoney(d.pek);
        document.getElementById('tbl_sgk').textContent = formatMoney(d.sgk_employee);
        document.getElementById('tbl_unemp').textContent = formatMoney(d.unemployment_employee);
        document.getElementById('tbl_gv_base').textContent = formatMoney(d.income_tax_base_month);
        document.getElementById('tbl_cum_base').textContent = formatMoney(d.cum_tax_base_new);
        document.getElementById('tbl_gv_gross').textContent = formatMoney(d.income_tax_gross);
        document.getElementById('tbl_gv_exemption').textContent = formatMoney(d.income_tax_exemption);
        document.getElementById('tbl_gv_net').textContent = formatMoney(d.income_tax_net);
        document.getElementById('tbl_dv_gross').textContent = formatMoney(d.stamp_tax_gross);
        document.getElementById('tbl_dv_exemption').textContent = formatMoney(d.stamp_tax_exemption);
        document.getElementById('tbl_dv_net').textContent = formatMoney(d.stamp_tax_net);


        // Chart
        updateChart(parseFloat(d.net), sgkTotal, parseFloat(d.income_tax_net), parseFloat(d.stamp_tax_net));
    }

    function updateChart(net, sgk, gv, dv) {
        const ctx = document.getElementById('salaryChart').getContext('2d');

        if (salaryChart) {
            salaryChart.destroy();
        }

        salaryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Net Maaş', 'SGK & İşsizlik', 'Gelir Vergisi', 'Damga Vergisi'],
                datasets: [{
                    data: [net, sgk, gv, dv],
                    backgroundColor: [
                        '#10b981', // Net - Green
                        '#ef4444', // SGK - Red
                        '#f97316', // GV - Orange
                        '#6366f1'  // DV - Indigo
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            font: { family: "'Inter', sans-serif", size: 11 }
                        }
                    }
                },
                cutout: '70%',
            }
        });
    }

});
