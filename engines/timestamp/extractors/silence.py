from engines.timestamp.utils import AutoTimestampError


def extract_silence_timestamps(audio_path: str, min_silence_db: float = -40.0,
                  min_silence_sec: float = 0.8,
                  min_song_sec: float = 60.0,
                  titles: list[str] | None = None,
                  cancel_check=None) -> list[dict] | None:
    """
    Detect song boundaries by finding silent gaps in audio.
    Requires 'librosa' to be installed.

    Args:
        audio_path:      Path to downloaded MP3/audio file
        min_silence_db:  RMS threshold in dBFS below which = silence
        min_silence_sec: Minimum duration of silence to count as a gap
        min_song_sec:    Minimum song length (ignore very short splits)
        titles:          Optional list of extracted song titles to map to boundaries
        cancel_check:    Optional callback returning True if operation should cancel

    Returns:
        List of {"seconds": int, "title": str} or None if not enough found.
    """
    try:
        import librosa
    except ImportError:
        return None

    try:
        if cancel_check and cancel_check():
            return None
            
        # Load at reduced sample rate for speed (mono)
        y, sr = librosa.load(audio_path, sr=22050, mono=True)

        if cancel_check and cancel_check():
            return None

        # Compute RMS energy per frame (~23ms each)
        frame_length = 512
        hop_length = 256
        rms = librosa.feature.rms(y=y, frame_length=frame_length,
                                   hop_length=hop_length)[0]

        frames_per_sec = sr / hop_length
        target_count = len(titles) if titles else None

        # Helper internal function to find boundaries for a given set of parameters
        def _get_bounds(db: float, sec: float, min_song: float) -> list[int]:
            threshold = librosa.db_to_amplitude(db)
            silent = rms < threshold
            min_silent_frames = int(sec * frames_per_sec)

            bounds = [0]  # always start at 0
            i = 0
            while i < len(silent):
                if silent[i]:
                    j = i
                    while j < len(silent) and silent[j]:
                        j += 1
                    gap_len = j - i
                    if gap_len >= min_silent_frames:
                        # Midpoint of silence = boundary
                        mid = (i + j) // 2
                        mid_sec = int(mid / frames_per_sec)
                        # Only add if far enough from last boundary
                        if mid_sec - bounds[-1] >= min_song:
                            bounds.append(mid_sec)
                    i = j
                else:
                    i += 1
            return bounds

        boundaries = None

        if target_count and target_count >= 2:
            print(f"[SILENCE] Memulai grid search untuk target {target_count} lagu. Judul yang terdeteksi: {titles}")

            # Expanded grid search parameter spaces (mencakup 0.7, 0.6, 0.3, hingga 0.1 detik)
            db_choices = [-40.0, -35.0, -30.0, -45.0, -50.0, -25.0, -55.0, -20.0, -60.0]
            sec_choices = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 1.0, 1.2, 1.5, 2.0]
            song_sec_choices = [min_song_sec, max(15.0, min_song_sec * 0.6), max(10.0, min_song_sec * 0.3), 5.0]

            best_boundaries = None
            best_diff = float("inf")
            found_exact = False
            best_params = None

            for song_sec in song_sec_choices:
                if cancel_check and cancel_check():
                    return None
                for db in db_choices:
                    if cancel_check and cancel_check():
                        return None
                    for sec in sec_choices:
                        bounds = _get_bounds(db, sec, song_sec)
                        diff = abs(len(bounds) - target_count)
                        if diff < best_diff:
                            best_diff = diff
                            best_boundaries = bounds
                            best_params = (db, sec, song_sec)
                        if diff == 0:
                            print(f"[SILENCE] Kombinasi EXACT ditemukan! db={db}, sec={sec}, min_song={song_sec} -> len={len(bounds)}")
                            found_exact = True
                            break
                    if found_exact:
                        break
                if found_exact:
                    break

            boundaries = best_boundaries
            print(f"[SILENCE] Selesai grid search. Best params: db={best_params[0] if best_params else 'N/A'}, sec={best_params[1] if best_params else 'N/A'}, min_song={best_params[2] if best_params else 'N/A'} -> len={len(boundaries) if boundaries else 0} (selisih: {best_diff})")

            # Strict mode: Jika tidak pas 100%, jangan selesaikan tugas! Lempar error.
            if not found_exact:
                raise AutoTimestampError(
                    f"Gagal mendeteksi jumlah track yang sesuai.\n\n"
                    f"Target dari deskripsi/thumbnail: {target_count} lagu,\n"
                    f"tetapi deteksi hening paling optimal hanya menemukan {len(boundaries) if boundaries else 0} jeda lagu.\n\n"
                    f"Silakan gunakan AI Prompt untuk menyalin timestamp secara manual."
                )
        else:
            print("[SILENCE] Menjalankan deteksi hening default (tanpa target_count).")
            # Single pass with defaults
            boundaries = _get_bounds(min_silence_db, min_silence_sec, min_song_sec)
            print(f"[SILENCE] Default run selesai. Ditemukan {len(boundaries) if boundaries else 0} batas hening.")

        if not boundaries or len(boundaries) < 2:
            return None

        entries = []
        for idx, sec in enumerate(boundaries):
            if titles and idx < len(titles):
                title = titles[idx]
            else:
                title = f"Track {idx + 1}"
            entries.append({
                "seconds": sec,
                "title": title,
            })

        return entries

    except AutoTimestampError:
        raise
    except Exception:
        return None
