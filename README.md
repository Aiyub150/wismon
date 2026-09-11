# WISMON — Windows System Monitoring

> **Monitor. Analyze. Understand.**

**WISMON (Windows System Monitoring)** adalah aplikasi monitoring dan analisis profesional untuk sistem operasi Windows yang memberikan visibilitas real-time mendalam terhadap kinerja prosesor, memori kernel, penyimpanan disk, jaringan, proses, layanan, dan keamanan sistem.

Dibangun dengan fondasi UI **TailAdmin**, WISMON menghadirkan antarmuka sistem monitoring yang bersih, profesional, cepat, dan responsif dengan dukungan penuh **Dark Mode** dan **Light Mode**, menggantikan antarmuka generatif dengan konsol telemetri data-dense berstandar industri.

---

## ⚡ Fitur Utama

1. **TailAdmin Professional UI Foundation**:
   - Desain dashboard profesional terinspirasi dari TailAdmin Dashboard Template.
   - Dukungan tema ganda: **Dark Mode** (Boxdark `#1A222C` / `#24303F`) dan **Light Mode** (`#F1F5F9` / `#FFFFFF`).
   - Ikon vektor SVG standar industri tanpa elemen dekoratif berlebihan atau emoji non-profesional.
   - Status koneksi real-time: `● LIVE` (pulsing dot hijau), `● RECONNECTING`, dan `● OFFLINE`.

2. **Decoupled Real-Time Streaming Architecture**:
   - Streaming telemetri Server-Sent Events (SSE) berkadensi ~1.0 detik langsung dari state in-memory tanpa jeda / lag 3–5 detik.
   - Scheduler independen: telemetri ultra-cepat (CPU, RAM, GPU, Storage I/O, Network) dieksekusi instan (<10ms), sedangkan kolektor berat (`ProcessCollector`, `ServicesCollector`, `HardwareCollector`) diproses secara asinkron di thread worker terpisah (`asyncio.to_thread`).
   - Penulisan database SQLite (WAL) dibatch per 5–10 frame untuk menjaga efisiensi SSD dan meminimalkan disk I/O.

3. **Monitoring First & No Fake Data**:
   - Seluruh data diperoleh langsung dari Windows API aktual (`psutil`, `kernel32.dll`, `iphlpapi.dll`, `advapi32.dll`, WMI, ACPI thermal zones).
   - Metrik yang tidak didukung oleh hardware atau BIOS ditandai eksplisit sebagai `Unavailable` atau `Not supported` — **tanpa data tiruan/palsu**.

4. **Dashboard Kesehatan Sistem & 8 KPI**:
   - Health Score dinamis (0–100) berbasis beban CPU, tekanan memori, saturasi storage, dan ancaman aktif.
   - 8 Kartu KPI: CPU Load, RAM, Storage, CPU Temperature, GPU Load, GPU Temperature, Network Throughput, dan Active Threats.

5. **Analisis CPU & Per-Core Matrix**:
   - Workload matrix per-core (logical dan physical cores).
   - Frekuensi real-time (MHz), nama prosesor resmi dari Windows Registry, dan analisis beban kerja terhadap baseline historis.

6. **Deep Memory Architecture**:
   - RAM fisik (Used, Available, Free, Cached).
   - Metrik kernel Windows mendalam via `GetPerformanceInfo`: **Paged Pool**, **Non-Paged Pool**, **Commit Charge**, **Commit Limit**, System Cache, dan jumlah Handles.

7. **Storage & I/O Analytics + Storage Analyzer**:
   - Partisi disk dengan tipe filesystem (NTFS, exFAT, dsb.).
   - Live throughput disk (Read/Write MB/s dan operasi per detik).
   - **Storage Analyzer**: Menemukan file berukuran besar (> 100 MB), file lama, dan file sementara di direktori User Temp tanpa pernah melakukan auto-delete (safety first).

