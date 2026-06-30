// ShopSphere main JavaScript
(function () {
    const toggle = document.getElementById('darkModeToggle');
    const html = document.documentElement;
    if (localStorage.getItem('darkMode') === 'true') html.classList.add('dark');
    if (toggle) {
        toggle.addEventListener('click', () => {
            html.classList.toggle('dark');
            localStorage.setItem('darkMode', html.classList.contains('dark'));
            toggle.textContent = html.classList.contains('dark') ? '☀️' : '🌙';
        });
        toggle.textContent = html.classList.contains('dark') ? '☀️' : '🌙';
    }
    // Auto-dismiss toasts
    document.querySelectorAll('.toast').forEach(el => {
        setTimeout(() => el.remove(), 5000);
    });
    // WebSocket notifications
    if (window.location.protocol.startsWith('http') && document.body.dataset.userId) {
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const ws = new WebSocket(`${wsScheme}://${window.location.host}/ws/notifications/`);
        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            const container = document.getElementById('toast-container') || document.body;
            const toast = document.createElement('div');
            toast.className = 'fixed top-20 right-4 bg-brand-600 text-white px-4 py-3 rounded-lg shadow-lg z-50';
            toast.textContent = data.title + ': ' + data.message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        };
    }
})();
