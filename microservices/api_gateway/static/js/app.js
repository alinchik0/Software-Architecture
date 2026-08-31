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

        async showPlaylistSelector(trackId) {
        try {
            // Получаем список плейлистов пользователя
            const playlists = await API.request(`/users/${this.currentUser.id}/playlists`);

            if (!playlists || playlists.length === 0) {
                UI.showToast('У вас пока нет плейлистов. Создайте первый!', 'info');
                return;
            }

            // Создаём модальное окно
            const modal = document.createElement('div');
            modal.id = 'playlist-selector-modal';
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;';

            modal.innerHTML = `
                <div style="background: #1a1a1a; padding: 30px; border-radius: 12px; max-width: 400px; width: 90%; max-height: 80vh; overflow-y: auto;">
                    <h3 style="margin-top: 0; margin-bottom: 20px;">Выберите плейлист</h3>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        ${playlists.map(pl => `
                            <div onclick="App.addTrackToPlaylist('${trackId}', ${pl.playlist_id})"
                                 style="padding: 15px; background: #2a2a2a; border-radius: 8px; cursor: pointer; transition: background 0.2s;"
                                 onmouseover="this.style.background='#3a3a3a'"
                                 onmouseout="this.style.background='#2a2a2a'">
                                <div style="font-weight: bold;">${pl.title}</div>
                                <div style="color: #aaa; font-size: 0.85em; margin-top: 4px;">${pl.description || 'Без описания'}</div>
                            </div>
                        `).join('')}
                    </div>
                    <button onclick="document.getElementById('playlist-selector-modal').remove()"
                            style="margin-top: 20px; width: 100%; padding: 12px; background: #444; border: none; color: white; border-radius: 8px; cursor: pointer; font-weight: bold;">Отмена</button>
                </div>
            `;

            document.body.appendChild(modal);

            // Закрытие по клику на фон
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.remove();
            });
        } catch (err) {
            UI.showToast('Ошибка загрузки плейлистов: ' + err.message, 'error');
        }
    },

    async addTrackToPlaylist(trackId, playlistId) {
        // Закрываем модальное окно
        const modal = document.getElementById('playlist-selector-modal');
        if (modal) modal.remove();

        try {
            await API.request(`/playlists/${playlistId}/tracks`, 'POST', {
                spotify_track_id: trackId,
                position: 0
            });

            UI.showToast('Трек добавлен в плейлист!', 'success');
        } catch (err) {
            // Обрабатываем случай дубликата
            const message = err.message && err.message.toLowerCase().includes('already')
                ? 'Этот трек уже есть в плейлисте'
                : 'Ошибка добавления: ' + err.message;
            UI.showToast(message, 'error');
        }
    },

        playPlaylist(playlistId) {
        // Находим плейлист в текущем отображении (или можно сделать запрос, но мы уже загрузили его)
        // Для простоты мы возьмем треки из текущего отображения, но лучше запросить заново,
        // чтобы убедиться в актуальности. Сделаем запрос:
        API.request(`/playlists/${playlistId}`)
            .then(playlist => {
                if (playlist.tracks && playlist.tracks.length > 0) {
                    // Преобразуем формат треков из API в формат, который понимает Player
                    const queue = playlist.tracks.map(t => ({
                        id: t.spotify_track_id,
                        title: t.title || 'Неизвестно',
                        artist: t.artist || 'Неизвестный исполнитель',
                        cover: t.cover || ''
                    }));

                    // Запускаем плеер с этой очередью
                    Player.setQueue(queue, 0);
                    UI.showToast('Воспроизведение началось', 'success');
                } else {
                    UI.showToast('Плейлист пуст', 'info');
                }
            })
            .catch(err => {
                UI.showToast('Ошибка загрузки плейлиста: ' + err.message, 'error');
            });
    },

        async removeTrackFromPlaylist(playlistId, trackId) {
        if (!confirm('Удалить этот трек из плейлиста?')) {
            return;
        }

        try {
            // ЯВНО преобразуем в строку, чтобы избежать сравнения числа со строкой в БД
            await API.request(`/playlists/${playlistId}/tracks/${String(trackId)}`, 'DELETE');

            UI.showToast('Трек удален из плейлиста', 'success');
            this.openPlaylist(playlistId);
        } catch (err) {
            UI.showToast('Ошибка удаления: ' + err.message, 'error');
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
        try {
            // Запрашиваем детали плейлиста
            const playlist = await API.request(`/playlists/${id}`);

            // Проверяем, является ли текущий пользователь владельцем (для кнопки удаления)
            const isOwner = playlist.owner_id === this.currentUser.id;

            // Передаем данные в UI
            UI.renderPlaylistDetail(playlist, isOwner);
        } catch (err) {
            UI.showToast('Не удалось загрузить плейлист: ' + err.message, 'error');
            // В случае ошибки (например, плейлист удален или нет доступа) возвращаем в медиатеку
            this.navigate('library');
        }
    },

    async deletePlaylist(id) {
        // Защита от случайного нажатия
        if (!confirm('Вы уверены, что хотите удалить этот плейлист? Это действие нельзя отменить.')) {
            return;
        }

        try {
            // Отправляем запрос на удаление.
            // Примечание: Бэкенд при успешном удалении должен опубликовать событие 'playlist.deleted' в Kafka
            await API.request(`/playlists/${id}`, 'DELETE');

            UI.showToast('Плейлист успешно удален', 'success');

            // Возвращаемся в медиатеку, где список обновится
            this.navigate('library');
        } catch (err) {
            UI.showToast('Ошибка удаления: ' + err.message, 'error');
        }
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
