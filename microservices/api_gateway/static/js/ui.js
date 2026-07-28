const UI = {
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000); // Исчезает через 3 сек
    },

    renderLibrary(playlists) {
        const content = document.getElementById('app-content');
        if (!playlists || playlists.length === 0) {
            content.innerHTML = '<h2>Моя медиатека</h2><p class="empty-state">У вас пока нет плейлистов.</p>';
            return;
        }

        let html = '<h2>Моя медиатека</h2><div class="grid-container">';
        playlists.forEach(pl => {
            // Используем заглушку обложки для плейлиста, пока не добавим кастомные обложки
            html += `
                <div class="playlist-card" onclick="App.openPlaylist(${pl.playlist_id})">
                    <div class="card-cover">🎵</div>
                    <div class="card-title">${pl.title}</div>
                    <div class="card-desc">${pl.description || 'Без описания'}</div>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    },

    renderSearchResults(tracks) {
        const content = document.getElementById('app-content');
        if (!tracks || tracks.length === 0) {
            content.innerHTML = '<h2>Поиск</h2><p>Ничего не найдено.</p>';
            return;
        }

        let html = '<h2>Результаты поиска</h2><div class="grid-container">';
        tracks.forEach(track => {
            html += `
                <div class="track-card" onclick='Player.play(${JSON.stringify(track).replace(/'/g, "&#39;")})'>
                    <div class="card-cover">
                        ${track.cover ? `<img src="${track.cover}" alt="cover">` : '🎵'}
                    </div>
                    <div class="card-title">${track.title}</div>
                    <div class="card-desc">${track.artist}</div>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    },

    renderCreatePlaylist() {
        document.getElementById('app-content').innerHTML = `
            <h2>Создать новый плейлист</h2>
            <form id="create-pl-form" class="form-box" style="max-width: 500px; margin-top: 20px;">
                <input type="text" id="pl-title" placeholder="Название" required style="width: 100%; padding: 12px; margin-bottom: 10px; background: #333; border: none; color: white; border-radius: 4px;">
                <textarea id="pl-desc" placeholder="Описание" rows="3" style="width: 100%; padding: 12px; margin-bottom: 10px; background: #333; border: none; color: white; border-radius: 4px;"></textarea>
                <button type="submit" style="padding: 12px 24px; background: var(--accent); color: black; border: none; border-radius: 20px; font-weight: bold; cursor: pointer;">Создать</button>
            </form>
        `;
    }
};