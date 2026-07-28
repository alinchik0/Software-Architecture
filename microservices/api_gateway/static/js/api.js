const API = {
    getToken: () => localStorage.getItem('music_app_token'),

    async request(endpoint, method = 'GET', body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const config = { method, headers };
        if (body) config.body = JSON.stringify(body);

        const res = await fetch(`${API_BASE}${endpoint}`, config);
        if (res.status === 401) {
            App.logout();
            throw new Error('Сессия истекла');
        }
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка сервера');
        }
        return res.json();
    }
};