8. **Network Throughput & Socket Explorer**:
   - Informasi adapter aktif (Wi-Fi, Ethernet, IPv4, IPv6, MAC, Gateway, Link Speed).
   - Throughput bandwidth real-time (Upload/Download).
   - **Socket Explorer**: Menampilkan koneksi TCP/UDP aktif beserta resolusi hostname reverse-DNS secara asinkron dengan in-memory cache.

9. **Process Explorer & Windows Services**:
   - Daftar proses Windows dengan pencarian cepat, pengurutan fleksibel (CPU, RAM, Threads, Handles), modal inspeksi, dan dialog terminasi proses yang aman dengan konfirmasi eksplisit.
   - Daftar Windows Services lengkap dengan visualisasi pohon hirarki proses **`svchost.exe`**.

10. **Threat Center & Security Events**:
    - Deteksi lonjakan koneksi mencurigakan, proses anomali ber-CPU ekstrem, dan saturasi memori kritis.
    - Lifecycle event keamanan: `Detected` → `Analyzing` → `Confirmed / Suspicious / False Positive` → `Mitigation Recommended` → `User Action` → `Resolved`.
    - Tindakan mitigasi aman (Terminate Process, Resolve, Flag False Positive).

11. **Dahoo Hybrid Assistant**:
    - Maskot pendamping cerdas dengan ekspresi wajah reaktif (`happy`, `normal`, `worried`, `alert`, `thinking`).
    - **Local Engine (Offline, 0 Tokens)**: Menjawab pertanyaan umum kondisi sistem secara instan berdasarkan telemetry nyata.
    - **Cloud AI (Gemini)**: Opsional menggunakan `google-genai` SDK jika `GEMINI_API_KEY` dikonfigurasi di `.env`, lengkap dengan kartu transparansi konsumsi token dan estimasi biaya per request.

---

## 🏗️ Arsitektur Sistem

```
┌────────────────────────────────────────────────────────┐
│                      Windows OS                        │
│    Kernel32 / IP Helper / Advapi32 / WMI / Registry    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Collector Layer                     │
│  cpu.py | memory.py | storage.py | network.py          │
│  process.py | socket.py | services.py | hardware.py    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           Monitoring & Analysis Engine                 │
│  - Realtime Ring Buffer (300 samples)                  │
│  - Analysis Engine (Baselines, Thresholds, Health)     │
│  - Threat Center (Security lifecycle & rules)          │
│  - Storage Analyzer (Large / Temp file scanner)        │
│  - Dahoo Engine (Local Rule Router + Gemini Cloud)     │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│  SQLite Database (WAL)    │ │   FastAPI Backend        │
│  database/monitoring.db   │ │   REST Endpoints & SSE   │
└───────────────────────────┘ └───────────┬──────────────┘
                                          │
                                          ▼
                              ┌──────────────────────────┐
                              │  Modern Frontend SPA     │
                              │  HTML5, CSS, Vanilla JS  │
                              └──────────────────────────┘
```

---

## 📋 Persyaratan Sistem

- **Sistem Operasi**: Windows 10 atau Windows 11 (64-bit)
- **Python**: Versi 3.10 atau lebih baru (direkomendasikan Python 3.11+)
- **Hak Akses**: Pengguna standar (Hak Administrator hanya diperlukan untuk menghentikan service atau proses sistem yang diproteksi)

---

## 🚀 Instalasi & Menjalankan Aplikasi

### 1. Masuk ke Direktori Project
```powershell
cd "c:\Users\aiyub\Desktop\System Monitoring"
```

### 2. Aktifkan Virtual Environment & Pasang Dependensi
Virtual environment `.venv` sudah tersedia di project:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (Opsional)
Salin berkas template `.env.example` menjadi `.env`:
```powershell
cp .env.example .env
```
Isi variabel yang diperlukan jika ingin mengaktifkan mode Cloud AI pada Dahoo:
```env
# Server
HOST=127.0.0.1
PORT=8080

# Dahoo Cloud AI (Opsional)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*Catatan: Tanpa `GEMINI_API_KEY`, Dahoo tetap dapat digunakan sepenuhnya secara offline via Local Engine.*

### 4. Jalankan Aplikasi
Jalankan satu perintah tunggal:
```powershell
python monitor.py
```
Aplikasi akan menampilkan banner di konsol terminal:
```text
=======================================
 Windows System Monitoring
