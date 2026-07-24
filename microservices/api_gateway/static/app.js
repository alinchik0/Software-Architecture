// Базовый URL API. Если HTML открывается через FastAPI StaticFiles, оставляем пустым (относительный путь).
// Если открываете файл напрямую (file://), замените на 'http://localhost:8000'
const API_BASE = '';

let currentToken = localStorage.getItem('music_app_token');
let currentPlaylists = [];
let activePlaylistId = null;

// === Инициализация ===
document.addEventListener('DOMContentLoaded', () => {
    if (currentToken) {
        showAppScreen();
        loadPlaylists();
    } else {
        showAuthScreen();
    }

    // Обработчик создания плейлиста
    document.getElementById('create-playlist-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createPlaylist();
    });
});

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
            currentToken = data.access_token; // Адаптируйте под имя поля вашего JWT
            localStorage.setItem('music_app_token', currentToken);
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
    currentToken = null;
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

    // Подсветка кнопок сайдбара
    if(viewName === 'library') document.querySelectorAll('.nav-btn')[0].classList.add('active');
    if(viewName === 'create') document.querySelectorAll('.nav-btn')[1].classList.add('active');
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
    const container = document.getElementById('playlists-container');
    container.innerHTML = '<p class="empty-state">Загрузка...</p>';

    try {
        // Адаптируйте путь '/playlists' под ваш реальный роутинг в api_gateway
        currentPlaylists = await apiCall('/playlists');
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
        <div class="playlist-card" onclick="openPlaylist(${pl.id})">
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
        // Этот запрос пойдет в api_gateway -> gRPC -> playlist_service -> Kafka Producer
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
    const pl = currentPlaylists.find(p => p.id === id);
    document.getElementById('detail-title').textContent = pl.title;
    document.getElementById('detail-desc').textContent = pl.description || '';
    document.getElementById('tracks-list').innerHTML = '<li>Загрузка треков...</li>';

    showView('detail');

    try {
        // Адаптируйте путь под ваш API
        const tracks = await apiCall(`/playlists/${id}/tracks`);
        renderTracks(tracks);
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
            <span>${idx + 1}. ${t.title || t.track_url || 'Неизвестный трек'}</span>
            <span style="font-size: 0.8rem">▶</span>
        </li>
    `).join('');
}

async function addTrack() {
    const url = document.getElementById('track-url').value;
    if (!url || !activePlaylistId) return;

    try {
        await apiCall(`/playlists/${activePlaylistId}/tracks`, 'POST', { track_url: url });
        document.getElementById('track-url').value = '';
        openPlaylist(activePlaylistId); // Перезагрузить список
    } catch (err) {
        alert('Ошибка добавления трека: ' + err.message);
    }
}