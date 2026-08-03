const Player = {
    audio: new Audio(),
    currentTrack: null,

    init() {
        this.audio.addEventListener('ended', () => {
            document.getElementById('play-pause-btn').textContent = '▶';
        });
    },

    play(track) {
    if (!track || !track.preview) {
        UI.showToast('Для этого трека нет доступного аудио', 'error');
        return;
    }

    this.currentTrack = track;

    // ВАЖНО: Используем наш прокси-эндпоинт вместо прямой ссылки на Jamendo
    // Это обходит CORS проблему
    const streamUrl = `${API_BASE}/catalog/stream/${track.id}`;

    this.audio.src = streamUrl;
    this.audio.play().catch(err => {
        console.error('Playback error:', err);
        UI.showToast('Не удалось воспроизвести трек', 'error');
    });

    // Обновляем UI плеера
    document.getElementById('player-title').textContent = track.title;
    document.getElementById('player-artist').textContent = track.artist;
    document.getElementById('player-cover').src = track.cover || 'https://via.placeholder.com/50?text=🎵';
    document.getElementById('play-pause-btn').textContent = '⏸';
    document.getElementById('player-bar').style.display = 'flex';

    UI.showToast(`Воспроизведение: ${track.title}`, 'info');
}

    togglePlay() {
        if (this.audio.paused) {
            this.audio.play();
            document.getElementById('play-pause-btn').textContent = '⏸';
        } else {
            this.audio.pause();
            document.getElementById('play-pause-btn').textContent = '▶';
        }
    }
};