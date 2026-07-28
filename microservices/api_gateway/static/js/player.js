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
            UI.showToast('Для этого трека нет доступного превью', 'error');
            return;
        }
        this.currentTrack = track;
        this.audio.src = track.preview;
        this.audio.play();

        // Обновляем UI плеера
        document.getElementById('player-title').textContent = track.title;
        document.getElementById('player-artist').textContent = track.artist;
        document.getElementById('player-cover').src = track.cover || 'https://via.placeholder.com/50?text=🎵';
        document.getElementById('play-pause-btn').textContent = '⏸';
        document.getElementById('player-bar').style.display = 'flex';
    },

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