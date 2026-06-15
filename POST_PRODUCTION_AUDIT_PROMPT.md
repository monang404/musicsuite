# Music Suite — Post-Production Audit Prompt

**Untuk:** Gemini Pro 3.1 / Claude  
**Kapan dipakai:** Setelah setiap major phase selesai, atau sebelum release  
**Output:** 4 file laporan MD di folder `docs/audit_reports/`

---

## INSTRUKSI UTAMA

Kamu adalah auditor teknis untuk proyek Music Suite V4.  
Tugas kamu: baca codebase, jalankan checks, lalu tulis laporan.  
**Jangan ubah kode apapun.** Audit saja, laporkan temuan.

Setelah audit selesai, buat folder `docs/audit_reports/` dan simpan 4 file berikut:
1. `UI_AUDIT.md`
2. `CODEBASE_AUDIT.md`  
3. `SECURITY_AUDIT.md`
4. `HEALTH_CHECK.md`

Format tiap temuan:
```
### [ID] Judul Temuan
- **Severity:** Critical / High / Medium / Low / Info
- **File:** path/to/file.py, baris N
- **Masalah:** Penjelasan singkat
- **Rekomendasi:** Apa yang harus dilakukan
```

---

## AUDIT 1 — UI_AUDIT.md

### A. Konsistensi Warna

Scan semua file di `ui/` untuk warna hardcode yang tidak melalui `ThemeManager.get_color()`:

```bash
grep -rn "setStyleSheet" ui/ --include="*.py" | grep -v __pycache__ | grep -E "#[0-9a-fA-F]{3,6}"
```

Untuk setiap temuan:
- Catat file, baris, warna hex yang dipakai
- Cek apakah warna tersebut ada di `ThemeManager.get_color()`
- Jika tidak ada ekuivalen → severity **High**
- Jika ada ekuivalen tapi tidak dipakai → severity **Medium**

**Pengecualian yang boleh diabaikan:**
- File `ui/themes/theme_manager.py` sendiri
- Komentar dan docstring
- Warna untuk `danger`, `error` state yang memang tidak ada di ThemeManager

---

### B. Konsistensi Font Size

Scan semua `font-size` yang hardcode:

```bash
grep -rn "font-size:" ui/ --include="*.py" | grep -v __pycache__
```

Dokumentasikan semua nilai yang dipakai. Apakah ada pola yang konsisten?
- Heading: berapa px?
- Body: berapa px?
- Caption/muted: berapa px?

Catat jika ada outlier (misal: 1 tempat pakai 14px sementara semua lainnya 13px).

---

### C. Widget Tanpa Minimum Size di Layar Kecil

Scan widget yang bisa overflow di resolusi rendah (1366x768):

```bash
grep -rn "setFixedWidth\|setFixedHeight\|setMinimumWidth\|setMinimumHeight" ui/ --include="*.py" | grep -v __pycache__
```

Tandai jika ada nilai > 800px width atau > 600px height → severity **Medium**.

---

### D. Signal Tanpa Slot / Slot Tanpa Signal

Scan `navigate_requested.emit` yang targetnya tidak terdaftar di `main.py`:

```bash
grep -rn 'navigate_requested.emit' ui/ --include="*.py" | grep -v __pycache__
grep -rn 'register_screen' main.py
```

Bandingkan route yang di-emit vs yang terdaftar. Jika ada yang tidak cocok → severity **Critical**.

---

### E. Cursor Missing

Scan tombol yang tidak punya `setCursor(Qt.PointingHandCursor)`:

```bash
grep -rn "QPushButton\|setStyleSheet" ui/screens/ --include="*.py" -l | xargs grep -L "PointingHandCursor" 2>/dev/null
```

File yang punya QPushButton tapi tidak punya PointingHandCursor sama sekali → severity **Low**.

---

### F. Screen Tanpa `on_navigated`

Semua screen yang terdaftar di router harus punya `on_navigated`:

```bash
grep -rn "def on_navigated" ui/screens/ --include="*.py"
grep -rn "register_screen" main.py
```

Jika ada screen yang terdaftar tapi tidak punya `on_navigated` → severity **Medium**.

---

## AUDIT 2 — CODEBASE_AUDIT.md

### A. Dead Code

```bash
# Fungsi/method yang didefinisikan tapi tidak pernah dipanggil
grep -rn "^    def \|^def " ui/ services/ engines/ --include="*.py" | grep -v __pycache__ | grep -v test_
```

