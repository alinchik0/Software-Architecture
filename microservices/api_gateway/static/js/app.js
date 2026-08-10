const App = {
    currentUser: null,

    init() {
        Player.init();
        const token = localStorage.getItem('music_app_token');
        const userStr = localStorage.getItem('music_app_user');

        if (token && userStr) {
            this.currentUser = JSON.parse(userStr);
            this.showApp();
        } else {
            this.showAuth();
        }

        // Навигация по сайдбару
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.navigate(e.target.dataset.view);
            });
        });

        // Обработчик формы создания плейлиста (делегирование событий)
        document.getElementById('app-content').addEventListener('submit', async (e) => {
            if (e.target.id === 'create-pl-form') {
                e.preventDefault();
                await this.createPlaylist();
            }
        });
    },

    showAuth() {
        document.getElementById('auth-screen').classList.add('active');
        document.getElementById('app-screen').classList.remove('active');
    },

    showApp() {
        document.getElementById('auth-screen').classList.remove('active');
        document.getElementById('app-screen').classList.add('active');
        document.getElementById('user-email').textContent = this.currentUser.email;
        this.navigate('library');
    },

    navigate(view) {
        if (view === 'library') this.loadLibrary();
        else if (view === 'search') this.renderSearchView();
        else if (view === 'create') UI.renderCreatePlaylist();
    },

    async handleLogin() {
        await this.authAction('/auth/login', 'Вход выполнен!');
    },

    async handleRegister() {
        await this.authAction('/auth/register', 'Регистрация успешна! Теперь войдите.');
    },

    async authAction(endpoint, successMsg) {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        try {
            const data = await API.request(endpoint, 'POST', { email, password });
            if (endpoint === '/auth/login') {
                localStorage.setItem('music_app_token', data.access_token);
                // Извлекаем user_id из JWT (упрощенно) или берем из ответа, если бэкенд отдает
                this.currentUser = { email: email, id: data.user_id || '1' };
                localStorage.setItem('music_app_user', JSON.stringify(this.currentUser));
                this.showApp();
            } else {
                UI.showToast(successMsg, 'success');
            }
        } catch (err) {
            document.getElementById('auth-error').textContent = err.message;
        }
    },

    logout() {
        localStorage.removeItem('music_app_token');
        localStorage.removeItem('music_app_user');
        this.currentUser = null;
        this.showAuth();
    },

    async loadLibrary() {
    try {
        // ПРАВИЛЬНЫЙ эндпоинт: получаем плейлисты конкретного пользователя
        const playlists = await API.request(`/users/${this.currentUser.id}/playlists`);
        UI.renderLibrary(playlists);
    } catch (err) {
        UI.showToast('Не удалось загрузить плейлисты', 'error');
        console.error(err);
    }
},

    renderSearchView() {
        document.getElementById('app-content').innerHTML = `
            <h2>Поиск музыки (Deezer)</h2>
            <div style="display: flex; gap: 10px; margin: 20px 0;">
                <input type="text" id="search-input" placeholder="Исполнитель или название..." style="flex: 1; padding: 12px; background: #333; border: none; color: white; border-radius: 4px;">
                <button onclick="App.doSearch()" style="padding: 12px 24px; background: var(--accent); color: black; border: none; border-radius: 20px; font-weight: bold; cursor: pointer;">Найти</button>
            </div>
            <div id="search-results-container"></div>
        `;
    },

    async doSearch() {
        const query = document.getElementById('search-input').value;
        if (!query) return;

        document.getElementById('search-results-container').innerHTML = '<p>Поиск...</p>';
        try {
            const data = await API.request(`/catalog/search?q=${encodeURIComponent(query)}&limit=10`);
            UI.renderSearchResults(data.tracks);
        } catch (err) {
            UI.showToast('Ошибка поиска', 'error');
        }
    },

    async createPlaylist() {
        const title = document.getElementById('pl-title').value;
        const description = document.getElementById('pl-desc').value;
        try {
            await API.request('/playlists', 'POST', { title, description, is_public: true });
            UI.showToast('Плейлист создан!', 'success');
            this.navigate('library');
        } catch (err) {
            UI.showToast('Ошибка создания: ' + err.message, 'error');
        }
    },

    async openPlaylist(id) {
        UI.showToast('Загрузка плейлиста...', 'info');
        // Здесь будет логика открытия детальной страницы плейлиста (День 3)
        // Пока просто заглушка
        document.getElementById('app-content').innerHTML = `<h2>Плейлист #${id}</h2><p>Детальный просмотр будет реализован в День 3.</p><button onclick="App.navigate('library')" style="margin-top:20px; padding: 10px;">Назад</button>`;
    }
};

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => App.init());