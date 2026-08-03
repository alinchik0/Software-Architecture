//const Player = {
//    audio: new Audio(),
//    currentTrack: null,
//
//    init() {
//        this.audio.addEventListener('ended', () => {
//            document.getElementById('play-pause-btn').textContent = '▶';
//        });
//    },
//
//    play(track) {
//    if (!track || !track.id) {
//        UI.showToast('Некорректный трек', 'error');
//        return;
//    }
//
//    this.currentTrack = track;
//
//    // ВАЖНО: Используем ТОЛЬКО наш прокси-эндпоинт, а НЕ track.preview!
//    // track.preview содержит прямую ссылку на Jamendo, которую браузер заблокирует
//    const streamUrl = `${API_BASE}/catalog/stream/${track.id}`;
//
//    console.log('Playing track:', track.title, 'via URL:', streamUrl);
//
//    this.audio.src = streamUrl;
//    this.audio.load(); // Принудительно загружаем новый источник
//
//    const playPromise = this.audio.play();
//
//    if (playPromise !== undefined) {
//        playPromise.then(() => {
//            console.log('Playback started successfully');
//            document.getElementById('player-title').textContent = track.title;
//            document.getElementById('player-artist').textContent = track.artist;
//            document.getElementById('player-cover').src = track.cover || 'https://via.placeholder.com/50?text=🎵';
//            document.getElementById('play-pause-btn').textContent = '⏸';
//            document.getElementById('player-bar').style.display = 'flex';
//            UI.showToast(`Играет: ${track.title}`, 'success');
//        }).catch(error => {
//            console.error("Audio play failed:", error);
//            UI.showToast('Ошибка воспроизведения: ' + error.message, 'error');
//        });
//    }
//}
//
//    togglePlay() {
//        if (this.audio.paused) {
//            this.audio.play();
//            document.getElementById('play-pause-btn').textContent = '⏸';
//        } else {
//            this.audio.pause();
//            document.getElementById('play-pause-btn').textContent = '▶';
//        }
//    }
//};

const Player = {
    audio: new Audio(),
    queue: [],
    currentIndex: -1,
    isShuffle: false,
    repeatMode: 'none', // 'none', 'one', 'all'

    init() {
        // События аудио
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('ended', () => this.handleTrackEnd());

        // События контролов
        document.getElementById('progress-bar').addEventListener('input', (e) => this.seek(e.target.value));
        document.getElementById('volume-slider').addEventListener('input', (e) => this.setVolume(e.target.value));

        // Начальная громкость
        this.audio.volume = 0.8;
    },

    // Добавить трек в очередь и начать воспроизведение
    playTrack(track) {
        if (!track || !track.id) {
            UI.showToast('Некорректный трек', 'error');
            return;
        }

        // Если трек уже в очереди, просто переключаемся на него
        const existingIndex = this.queue.findIndex(t => t.id === track.id);
        if (existingIndex !== -1) {
            this.currentIndex = existingIndex;
        } else {
            this.queue.push(track);
            this.currentIndex = this.queue.length - 1;
        }

        this.loadAndPlay(this.queue[this.currentIndex]);
    },

    // Установить очередь целиком (например, из результатов поиска)
    setQueue(tracks, startIndex = 0) {
        this.queue = tracks;
        this.currentIndex = startIndex;
        if (this.queue.length > 0) {
            this.loadAndPlay(this.queue[this.currentIndex]);
        }
    },

    loadAndPlay(track) {
        const streamUrl = `${API_BASE}/catalog/stream/${track.id}`;
        console.log('Loading track:', track.title, 'via:', streamUrl);

        this.audio.src = streamUrl;
        this.audio.load();

        const playPromise = this.audio.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                this.updatePlayerUI(track);
                UI.showToast(`Играет: ${track.title}`, 'info');
            }).catch(error => {
                console.error("Playback failed:", error);
                UI.showToast('Ошибка воспроизведения', 'error');
            });
        }
    },

    togglePlay() {
        if (this.audio.paused) {
            this.audio.play();
            document.getElementById('play-pause-btn').textContent = '⏸';
        } else {
            this.audio.pause();
            document.getElementById('play-pause-btn').textContent = '▶';
        }
    },

    playNext() {
        if (this.queue.length === 0) return;

        if (this.isShuffle) {
            this.currentIndex = Math.floor(Math.random() * this.queue.length);
        } else {
            this.currentIndex = (this.currentIndex + 1) % this.queue.length;
        }
        this.loadAndPlay(this.queue[this.currentIndex]);
    },

    playPrev() {
        if (this.queue.length === 0) return;

        // Если трек играет более 3 секунд, начинаем его сначала
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            return;
        }

        this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
        this.loadAndPlay(this.queue[this.currentIndex]);
    },

    handleTrackEnd() {
        if (this.repeatMode === 'one') {
            this.audio.currentTime = 0;
            this.audio.play();
        } else if (this.repeatMode === 'all' || this.currentIndex < this.queue.length - 1) {
            this.playNext();
        } else {
            document.getElementById('play-pause-btn').textContent = '▶';
        }
    },

    toggleShuffle() {
        this.isShuffle = !this.isShuffle;
        document.getElementById('shuffle-btn').classList.toggle('active', this.isShuffle);
        UI.showToast(this.isShuffle ? 'Перемешивание включено' : 'Перемешивание выключено', 'info');
    },

    toggleRepeat() {
        if (this.repeatMode === 'none') {
            this.repeatMode = 'all';
            document.getElementById('repeat-btn').textContent = '🔁';
            document.getElementById('repeat-btn').classList.add('active');
            UI.showToast('Повтор плейлиста', 'info');
        } else if (this.repeatMode === 'all') {
            this.repeatMode = 'one';
            document.getElementById('repeat-btn').textContent = '🔂';
            UI.showToast('Повтор трека', 'info');
        } else {
            this.repeatMode = 'none';
            document.getElementById('repeat-btn').textContent = '🔁';
            document.getElementById('repeat-btn').classList.remove('active');
            UI.showToast('Повтор выключен', 'info');
        }
    },

    updateProgress() {
        if (!this.audio.duration) return;
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        document.getElementById('progress-bar').value = percent;
        document.getElementById('current-time').textContent = this.formatTime(this.audio.currentTime);
    },

    updateDuration() {
        document.getElementById('duration').textContent = this.formatTime(this.audio.duration);
    },

    seek(percent) {
        if (!this.audio.duration) return;
        const time = (percent / 100) * this.audio.duration;
        this.audio.currentTime = time;
    },

    setVolume(value) {
        this.audio.volume = value;
    },

    updatePlayerUI(track) {
        document.getElementById('player-title').textContent = track.title;
        document.getElementById('player-artist').textContent = track.artist;
        document.getElementById('player-cover').src = track.cover || 'https://via.placeholder.com/56?text=🎵';
        document.getElementById('play-pause-btn').textContent = '⏸';
        document.getElementById('player-bar').style.display = 'flex';

        // Сброс прогресса
        document.getElementById('progress-bar').value = 0;
        document.getElementById('current-time').textContent = '0:00';
    },

    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
};