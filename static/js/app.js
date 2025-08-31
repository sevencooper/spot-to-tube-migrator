document.addEventListener('DOMContentLoaded', () => {
    const spotifySection = document.getElementById('spotify-section');
    const playlistLoader = document.getElementById('playlist-loader');
    const playlistListDiv = document.getElementById('playlist-list');

    const ytStatus = document.getElementById('yt-status');
    const ytHeadersTextarea = document.getElementById('yt-headers');
    const verifyYtBtn = document.getElementById('verify-yt-btn');
    const ytMessage = document.getElementById('yt-message');

    const startMigrationBtn = document.getElementById('start-migration-btn');

    const resultsSection = document.getElementById('results-section');
    const migrationLoader = document.getElementById('migration-loader');
    const summaryReportDiv = document.getElementById('summary-report');
    const migrationLogPre = document.getElementById('migration-log');

    let isSpotifyConnected = false;
    let isYouTubeConnected = false;

    // --- State Management ---
    function updateUIState() {
        const selectedPlaylists = document.querySelectorAll('#playlist-list input[type="checkbox"]:checked');
        if (isSpotifyConnected && isYouTubeConnected && selectedPlaylists.length > 0) {
            startMigrationBtn.disabled = false;
        } else {
            startMigrationBtn.disabled = true;
        }
    }

    // --- Spotify Logic ---
    if (spotifySection.querySelector('.status-success')) {
        isSpotifyConnected = true;
        fetchSpotifyPlaylists();
    }

    async function fetchSpotifyPlaylists() {
        playlistLoader.classList.remove('hidden');
        playlistListDiv.innerHTML = '';
        try {
            const response = await fetch('/api/spotify-playlists');
            if (!response.ok) {
                throw new Error(`Error fetching playlists: ${response.statusText}`);
            }
            const playlists = await response.json();

            if (playlists.length === 0) {
                playlistListDiv.innerHTML = '<p>No playlists found.</p>';
            } else {
                playlists.forEach(p => {
                    const item = document.createElement('div');
                    item.className = 'playlist-item';
                    item.innerHTML = `
                        <label>
                            <input type="checkbox" value="${p.id}">
                            ${p.name} <span>(${p.track_count} songs)</span>
                        </label>
                    `;
                    playlistListDiv.appendChild(item);
                });
                playlistListDiv.addEventListener('change', updateUIState);
            }
        } catch (error) {
            playlistListDiv.innerHTML = `<p class="status-error">Could not load playlists. Please try refreshing.</p>`;
            console.error(error);
        } finally {
            playlistLoader.classList.add('hidden');
        }
    }

    // --- YouTube Music Logic ---
    verifyYtBtn.addEventListener('click', async () => {
        const headers_raw = ytHeadersTextarea.value.trim();
        if (!headers_raw) {
            ytMessage.textContent = 'Headers cannot be empty.';
            ytMessage.className = 'message status-error';
            return;
        }

        ytMessage.textContent = 'Verifying...';
        ytMessage.className = 'message';

        try {
            const response = await fetch('/api/verify-youtube', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ headers_raw })
            });
            const result = await response.json();

            if (response.ok && result.success) {
                isYouTubeConnected = true;
                ytStatus.textContent = '✅ Connected';
                ytStatus.className = 'status-success';
                ytMessage.textContent = result.message;
                ytMessage.className = 'message status-success';
            } else {
                throw new Error(result.error || 'Verification failed.');
            }
        } catch (error) {
            isYouTubeConnected = false;
            ytStatus.textContent = '❌ Not Connected';
            ytStatus.className = 'status-error';
            ytMessage.textContent = `Error: ${error.message}`;
            ytMessage.className = 'message status-error';
        } finally {
            updateUIState();
        }
    });

    // --- Migration Logic ---
    startMigrationBtn.addEventListener('click', async () => {
        const selectedPlaylists = document.querySelectorAll('#playlist-list input:checked');
        const playlist_ids = Array.from(selectedPlaylists).map(cb => cb.value);

        if (playlist_ids.length === 0) {
            alert('Please select at least one playlist to migrate.');
            return;
        }

        startMigrationBtn.disabled = true;
        startMigrationBtn.textContent = 'Migrating...';
        resultsSection.classList.remove('hidden');
        migrationLoader.classList.remove('hidden');
        migrationLogPre.textContent = 'Starting migration process...';
        summaryReportDiv.innerHTML = '';

        try {
            const response = await fetch('/api/migrate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ playlist_ids })
            });
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'An unknown error occurred during migration.');
            }

            migrationLogPre.textContent = result.log;
            displaySummary(result.summary);

        } catch (error) {
            migrationLogPre.textContent += `\n\n--- MIGRATION FAILED ---\n${error.message}`;
        } finally {
            startMigrationBtn.disabled = false;
            startMigrationBtn.textContent = 'Start Migration';
            migrationLoader.classList.add('hidden');
            window.scrollTo(0, document.body.scrollHeight);
        }
    });

    function displaySummary(summary) {
        let summaryHTML = `
            <h3>Migration Summary</h3>
            <p><strong>Total Songs Transferred:</strong> ${summary.success}</p>
            <p><strong>Total Songs Not Found:</strong> ${summary.failed}</p>
            <hr>
        `;

        summary.playlists.forEach(p => {
            summaryHTML += `
                <h4>Playlist: ${p.name}</h4>
                <p>${p.found} / ${p.total} songs migrated successfully.</p>
            `;
            if (p.not_found.length > 0) {
                summaryHTML += `<p><strong>Could not find:</strong></p><ul>`;
                p.not_found.forEach(track => {
                    summaryHTML += `<li>${track}</li>`;
                });
                summaryHTML += `</ul>`;
            }
        });
        summaryReportDiv.innerHTML = summaryHTML;
    }

    // Initial check
    updateUIState();
});