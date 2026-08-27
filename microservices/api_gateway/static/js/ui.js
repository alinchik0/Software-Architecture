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

//        renderSearchResults(tracks) {
//        const content = document.getElementById('app-content');
//        if (!tracks || tracks.length === 0) {
//            content.innerHTML = '<h2>Поиск</h2><p>Ничего не найдено.</p>';
//            return;
//        }
//
//        let html = '<h2>Результаты поиска</h2><div class="grid-container">';
//        tracks.forEach((track, index) => {
//            // При клике устанавливаем весь список треков как очередь и начинаем с выбранного
//            html += `
//                <div class="track-card" onclick='App.playFromSearch(${index})'>
//                    <div class="card-cover">
//                        ${track.cover ? `<img src="${track.cover}" alt="cover">` : '🎵'}
//                    </div>
//                    <div class="card-title">${track.title}</div>
//                    <div class="card-desc">${track.artist}</div>
//                </div>
//            `;
//        });
//        html += '</div>';
//        content.innerHTML = html;

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
