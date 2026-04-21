// Formatting Utilities

const utils = {
    // Format timestamp to localized readable string
    formatDate: (timestampStr) => {
        if (!timestampStr) return '-';
        const date = new Date(timestampStr.replace(' ', 'T')); // fixing typical mysql format
        return date.toLocaleDateString('id-ID', {
            day: 'numeric', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    },

    formatTimeOnly: (timestampStr) => {
        if (!timestampStr) return '-';
        const date = new Date(timestampStr.replace(' ', 'T'));
        return date.toLocaleTimeString('id-ID', {
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    },

    // Format IDR Currency
    formatRupiah: (number) => {
        return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(number);
    },

    // Safe number formatting
    formatNumber: (number, decimals = 1) => {
        const num = parseFloat(number);
        return isNaN(num) ? '0' : num.toFixed(decimals);
    }
};

window.utils = utils;
