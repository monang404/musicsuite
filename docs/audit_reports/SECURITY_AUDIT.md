# Security Audit Report
**Tanggal:** 2026-06-15
**Auditor:** Gemini Pro 3.1
**Proyek:** Music Suite V4
**Total Temuan:** 3 (Critical: 1, High: 1, Medium: 1, Low: 0, Info: 0)

---

## Ringkasan Eksekutif
Secara keseluruhan, aplikasi memiliki sistem pertahanan yang baik terhadap injeksi SQL (penggunaan query parameter yang ketat) dan serangan input URL (karena `validate_url` diterapkan secara masif pada seluruh flow). Namun ditemukan isu kebocoran API Key yang dicetak langsung ke log/konsol, potensi Path Traversal pada penentuan folder output, dan raw exception string yang ditampilkan ke antarmuka pengguna.

## Temuan

### 🚨 [C-001] Sensitive Data Exposure: API Key di Log Output
- **Severity:** Critical
- **File:** `engines/timestamp/extractors/ocr.py`, baris 14
- **Masalah:** Baris kode memanggil fungsi `print(f"[OCR] Menggunakan API Key: {api_key}")`. Ini berarti kunci API (secret) dicetak langsung ke standard output / terminal, sehingga bisa terbaca oleh proses eksternal atau tersimpan di log sistem tanpa enkripsi.
- **Rekomendasi:** Hapus baris print tersebut atau sensor (masking) lognya menjadi `API Key: *****`.

### [H-001] Potensi Path Traversal pada Output Directory
- **Severity:** High
- **File:** `services/workflow_service.py` (baris 21, 60, dll) dan `services/downloader_service.py`
- **Masalah:** Fungsi menerima argumen `output_dir` (berupa Path) dari input konfigurasi user tanpa validasi. Meskipun OS biasanya akan menangani invalid characters, path yang memuat input relatif nyasar (contoh: `../../Windows/System32`) berpotensi mengganggu stabilitas sistem atau menimpa direktori yang tidak diharapkan jika dieksekusi oleh subprocess eksternal (seperti FFmpeg atau yt-dlp).
- **Rekomendasi:** Tambahkan pemanggilan `Path(output_dir).resolve()` sebelum mengeksekusi subprocess, dan pastikan root path berada dalam wilayah yang aman (bukan `C:\Windows` atau `/`).

### [M-001] Error Message Exposure (Raw Exception)
- **Severity:** Medium
- **File:** `ui/workers/base_worker.py` (baris 125), `ui/workers/playlist_inspector_worker.py` (baris 70)
- **Masalah:** Pekerja worker menangkap Exception generik dan meneruskan pesan kesalahannya secara harfiah dengan `self.failed.emit(str(e))`. Pesan ini kemudian ditangkap oleh UI (seperti `self.error_label.setText(err)`). `str(e)` berisiko mengekspos full path sistem atau konfigurasi internal yang sensitif jika library pihak ketiga mengembalikan string panjang.
- **Rekomendasi:** Gunakan pesan error yang lebih user-friendly (contoh: "Terjadi kesalahan sistem saat memproses berkas"), dan cukup lakukan log internal untuk `str(e)`.

## Tidak Ditemukan Masalah Pada
- **SQL Injection:** Modul `ResultStore` (`services/result_store.py`) sepenuhnya mematuhi standar parameterisasi `(?, ?)` sqlite3. Tidak ada query f-string rawan injeksi SQL.
- **URL Validation:** `validate_url()` secara disiplin dipanggil pada class service sebelum URL diteruskan ke layer backend (contohnya di `search_worker.py`, `downloader_service.py`, dan `search_service.py`).
- **Subprocess Safety:** Tidak ditemukan penggunaan `shell=True` di seluruh codebase, yang memitigasi eksekusi command line injection arbitrary.

## Rekomendasi Prioritas
1. Hapus cetakan API key di module OCR segera (C-001).
2. Terapkan Path resolution and sanitization (H-001).
3. Bungkus `str(e)` pada UI worker emit dengan fallback message generik (M-001).
