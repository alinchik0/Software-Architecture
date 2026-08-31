const UI = {
    showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('toast-container not found!');
        return;
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
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

        renderPlaylistDetail(playlist, isOwner) {
        const content = document.getElementById('app-content');

        // Формируем список треков
        const tracksHtml = (playlist.tracks && playlist.tracks.length > 0)
            ? playlist.tracks.map((track, index) => `
                <div class="track-card" style="display: flex; align-items: center; gap: 15px; padding: 12px; background: #2a2a2a; margin-bottom: 10px; border-radius: 8px;">
                    <div style="width: 30px; text-align: center; color: #888; font-weight: bold;">${index + 1}</div>
                    <img src="${track.cover || 'https://via.placeholder.com/50'}" alt="cover" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; background: #444;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${track.title || 'Неизвестно'}</div>
                        <div style="color: #aaa; font-size: 0.9em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${track.artist || 'Неизвестный исполнитель'}</div>
                    </div>
                    <!-- Кнопка удаления трека из плейлиста будет добавлена на Этапе 3 -->
                </div>
            `).join('')
            : '<p style="color: #888; margin-top: 20px;">В этом плейлисте пока нет треков. Найдите музыку и добавьте её сюда!</p>';

        // Кнопка удаления отображается только для владельца
        const deleteButton = isOwner
            ? `<button onclick="App.deletePlaylist(${playlist.playlist_id})" style="background: #ff4444; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-weight: bold;">Удалить плейлист</button>`
            : '';

        // Рендерим всю страницу
        content.innerHTML = `
            <div style="padding: 20px; max-width: 800px; margin: 0 auto;">
                <button onclick="App.navigate('library')" style="background: none; border: none; color: var(--accent, #1db954); cursor: pointer; margin-bottom: 20px; font-size: 1em; display: flex; align-items: center; gap: 5px;">
                    ← Назад к медиатеке
                </button>

                <h1 style="margin-bottom: 10px; font-size: 2.5em;">${playlist.title}</h1>
                <p style="color: #aaa; margin-bottom: 30px; font-size: 1.1em;">${playlist.description || 'Без описания'}</p>

                <div style="display: flex; gap: 15px; margin-bottom: 40px;">
                    <!-- Кнопка "Воспроизвести всё" будет добавлена на Этапе 3 -->
                    ${deleteButton}
                </div>

                <h3 style="margin-bottom: 15px; color: #fff;">Треки (${playlist.tracks ? playlist.tracks.length : 0})</h3>
                <div id="playlist-tracks-container">
                    ${tracksHtml}
                </div>
            </div>
        `;
    },

        renderSearchResults(tracks, isPopular = false) {
        const container = document.getElementById('search-results-container');
        if (!container) {
            console.error('search-results-container not found!');
            return;
        }

        if (!tracks || tracks.length === 0) {
            container.innerHTML = '<p>Ничего не найдено.</p>';
            return;
        }

        const title = isPopular ? '<h3 style="margin-bottom: 15px;">Популярные треки</h3>' : '';

        let html = title;
        tracks.forEach((track, index) => {
            html += `
                <div class="track-card" onclick='App.playFromSearch(${index})' style="display: flex; align-items: center; gap: 15px; padding: 12px; background: #2a2a2a; margin-bottom: 10px; border-radius: 8px; cursor: pointer;">
                    <div class="card-cover" style="width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #444; border-radius: 4px;">
                        ${track.cover ? `<img src="${track.cover}" alt="cover" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;">` : '🎵'}
                    </div>
                    <div style="flex: 1;">
                        <div class="card-title" style="font-weight: bold;">${track.title}</div>
                        <div class="card-desc" style="color: #aaa; font-size: 0.9em;">${track.artist}</div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    },
//        // Сохраняем текущие результаты в глобальную переменную для плеера
//        this.currentSearchResults = tracks;

    renderCreatePlaylist() {
        document.getElementById('app-content').innerHTML = `
            <h2>Создать новый плейлист</h2>
            <form id="create-pl-form" class="form-box" style="max-width: 500px; margin-top: 20px;">
                <input type="text" id="pl-title" placeholder="Название" required style="width: 100%; padding: 12px; margin-bottom: 10px; background: #333; border: none; color: white; border-radius: 4px;">
                <textarea id="pl-desc" placeholder="Описание" rows="3" style="width: 100%; padding: 12px; margin-bottom: 10px; background: #333; border: none; color: white; border-radius: 4px;"></textarea>
                <button type="submit" style="padding: 12px 24px; background: var(--accent); color: black; border: none; border-radius: 20px; font-weight: bold; cursor: pointer;">Создать</button>
            </form>
        `;
    },

    playFromSearch(index) {
        if (!this.currentSearchResults || !this.currentSearchResults[index]) return;

        // Передаём весь массив треков и индекс выбранного в плеер
        Player.setQueue(this.currentSearchResults, index);
    },
};
