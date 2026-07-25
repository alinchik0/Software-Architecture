// microservices/api_gateway/static/app.js

const API_BASE = '';

let currentToken = localStorage.getItem('music_app_token');
let currentUser = JSON.parse(localStorage.getItem('music_app_user') || 'null');
let currentPlaylists = [];
let activePlaylistId = null;

// === Инициализация ===
document.addEventListener('DOMContentLoaded', () => {
    if (currentToken && currentUser) {
        showAppScreen();
        loadPlaylists();
    } else {
        showAuthScreen();
    }

    document.getElementById('create-playlist-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createPlaylist();
    });
});

// === Вспомогательные функции ===
function decodeJWT(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

// === Авторизация ===
async function handleLogin() {
    await authRequest('/auth/login', 'Вход выполнен!');
}

async function handleRegister() {
    await authRequest('/auth/register', 'Регистрация успешна! Теперь войдите.');
}

async function authRequest(endpoint, successMsg) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');
    errorEl.textContent = '';

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Ошибка сервера');

        if (endpoint === '/auth/login') {
            currentToken = data.access_token;
            const payload = decodeJWT(currentToken);
            currentUser = { id: payload.sub, email: email };

            localStorage.setItem('music_app_token', currentToken);
            localStorage.setItem('music_app_user', JSON.stringify(currentUser));

            document.getElementById('user-email').textContent = email;
            showAppScreen();
            loadPlaylists();
        } else {
            alert(successMsg);
        }
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

function logout() {
    localStorage.removeItem('music_app_token');
    localStorage.removeItem('music_app_user');
    currentToken = null;
    currentUser = null;
    showAuthScreen();
}

// === Навигация ===
function showAuthScreen() {
    document.getElementById('auth-screen').classList.add('active');
    document.getElementById('app-screen').classList.remove('active');
}

function showAppScreen() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
}

function showView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`view-${viewName}`).classList.add('active');

    if(viewName === 'library') document.querySelectorAll('.nav-btn')[0].classList.add('active');
    if(viewName === 'create') document.querySelectorAll('.nav-btn')[1].classList.add('active');
    if(viewName === 'search') document.querySelectorAll('.nav-btn')[2].classList.add('active');
}

// === Работа с данными (API) ===
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentToken}`
    };
    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${endpoint}`, config);
    if (res.status === 401) {
        logout();
        throw new Error('Сессия истекла');
    }
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка запроса');
    }
    return res.json();
}

async function loadPlaylists() {
    if (!currentUser) return;

    const container = document.getElementById('playlists-container');
    container.innerHTML = '<p class="empty-state">Загрузка...</p>';

    try {
        // ИСПРАВЛЕНО: используем правильный эндпоинт
        currentPlaylists = await apiCall(`/users/${currentUser.id}/playlists`);
        renderPlaylists();
    } catch (err) {
        container.innerHTML = `<p class="error">Не удалось загрузить плейлисты: ${err.message}</p>`;
    }
}

function renderPlaylists() {
    const container = document.getElementById('playlists-container');
    if (currentPlaylists.length === 0) {
        container.innerHTML = '<p class="empty-state">У вас пока нет плейлистов. Создайте первый!</p>';
        return;
    }

    container.innerHTML = currentPlaylists.map(pl => `
        <div class="playlist-card" onclick="openPlaylist(${pl.playlist_id})">
            <div class="playlist-cover">🎵</div>
            <div class="playlist-title">${pl.title}</div>
            <div class="playlist-desc">${pl.description || 'Без описания'}</div>
        </div>
    `).join('');
}

async function createPlaylist() {
    const title = document.getElementById('pl-title').value;
    const description = document.getElementById('pl-desc').value;
    const is_public = document.getElementById('pl-public').checked;

    try {
        const newPl = await apiCall('/playlists', 'POST', { title, description, is_public });
        alert('Плейлист создан! Событие отправлено в Kafka.');
        document.getElementById('create-playlist-form').reset();
        showView('library');
        loadPlaylists();
    } catch (err) {
        alert('Ошибка создания: ' + err.message);
    }
}

