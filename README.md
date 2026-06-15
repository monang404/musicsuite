# 🎵 Music Suite

Desktop app untuk mencari, mendownload, dan memisahkan track dari kompilasi musik dan playlist YouTube — otomatis, tanpa edit manual.

Built with Python + PySide6.

---

## Fitur

- **Cari kompilasi & playlist** langsung dari YouTube via search bar
- **Auto-detect timestamps** dari chapters, deskripsi, komentar, atau silence detection
- **Split otomatis** — satu video kompilasi dipecah jadi file per track
- **Download playlist** — setiap entry didownload sebagai file terpisah
- **Queue system** — antri beberapa job sekaligus
- **History** — riwayat hasil download tersimpan lokal

---

## Prasyarat

Sebelum install, pastikan sudah ada:

| Dependency | Versi Minimum | Cara Install |
|---|---|---|
| **Python** | 3.11+ | [python.org](https://python.org) |
| **FFmpeg** | any | Lihat di bawah |

### Install FFmpeg

**Windows**
```
winget install ffmpeg
```
atau download manual dari [ffmpeg.org/download.html](https://ffmpeg.org/download.html) dan tambahkan ke PATH.

**macOS**
```
brew install ffmpeg
```

**Linux (Debian/Ubuntu)**
```
sudo apt install ffmpeg
```

Verifikasi: `ffmpeg -version` harus berjalan tanpa error.

---

## Instalasi

```bash
# 1. Clone repo
git clone https://github.com/your-username/musicsuite.git
cd musicsuite

# 2. (Opsional) Buat virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 3. Install dependencies Python
pip install -r requirements.txt
```

---

## Menjalankan Aplikasi

```bash
python main.py
```

---

## Cara Pakai

1. Ketik nama artis atau judul album di search bar, lalu tekan Enter
2. Pilih hasil yang sesuai dari daftar
3. Klik **Inspect** untuk melihat detail tracklist
4. Klik **Download** — pilih output folder, lalu mulai
5. File hasil split tersimpan di folder yang dipilih dengan struktur:
   ```
   output/
   └── kompilasi/
       └── Nama Album/
           ├── 001 - Track One.mp3
           ├── 002 - Track Two.mp3
           └── ...
   ```

---

## Struktur Proyek

```
musicsuite/
├── main.py                  # Entry point
├── engines/
│   ├── search/              # Pencarian YouTube (yt-dlp)
│   ├── downloader/          # Download audio
│   ├── timestamp/           # Ekstraksi & parsing timestamp
│   └── splitter/            # Split audio via FFmpeg
├── services/                # Orchestration layer
├── ui/
│   ├── screens/             # Halaman-halaman app
│   ├── viewmodels/          # Business logic UI
│   ├── workers/             # QThread workers
│   ├── widgets/             # Custom widgets
│   └── themes/              # Dark theme & ThemeManager
└── tests/                   # Unit tests
```

---

## Menjalankan Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Catatan

- Hanya mendukung URL YouTube (`youtube.com` / `youtu.be`)
- Kualitas output default: MP3 320kbps
- OCR thumbnail menggunakan [OCR.space](https://ocr.space/) free tier — opsional, tidak wajib
- App menggunakan SQLite lokal untuk menyimpan history (`data/music_suite.db`)
