const API_BASE_URL = '/api'; // Menggunakan relative path agar otomatis mengikuti origin browser

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

// Redirect ke login jika tidak ada token dan bukan di halaman login
function checkAuth() {
    if (!getToken() && !window.location.pathname.endsWith('login.html')) {
        window.location.href = 'login.html';
    }
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Unauthorized / Token expired
            const errBody = await response.json().catch(() => ({}));
            alert("Terjadi 401 Unauthorized! Alasan: " + JSON.stringify(errBody));
            clearToken();
            window.location.href = 'login.html';
            return { error: true, message: 'Sesi berakhir, silakan login kembali.' };
        }

        const data = await response.json();
        if (!response.ok) {
            return { error: true, ...data };
        }
        return data;
    } catch (error) {
        console.error('API Fetch Error:', error);
        return { error: true, message: 'Tidak dapat terhubung ke server.' };
    }
}

// Export functions for other scripts
window.api = {
    fetch: apiFetch,
    getToken,
    setToken,
    clearToken,
    checkAuth,
    BASE_URL: API_BASE_URL
};
