let currentSessionId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    loadCurrentSessionFromCookie();

    const textarea = document.getElementById('messageInput');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

async function loadSessions() {
    try {
        const res = await fetch('/sessions');
        const data = await res.json();
        renderSessionsList(data.sessions);
    } catch (e) { console.error('Error loading sessions:', e); }
}

function renderSessionsList(sessions) {
    const container = document.getElementById('sessionsList');
    if (sessions.length === 0) {
        container.innerHTML = '<div style="color: #5A6C7D; text-align: center; padding: 20px; font-size: 13px;">Нет сохранённых диалогов</div>';
        return;
    }
    container.innerHTML = sessions.map(s => `
        <div class="session-item ${s.id === currentSessionId ? 'active' : ''}" onclick="loadSession('${s.id}')">
            <div class="session-title">${escapeHtml(s.title)}</div>
            <div class="session-date">${formatDate(s.created_at)}</div>
        </div>
    `).join('');
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    document.cookie = `session_id=${sessionId}; path=/; max-age=${60*60*24*30}`;

    try {
        const res = await fetch(`/sessions/${sessionId}/messages`);
        const data = await res.json();
        renderMessages(data.messages);

        const session = JSON.parse(localStorage.getItem('sessions_cache') || '[]').find(s => s.id === sessionId);
        if (session) document.getElementById('currentSessionTitle').textContent = session.title;
    } catch (e) { console.error('Error loading messages:', e); }

    loadSessions();
}

function loadCurrentSessionFromCookie() {
    const match = document.cookie.match(/(?:^|; )session_id=([^;]*)/);
    if (match) {
        currentSessionId = decodeURIComponent(match[1]);
        loadSession(currentSessionId);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messagesContainer');
    if (messages.length === 0) {
        container.innerHTML = `<div class="welcome-message"><h2>👋 Добро пожаловать!</h2><p>Я помогу вам с управлением задачами и обучением.</p></div>`;
        return;
    }
    container.innerHTML = messages.map(msg => `
        <div class="message ${msg.role}">
            <div class="msg-avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
            <div class="msg-content">${escapeHtml(msg.content).replace(/\n/g, '<br>')}</div>
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

function createNewChat() {
    currentSessionId = null;
    document.cookie = "session_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.getElementById('currentSessionTitle').textContent = 'Новый диалог';
    renderMessages([]);
    loadSessions();
    document.getElementById('messageInput').focus();
}

async function sendMessage(event) {
    if (event) event.preventDefault();
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    input.style.height = 'auto';

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.innerHTML = '<div class="loading-spinner"></div>';
    sendBtn.disabled = true;

    // Optimistic UI update
    addMessageToDisplay('user', message);

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: currentSessionId })
        });
        const data = await res.json();

        if (!currentSessionId && data.session_id) {
            currentSessionId = data.session_id;
            document.cookie = `session_id=${currentSessionId}; path=/; max-age=${60*60*24*30}`;
            document.getElementById('currentSessionTitle').textContent = message.substring(0, 30) + '...';
        }

        addMessageToDisplay('assistant', data.response);
        await loadSessions();
    } catch (e) {
        console.error('Error:', e);
        addMessageToDisplay('assistant', '❌ Произошла ошибка. Попробуйте ещё раз.');
    } finally {
        sendBtn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        sendBtn.disabled = false;
    }
}

function addMessageToDisplay(role, content) {
    const container = document.getElementById('messagesContainer');
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="msg-content">${escapeHtml(content).replace(/\n/g, '<br>')}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const diff = Date.now() - date.getTime();
    if (diff < 60000) return 'Только что';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} мин. назад`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч. назад`;
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}