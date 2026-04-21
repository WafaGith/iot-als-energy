/**
 * sidebar.js - Mengurus pemuatan sidebar secara dinamis ke semua halaman
 * Cara pakai: tambahkan <script src="assets/js/sidebar.js"></script>
 * setelah api.js di setiap halaman (sebelum script lain).
 */
(async function () {
    const container = document.getElementById('sidebar-container');
    if (!container) return; // Halaman ini tidak pakai sidebar

    try {
        const res = await fetch('/components/sidebar.html');
        if (!res.ok) throw new Error('Gagal memuat sidebar');
        const html = await res.text();

        // Inject sidebar HTML ke dalam container
        container.innerHTML = html;

        // --- Tandai menu aktif berdasarkan halaman saat ini ---
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        const navLinks = container.querySelectorAll('.nav-item');
        navLinks.forEach(link => {
            const href = link.getAttribute('href') || '';
            if (href === currentPage || (currentPage === '' && href === 'index.html')) {
                link.classList.add('active');
            }
        });

        // --- Setup tombol toggle sidebar untuk mobile ---
        const toggleBtn = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');

        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('show');
            });

            // Tutup sidebar jika klik di luar area sidebar (pada mobile)
            document.addEventListener('click', (e) => {
                if (
                    window.innerWidth <= 768 &&
                    sidebar.classList.contains('show') &&
                    !sidebar.contains(e.target) &&
                    !toggleBtn.contains(e.target)
                ) {
                    sidebar.classList.remove('show');
                }
            });
        }

        // --- Tampilkan nama user dari token JWT (jika tersedia) ---
        try {
            const token = localStorage.getItem('token');
            if (token) {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const nameEl = container.querySelector('.user-profile p');
                if (nameEl && payload.username) {
                    nameEl.textContent = payload.username;
                }
            }
        } catch (_) {
            // Abaikan jika token tidak valid / tidak ada
        }

    } catch (err) {
        console.error('Sidebar load error:', err);
        // Tampilkan pesan fallback agar layout tidak rusak
        container.innerHTML = `
            <aside id="sidebar" style="width:260px;background:#1e293b;display:flex;align-items:center;justify-content:center;padding:1rem;">
                <p style="color:#ef4444;font-size:0.75rem;">Gagal memuat sidebar</p>
            </aside>`;
    }
})();
