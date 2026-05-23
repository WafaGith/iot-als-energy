document.addEventListener('DOMContentLoaded', () => {
    // Pastikan user login
    window.api.checkAuth();

    let chartM1, chartM2;
    let tarifPerKwh = 1444.70; // default, akan ditimpa setting
    let isFetching = false;

    // Inisialisasi ChartJS Theme
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";

    function initCharts() {
        const ctx1 = document.getElementById('chartM1').getContext('2d');
        const gradient1 = ctx1.createLinearGradient(0, 0, 0, 300);
        gradient1.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // blue
        gradient1.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        chartM1 = new Chart(ctx1, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Daya (W)', data: [], borderColor: '#3b82f6', backgroundColor: gradient1, fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, beginAtZero: true }
                },
                animation: { duration: 0 } // disable animation for realtime data
            }
        });

        const ctx2 = document.getElementById('chartM2').getContext('2d');
        const gradient2 = ctx2.createLinearGradient(0, 0, 0, 300);
        gradient2.addColorStop(0, 'rgba(139, 92, 246, 0.5)'); // purple
        gradient2.addColorStop(1, 'rgba(139, 92, 246, 0.0)');

        chartM2 = new Chart(ctx2, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Daya (W)', data: [], borderColor: '#8b5cf6', backgroundColor: gradient2, fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, beginAtZero: true }
                },
                animation: { duration: 0 }
            }
        });
    }

    async function loadSettings() {
        const response = await window.api.fetch('/settings');
        if (!response.error && response.tarif_per_kwh) {
            tarifPerKwh = parseFloat(response.tarif_per_kwh);
            document.getElementById('tarif_display').textContent = `Rp ${window.utils.formatNumber(tarifPerKwh, 0)}/kWh`;
        }
    }

    async function fetchRealtimeData() {
        if (isFetching) return;
        isFetching = true;

        const response = await window.api.fetch('/realtime');

        if (!response.error) {
            let m1 = response.m1 || {};
            let m2 = response.m2 || {};

            // 1. Cek Timeout (Offline / Staleness Check)
            // Menggunakan 75 detik karena hardware mengirim tiap 1 menit.
            let isStale = false;
            if (m1.timestamp) {
                const tString = m1.timestamp.replace(' ', 'T');
                const lastDate = new Date(tString);
                const diffSec = (new Date() - lastDate) / 1000;
                if (diffSec > 75) {
                    isStale = true;
                }
            } else {
                isStale = true;
            }

            if (isStale) {
                document.getElementById('status_sistem').innerText = 'Offline';
                document.getElementById('status_sistem').className = 'text-xl font-bold text-red-500 mt-1';
                // Jika mati, null-kan nilai realtime agar kembali jadi 0
                m1.daya = 0; m2.daya = 0;
            } else {
                document.getElementById('status_sistem').innerText = 'Online';
                document.getElementById('status_sistem').className = 'text-xl font-bold text-emerald-400 mt-1';
            }

            if (m1.timestamp) {
                document.getElementById('last_update').innerText = window.utils.formatTimeOnly(m1.timestamp);
            }

            // 2. Kalkulasi Data Summary
            const p1 = m1.daya || 0;
            const p2 = m2.daya || 0;

            // Total energi dari Database (paling akurat & kumulatif)
            const totalEnergiDb    = response.total_energi_db    || 0;
            const totalEnergiM1Db  = response.total_energi_m1_db || 0;
            const totalEnergiM2Db  = response.total_energi_m2_db || 0;

            const totalDaya = p1 + p2;
            const estimasiBiaya = totalEnergiDb * tarifPerKwh;

            // 3. Render ke layer tampilan DOM
            document.getElementById('total_daya').innerHTML = `${window.utils.formatNumber(totalDaya, 0)}<span class="text-lg text-gray-500 ml-1">W</span>`;
            document.getElementById('total_energi').innerHTML = `${window.utils.formatNumber(totalEnergiDb, 2)}<span class="text-lg text-gray-500 ml-1">kWh</span>`;
            document.getElementById('energi_m1_db').textContent = window.utils.formatNumber(totalEnergiM1Db, 2);
            document.getElementById('energi_m2_db').textContent = window.utils.formatNumber(totalEnergiM2Db, 2);
            document.getElementById('estimasi_biaya').innerText = window.utils.formatRupiah(estimasiBiaya);

            // Update Badges
            document.getElementById('badge_m1').innerText = `Status: ${p1 > 5 ? 'ON' : 'OFF'}`;
            document.getElementById('badge_m1').className = `px-2 py-1 rounded text-xs font-mono border ${p1 > 5 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-gray-800 text-gray-400 border-gray-600'}`;

            document.getElementById('badge_m2').innerText = `Status: ${p2 > 5 ? 'ON' : 'OFF'}`;
            document.getElementById('badge_m2').className = `px-2 py-1 rounded text-xs font-mono border ${p2 > 5 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-gray-800 text-gray-400 border-gray-600'}`;

            // Update charts history
            if (response.history_m1) {
                chartM1.data.labels = response.history_m1.map(d => d.timestamp);
                chartM1.data.datasets[0].data = response.history_m1.map(d => d.daya);
                chartM1.update();
            }
            if (response.history_m2) {
                chartM2.data.labels = response.history_m2.map(d => d.timestamp);
                chartM2.data.datasets[0].data = response.history_m2.map(d => d.daya);
                chartM2.update();
            }

        } else {
            document.getElementById('status_sistem').innerText = 'Koneksi Terputus';
            document.getElementById('status_sistem').className = 'text-xl font-bold text-red-500 mt-1';
        }

        isFetching = false;
    }

    // Initialize
    initCharts();
    loadSettings().then(() => {
        fetchRealtimeData();
        setInterval(fetchRealtimeData, 3000); // Poll every 3 seconds
    });
});