=======================================

Backend : http://127.0.0.1:8080
Frontend: http://127.0.0.1:8080

Monitoring: ONLINE

CPU     : 18.5%
Memory  : 52.3%
Threats : 0

Press Ctrl+C to stop.
=======================================
```

Buka browser pada alamat: **`http://localhost:8080`**

---

## 🗄️ Database & Retensi Data

Aplikasi menggunakan database lokal **SQLite** dalam mode **WAL (Write-Ahead Logging)** yang terletak pada:
```text
database/monitoring.db
```
- **Buffering**: Data telemetry ditulis secara batched untuk meminimalkan beban I/O disk.
- **Retensi Data**:
  - Ring buffer in-memory: 300 sampel data real-time terbaru (tanpa beban disk).
  - Telemetry detail: Tersimpan selama 24 jam.
  - Pembersihan otomatis (*retention purge*) berjalan secara berkala di latar belakang.

---

## 🛡️ Prinsip Keamanan & Mitigasi

- **Least Privilege**: Tidak memaksa pengguna menjalankan aplikasi sebagai Administrator.
- **Konfirmasi Eksplisit**: Tindakan berbahaya (seperti mematikan proses `Terminate Process` atau menghentikan service) **selalu mewajibkan konfirmasi modal** dari pengguna.
- **Perlindungan Kernel**: Proses inti sistem (PID 0, PID 4) tidak dapat dimatikan melalui API.
- **Keamanan Kunci Rahasia**: Berkas `.env` dan database dikecualikan dari Git repository via `.gitignore`.

---

## 🛠️ Struktur Direktori

```text
├── database/
│   └── monitoring.db              # Database SQLite (dibuat saat startup)
├── backend/
│   ├── config.py                  # Konfigurasi & pembacaan environment
│   ├── db.py                      # Operasi database & schema
│   ├── collectors/                # Kolektor telemetry terisolasi
│   │   ├── cpu.py                 # CPU & per-core
│   │   ├── memory.py              # RAM & kernel pools (Win32)
│   │   ├── gpu.py                 # Telemetry GPU / Adapter
│   │   ├── storage.py             # Partisi disk & live I/O
│   │   ├── network.py             # Adapter & throughput speed
│   │   ├── process.py             # Enumerasi proses Windows
│   │   ├── socket.py              # Koneksi jaringan & async DNS
│   │   ├── services.py            # Windows services & svchost
│   │   └── temperature.py         # ACPI thermal zones & baterai
│   ├── engine/                    # Mesin analisis & Dahoo
│   │   ├── aggregator.py          # Ring buffer & SSE coordinator
│   │   ├── analysis.py            # Baseline & health scoring
│   │   ├── threat_center.py       # Security rules & threat lifecycle
│   │   ├── storage_analyzer.py    # Pemindai file berukuran besar / temp
│   │   └── dahoo_engine.py        # Asisten Dahoo (Local + Cloud)
│   ├── api/                       # Router FastAPI REST & SSE
│   └── main.py                    # Entrypoint aplikasi FastAPI
├── frontend/
│   ├── index.html                 # Antarmuka web utama
│   ├── css/                       # Desain sistem & tokens CSS
│   └── js/                        # Engine charts, SSE, Dahoo & controller halaman
├── monitor.py                     # Skrip startup terpadu
├── requirements.txt               # Daftar dependensi Python
├── .env.example                   # Template konfigurasi environment
└── README.md                      # Dokumentasi project
```

---

## 📄 Lisensi
Project ini didistribusikan untuk monitoring dan administrasi sistem Windows pribadi/organisasi.
