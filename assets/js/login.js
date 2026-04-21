document.addEventListener('DOMContentLoaded', () => {
    // Redirect context if already logged in
    if (window.api && window.api.getToken()) {
        window.location.href = 'index.html';
    }

    const form = document.getElementById('login-form');
    const errorMsg = document.getElementById('error-msg');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const usernameInput = document.getElementById('username').value;
        const passwordInput = document.getElementById('password').value;
        const btn = form.querySelector('button');

        // Loading state
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating...';
        btn.disabled = true;
        errorMsg.classList.add('hidden');

        try {
            const response = await fetch(`${window.api.BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: usernameInput, password: passwordInput })
            });

            const data = await response.json();

            if (response.ok && data.token) {
                window.api.setToken(data.token);
                window.location.href = 'index.html';
            } else {
                errorMsg.textContent = data.message || 'Login gagal. Periksa kembali kredensial Anda.';
                errorMsg.classList.remove('hidden');
            }
        } catch (err) {
            errorMsg.textContent = 'Tidak dapat menghubungi server backend.';
            errorMsg.classList.remove('hidden');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
});