async function openPlaylist(id) {
    activePlaylistId = id;
    const pl = currentPlaylists.find(p => p.playlist_id === id);
    document.getElementById('detail-title').textContent = pl.title;
    document.getElementById('detail-desc').textContent = pl.description || '';
    document.getElementById('tracks-list').innerHTML = '<li>Загрузка треков...</li>';

    showView('detail');

    try {
        // ИСПРАВЛЕНО: используем правильный эндпоинт для получения одного плейлиста
        const playlistData = await apiCall(`/playlists/${id}`);
        renderTracks(playlistData.tracks);
    } catch (err) {
        document.getElementById('tracks-list').innerHTML = `<li class="error">Не удалось загрузить треки</li>`;
    }
}

function renderTracks(tracks) {
    const list = document.getElementById('tracks-list');
    if (!tracks || tracks.length === 0) {
        list.innerHTML = '<li>В этом плейлисте пока нет треков.</li>';
        return;
    }
    list.innerHTML = tracks.map((t, idx) => `
        <li>
            <span>${idx + 1}. ${t.title || 'Неизвестный трек'} - ${t.artist || 'Неизвестный исполнитель'}</span>
            <button onclick="removeTrack('${t.spotify_track_id}')" style="background: #e22134; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Удалить</button>
        </li>
    `).join('');
}

async function addTrack() {
    const url = document.getElementById('track-url').value;
    if (!url || !activePlaylistId) return;

    try {
        await apiCall(`/playlists/${activePlaylistId}/tracks`, 'POST', { spotify_track_id: url, position: 0 });
        document.getElementById('track-url').value = '';
        openPlaylist(activePlaylistId);
    } catch (err) {
        alert('Ошибка добавления трека: ' + err.message);
    }
}

async function removeTrack(trackId) {
    if (!activePlaylistId) return;

    try {
        await apiCall(`/playlists/${activePlaylistId}/tracks/${trackId}`, 'DELETE');
        openPlaylist(activePlaylistId);
    } catch (err) {
        alert('Ошибка удаления трека: ' + err.message);
    }
}

// === Поиск треков (новая функция) ===
async function searchTracks() {
    const query = document.getElementById('search-query').value;
    if (!query) return;

    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<p>Поиск...</p>';

    try {
        // Вызываем новый эндпоинт поиска (его нужно добавить в API Gateway)
        const results = await apiCall(`/catalog/search?q=${encodeURIComponent(query)}`);
        renderSearchResults(results.tracks || []);
    } catch (err) {
        resultsContainer.innerHTML = `<p class="error">Ошибка поиска: ${err.message}</p>`;
    }
}

function renderSearchResults(tracks) {
    const container = document.getElementById('search-results');
    if (tracks.length === 0) {
        container.innerHTML = '<p>Ничего не найдено</p>';
        return;
    }

    container.innerHTML = tracks.map(t => `
        <div class="search-result-item" style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333;">
            <div>
                <strong>${t.title}</strong><br>
                <small>${t.artist} - ${t.album}</small>
            </div>
            <button onclick="addTrackFromSearch('${t.id}')" style="background: var(--accent); color: black; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer;">+ Добавить</button>
        </div>
    `).join('');
}

async function addTrackFromSearch(trackId) {
    if (!activePlaylistId) {
        alert('Сначала откройте плейлист, чтобы добавить трек');
        return;
    }

    try {
        await apiCall(`/playlists/${activePlaylistId}/tracks`, 'POST', { spotify_track_id: trackId, position: 0 });
        alert('Трек добавлен!');
        openPlaylist(activePlaylistId);
    } catch (err) {
        alert('Ошибка добавления: ' + err.message);
    }
}