Untuk setiap method, cek apakah namanya muncul di file lain:
- Method yang hanya ada 1 kali (definisi saja, tidak dipanggil) → catat sebagai kandidat dead code
- Fokus pada `ui/` dan `services/`, engines boleh skip

---

### B. Import Tidak Dipakai

```bash
grep -rn "^import \|^from " ui/ services/ --include="*.py" | grep -v __pycache__
```

Cek setiap import: apakah nama module/class yang diimport benar-benar dipakai di file tersebut.
Import tidak terpakai → severity **Low** (tapi bisa menyebabkan circular import).

---

### C. Duplikasi Logika

Scan fungsi dengan nama mirip di file berbeda:

```bash
grep -rn "def validate\|def parse\|def format\|def build" ui/ services/ engines/ --include="*.py" | grep -v __pycache__ | grep -v test_
```

Jika ada 2+ fungsi dengan nama dan parameter mirip di file berbeda → severity **Medium** (kandidat untuk dipindah ke utils).

---

### D. Exception Handling Kosong

```bash
grep -rn "except.*:" ui/ services/ engines/ --include="*.py" | grep -v __pycache__ | grep -A1 "except" | grep -E "pass$|\.\.\.$ "
```

`except: pass` tanpa logging → severity **High** (error hilang tanpa jejak).
`except Exception as e: pass` → severity **Medium**.

---

### E. Thread Safety

```bash
grep -rn "ServiceContainer\(\)\." ui/ --include="*.py" | grep -v __pycache__
```

ServiceContainer adalah singleton. Cek apakah ada akses ke service dari dalam `QThread.run()` atau worker thread tanpa lock. Jika ada direct DB access dari worker → severity **Critical**.

```bash
grep -rn "result_store\|sqlite\|\.db" ui/workers/ ui/viewmodels/ --include="*.py" | grep -v __pycache__
```

---

### F. File Terlalu Besar

```bash
wc -l ui/screens/*.py ui/viewmodels/*.py ui/workers/*.py services/*.py | sort -rn | head -15
```

File > 400 baris → catat sebagai kandidat untuk dipecah (bukan bug, tapi technical debt).

---

### G. TODO / FIXME / HACK yang Tertinggal

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|TEMP\|WORKAROUND" ui/ services/ engines/ --include="*.py" | grep -v __pycache__ | grep -v test_
```

Catat semua. Severity tergantung konteks.

---

## AUDIT 3 — SECURITY_AUDIT.md

### A. URL Validation Coverage

```bash
grep -rn "http\|url\|URL" ui/ services/ --include="*.py" | grep -v __pycache__ | grep -v "validate_url\|#\|comment\|ThemeManager"
```

Setiap tempat yang menerima URL dari user, pastikan `validate_url()` dari `services/security.py` dipanggil sebelum digunakan. Jika tidak → severity **Critical**.

---

### B. Subprocess Safety

```bash
grep -rn "subprocess\|Popen\|os.system\|os.popen\|shell=True" --include="*.py" ui/ services/ engines/ | grep -v __pycache__ | grep -v base_worker
```

- `shell=True` dengan input dari user → severity **Critical**
- `shell=True` dengan string literal saja → severity **Medium**
- Subprocess tanpa timeout → severity **Low**

Pengecualian: `ui/workers/base_worker.py` sudah punya custom Popen hook, ini expected.

---

### C. Path Traversal

```bash
grep -rn "open(\|Path(\|os.path\|output_dir\|output_folder\|save_path" services/ ui/ --include="*.py" | grep -v __pycache__ | grep -v "ThemeManager\|\.qss\|assets"
```

Cek setiap path yang konstruksinya menggunakan input user (output folder dari config dialog).  
Pastikan ada sanitasi atau `Path().resolve()` sebelum dipakai. Jika tidak → severity **High**.

---

### D. SQL Injection (ResultStore)

```bash
cat services/result_store.py
```

Baca seluruh `result_store.py`. Pastikan semua query menggunakan parameterized query (`?` placeholder), bukan f-string atau concatenation. Jika ada query dengan f-string yang menyisipkan user input → severity **Critical**.

---

### E. Sensitive Data di Log

```bash
grep -rn "print(\|logging\.\|logger\." ui/ services/ --include="*.py" | grep -v __pycache__ | grep -iE "password|token|key|secret|auth"
```

Jika ada credential yang di-log → severity **Critical**.

---

### F. Error Message Exposure

```bash
grep -rn "failed.emit\|error_label\|show_error\|setText.*error\|setText.*Error" ui/ --include="*.py" | grep -v __pycache__
```

Cek apakah error message yang ditampilkan ke user mengekspos internal path, stack trace, atau info teknis sensitif. Jika ya → severity **Medium**.

---

## AUDIT 4 — HEALTH_CHECK.md

### A. Dependency Check

```bash
python -c "import PySide6; print('PySide6 OK')"
python -c "import yt_dlp; print('yt-dlp OK')"
python -c "import sqlite3; print('sqlite3 OK')"
ffmpeg -version 2>&1 | head -1
yt-dlp --version
```

Catat versi masing-masing. Jika ada yang gagal → severity **Critical**.

---

### B. App Startup Test

```bash
python -c "
from ui.core.service_container import ServiceContainer
sc = ServiceContainer()
print('ServiceContainer OK')
print('Dependencies:', sc.dependency_service.get_dependency_status())
print('ResultStore OK' if sc.result_store else 'ResultStore FAIL')
"
```

Jika ada ImportError atau exception → severity **Critical** dengan full traceback.

---

### C. Test Suite

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

Catat:
- Total tests
- Passed / Failed / Error / Skipped
- Jika ada failure: file, test name, error message lengkap

Expected: semua passed. Jika ada failure → severity sesuai impact.

---

### D. Database Integrity

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/music_suite.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
print('DB Integrity:', cursor.fetchone())
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
print('Tables:', [r[0] for r in cursor.fetchall()])
conn.close()
"
```

