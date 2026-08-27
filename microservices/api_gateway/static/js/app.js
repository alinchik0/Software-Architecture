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

//    renderSearchView() {
//        document.getElementById('app-content').innerHTML = `
//            <h2>Поиск музыки (Deezer)</h2>
//            <div style="display: flex; gap: 10px; margin: 20px 0;">
//                <input type="text" id="search-input" placeholder="Исполнитель или название..." style="flex: 1; padding: 12px; background: #333; border: none; color: white; border-radius: 4px;">
//                <button onclick="App.doSearch()" style="padding: 12px 24px; background: var(--accent); color: black; border: none; border-radius: 20px; font-weight: bold; cursor: pointer;">Найти</button>
//            </div>
//            <div id="search-results-container"></div>
//        `;
//    },
    renderSearchView() {
        const content = document.getElementById('app-content');

        // Создаем структуру поиска только если её еще нет
        // Это предотвращает потерю фокуса и исчезновение строки при обновлениях
        if (!document.getElementById('search-view-container')) {
            content.innerHTML = `
                <div id="search-view-container">
                    <h2>Поиск музыки</h2>
                    <div style="display: flex; gap: 10px; margin: 20px 0;">
                        <input type="text" id="search-input" placeholder="Исполнитель или название..."
                               style="flex: 1; padding: 12px; background: #333; border: none; color: white; border-radius: 4px;">
                        <button onclick="App.doSearch()" style="padding: 12px 24px; background: var(--accent, #1db954); color: black; border: none; border-radius: 20px; font-weight: bold; cursor: pointer;">Найти</button>
                    </div>
                    <div id="search-results-container">
                        <p style="color: #888;">Введите запрос или посмотрите популярные треки ниже</p>
                    </div>
                </div>
            `;

            // Добавляем обработчик нажатия Enter
            document.getElementById('search-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    App.doSearch();
                }
            });

            // Загружаем популярные треки при первом открытии вкладки
            this.loadPopularTracks();
        }
    },

    async loadPopularTracks() {
        const resultsContainer = document.getElementById('search-results-container');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = '<p>Загрузка популярных треков...</p>';
        try {
            // Используем общий запрос как заглушку для "популярного",
            // либо можно сделать отдельный эндпоинт, если он есть
            const data = await API.request(`/catalog/search?q=hit&limit=10`);
            this.currentSearchResults = data.tracks || [];

            if (this.currentSearchResults.length > 0) {
                UI.renderSearchResults(this.currentSearchResults, true); // true = это популярный список
            } else {
                resultsContainer.innerHTML = '<p>Начните вводить запрос для поиска</p>';
            }
        } catch (err) {
            resultsContainer.innerHTML = '<p>Начните вводить запрос для поиска</p>';
        }
    },

    async doSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput ? searchInput.value.trim() : '';

        if (!query) return;

        const resultsContainer = document.getElementById('search-results-container');
        resultsContainer.innerHTML = '<p>Поиск...</p>';

        try {
            const data = await API.request(`/catalog/search?q=${encodeURIComponent(query)}&limit=15`);
            this.currentSearchResults = data.tracks || [];

            // Передаем false, чтобы показать, что это результаты поиска, а не популярные треки
            UI.renderSearchResults(this.currentSearchResults, false);
        } catch (err) {
            UI.showToast('Ошибка поиска: ' + err.message, 'error');
            resultsContainer.innerHTML = '<p>Ничего не найдено или произошла ошибка</p>';
        }
    },

//    async doSearch() {
//        const query = document.getElementById('search-input').value;
//        if (!query) return;
//        document.getElementById('search-results-container').innerHTML = '<p>Поиск...</p>';
//        try {
//            const data = await API.request(`/catalog/search?q=${encodeURIComponent(query)}&limit=10`);
//
//            // <-- 2. ДОБАВИТЬ: сохраняем треки в App, прежде чем рисовать
//            this.currentSearchResults = data.tracks || [];
//
//            UI.renderSearchResults(this.currentSearchResults);
//        } catch (err) {
//            UI.showToast('Ошибка поиска', 'error');
//        }
//    },

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
    },
    playFromSearch(index) {
        if (!this.currentSearchResults || !this.currentSearchResults[index]) {
            UI.showToast('Ошибка: трек не найден', 'error');
            return;
        }
        // Передаем весь массив и индекс в плеер
        Player.setQueue(this.currentSearchResults, index);
    }
};

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => App.init());
