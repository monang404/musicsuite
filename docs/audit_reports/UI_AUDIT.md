# UI Audit Report
**Tanggal:** 2026-06-15
**Auditor:** Gemini Pro 3.1
**Proyek:** Music Suite V4
**Total Temuan:** 5 (Critical: 0, High: 1, Medium: 3, Low: 1, Info: 0)

---

## Ringkasan Eksekutif
Secara keseluruhan, UI sudah menggunakan ThemeManager untuk styling, namun masih terdapat beberapa warna hex yang di-hardcode di file tertentu, ukuran font yang sangat bervariasi tanpa hierarki baku, dan satu screen (HomeScreen) yang tidak mengimplementasikan metode `on_navigated`. Tidak ada isu major terkait responsive design, dan routing antar screen aman dari signal nyasar.

## Temuan

### [M-001] Warna Hardcode yang Memiliki Ekuivalen di ThemeManager
- **Severity:** Medium
- **File:** `ui/widgets/source_card.py` (baris 34, 39, 42, 49, 57, 59), `ui/screens/results_center_screen.py` (baris 343), `ui/screens/process_screen.py` (baris 116), `ui/screens/home_screen.py` (baris 81), `ui/main_window.py` (baris 69)
- **Masalah:** Terdapat banyak penggunaan warna hex statis (`#ffffff`, `#aaaaaa`, `#55ff55`, `#ffaa00`, `#ff5555`, `#e74c3c`, dll). Warna-warna ini memiliki nilai ekuivalen pada ThemeManager seperti `text_primary`, `text_secondary`, `success`, `warning`, dan `danger`.
- **Rekomendasi:** Gunakan fungsi `ThemeManager.get_color()` daripada melakukan hardcoding hex agar konsisten jika suatu saat warna global diganti.

### [H-001] Inkonsistensi Ukuran Font (Font Size)
- **Severity:** High
- **File:** Hampir seluruh file di `ui/widgets/` dan `ui/screens/`
- **Masalah:** Terdapat lebih dari 50 baris kode yang menetapkan `font-size` secara hardcode dengan ukuran yang sangat beragam tanpa pola baku. Contohnya, teks body ada yang 11px, 12px, 13px, 14px, 15px, hingga 16px. Teks heading juga bervariasi mulai dari 14px hingga 28px.
- **Rekomendasi:** Terapkan tipografi (Typography System) dalam `ThemeManager` dan ubah ukuran font menjadi konstanta seperti `heading_1`, `body_text`, `caption`, dll.

### [L-001] QPushButton Tanpa `PointingHandCursor`
- **Severity:** Low
- **File:** `ui/screens/queue_screen.py`
- **Masalah:** File memiliki `QPushButton` tapi tidak ada instruksi `setCursor(Qt.PointingHandCursor)`, sehingga kursor panah biasa akan terlihat saat hover di atas tombol (mengurangi UX interaktif).
- **Rekomendasi:** Tambahkan `.setCursor(Qt.PointingHandCursor)` atau set secara default di stylesheet global pada tag `QPushButton`.

### [M-002] Screen Terdaftar Tanpa Implementasi `on_navigated`
- **Severity:** Medium
- **File:** `ui/screens/home_screen.py`
- **Masalah:** Screen "HOME" diregistrasikan ke router, tapi `HomeScreen` tidak memiliki metode `on_navigated` yang didefinisikan secara spesifik (berbeda dari screen lainnya).
- **Rekomendasi:** Tambahkan metode `on_navigated` ke dalam `HomeScreen` meskipun isinya hanya membersihkan kotak pencarian atau melakukan refresh komponen tertentu jika tidak ada parameter khusus.

## Tidak Ditemukan Masalah Pada
- **Widget Overflow di Resolusi Rendah:** Widget tidak ada yang dipaksa menggunakan lebar > 800px atau tinggi > 600px. Resolusi 1366x768 akan aman.
- **Signal & Routing (Dead Routes):** Semua target routing pada `navigate_requested.emit()` di UI (yaitu `HOME`, `INSPECTOR`, `RESULTS`) memiliki route terdaftar yang relevan di `main.py`.

## Rekomendasi Prioritas
1. Selesaikan [H-001] karena akan memberikan impact positif pada keseluruhan estetika dan UI consistency (terutama untuk UI yang clean & modern).
2. Tuntaskan [M-001] dan ganti semua hardcode colors ke `ThemeManager.get_color(...)` untuk memastikan fungsionalitas light/dark mode di masa depan.
3. Fix [M-002] pada `HomeScreen` agar state management router bisa berjalan konsisten.
4. Terapkan hand cursor untuk queue screen [L-001].