Jika integrity_check bukan `('ok',)` → severity **Critical**.

---

### E. Stale File Check

Cek apakah masih ada file debug/scratch yang seharusnya sudah dihapus:

```bash
find . -name "scratch_test*.py" -o -name "debug_*.py" -o -name "*.part" 2>/dev/null | grep -v node_modules | grep -v .git
```

Jika ada → severity **Low** (cleanup recommended).

---

### F. File Size Anomali

```bash
find . -name "*.md" -size +500k | grep -v .git
find . -name "*.py" -size +100k | grep -v .git
find data/ -name "*.db" 2>/dev/null | xargs ls -lh 2>/dev/null
```

File MD > 500KB atau Python > 100KB biasanya anomali (mungkin generated content atau data yang tidak sengaja dicommit).

---

## FORMAT OUTPUT

Setelah semua audit selesai, buat 4 file di `docs/audit_reports/`:

### Template Header Tiap File:

```markdown
# [Nama] Audit Report
**Tanggal:** [tanggal hari ini]
**Auditor:** Gemini Pro 3.1
**Proyek:** Music Suite V4
**Total Temuan:** X (Critical: N, High: N, Medium: N, Low: N, Info: N)

---

## Ringkasan Eksekutif
[2-3 kalimat kondisi keseluruhan]

## Temuan

### [C-001] Judul — Critical
...

### [H-001] Judul — High
...

## Tidak Ditemukan Masalah Pada
- Item yang sudah dicek dan hasilnya bersih

## Rekomendasi Prioritas
1. Fix Critical dulu
2. dst.
```

### Prefix ID:
- `C-XXX` = Critical
- `H-XXX` = High  
- `M-XXX` = Medium
- `L-XXX` = Low
- `I-XXX` = Info

---

## PERINGATAN

- Jangan fix apapun saat audit. Tulis laporan dulu, tunggu approval.
- Jika menemukan Critical security issue, tandai dengan `🚨` di awal baris.
- Jika tidak menemukan masalah di satu section, tulis "✅ Tidak ditemukan masalah."
- Setelah 4 file selesai ditulis, tampilkan ringkasan tabel:

```
| Kategori  | Critical | High | Medium | Low | Info |
|-----------|----------|------|--------|-----|------|
| UI        |    0     |  X   |   X    |  X  |  X   |
| Codebase  |    0     |  X   |   X    |  X  |  X   |
| Security  |    0     |  X   |   X    |  X  |  X   |
| Health    |    0     |  X   |   X    |  X  |  X   |
| **TOTAL** |    0     |  X   |   X    |  X  |  X   |
```
