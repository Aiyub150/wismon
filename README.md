# WISMON — Windows System Monitoring

> **Monitor. Analyze. Understand.**

**WISMON (Windows System Monitoring)** adalah aplikasi monitoring, observabilitas, dan pemeliharaan performa sistem operasi Windows modern yang menyajikan visibilitas real-time mendalam terhadap kinerja CPU, memori kernel, adapter grafis (GPU), penyimpanan disk, jaringan, proses, layanan, dan keamanan sistem.

Dibangun dengan fondasi antarmuka profesional berbasis desain **TailAdmin**, WISMON menghadirkan konsol telemetri berstandar industri dengan dukungan penuh **Dark Mode** dan **Light Mode**, arsitektur streaming Server-Sent Events (SSE) berkecepatan tinggi, serta asisten cerdas **Dahoo** dengan kapabilitas **Detect-Ask-Act**.

---

## ⚡ Fitur Utama

### 1. TailAdmin Professional UI Foundation
- Antarmuka monitoring elegan terinspirasi dari TailAdmin Dashboard Template.
- Dukungan tema ganda instan: **Dark Mode** (`#1A222C` / `#24303F`) dan **Light Mode** (`#F1F5F9` / `#FFFFFF`).
- Indikator status telemetri real-time: `● LIVE` (pulsing dot hijau), `● RECONNECTING`, dan `● OFFLINE`.
- Responsive layout yang dense dan fokus pada penyajian data metrik teknis tanpa ornamen visual berlebih.

### 2. Native Windows PDH & ACPI Thermal Architecture
- **Zero-Privilege Thermal Monitoring**: Menggunakan antarmuka native Windows Performance Data Helper (`pdh.dll`) via counter `\Thermal Zone Information(*)\High Precision Temperature`.
- Pembacaan suhu CPU & SoC akurat (derajat Celsius) secara instan tanpa memerlukan hak akses Administrator atau driver kernel pihak ketiga.
- Indikator visual meter / progress bar interaktif pada kartu KPI suhu di halaman Dashboard.

### 3. Universal Multi-GPU & Integrated Graphics Telemetry
- Mendukung seluruh arsitektur grafis: **Intel Iris Xe**, **Intel UHD**, **AMD Radeon**, dan **NVIDIA GeForce / RTX**.
- Integrasi Windows DirectX / WDDM PerfCounters untuk engine utilization (3D) dan alokasi memory VRAM (Dedicated & Shared System Memory).
- Deteksi diode suhu dedicated via `nvidia-smi` untuk kartu diskrit, serta korelasi thermal package SoC untuk GPU terintegrasi.
- Tampilan GPU & Hardware dinamis tanpa delay atau status stuck pada "Detecting...".

### 4. Decoupled Real-Time Streaming Architecture
- Streaming telemetri Server-Sent Events (SSE) berkadensi ~1.0 detik langsung dari state in-memory ring-buffer (300 sampel data).
- Scheduler independen: telemetri cepat (CPU, RAM, GPU, Storage I/O, Network) dieksekusi instan (<10ms), sedangkan kolektor berat (`ProcessCollector`, `ServicesCollector`, `HardwareCollector`) diproses secara asinkron di worker thread terpisah (`asyncio.to_thread`).
- Penulisan database SQLite (WAL) dibatch per 5–10 frame untuk menjaga efisiensi SSD dan meminimalkan disk I/O.

### 5. Threat Center & Security Events dengan Aksi Nyata (Active Remediation)
- Deteksi otomatis anomali beban prosesor ekstrem, lonjakan koneksi mencurigakan, dan kepenuhan memori fisik.
- **Tindakan Nyata Saat Resolve**:
  - **High CPU Process**: Menangguhkan (*pause / suspend*) proses target selama 3.5 detik untuk mendinginkan prosesor dan menstabilkan beban sistem, lalu melanjutkannya (*resume*) secara normal.
  - **RAM Exhaustion**: Membersihkan dan memangkas (*trim*) working set memory proses aktif via Windows API `EmptyWorkingSet`.
  - **Malicious Process**: Opsi terminasi proses aman dengan konfirmasi eksplisit.
- Setiap aksi tercatat dalam audit log dan riwayat database.

### 6. Dahoo Assistant 2.0 (Detect — Ask — Act)
- Maskot pendamping cerdas dengan ekspresi wajah reaktif (`happy`, `normal`, `worried`, `alert`, `thinking`).
- **Pola Detect-Ask-Act**:
  - **Detect**: Memeriksa beban CPU, RAM, suhu, file sementara, dan ancaman secara berkelanjutan.
  - **Ask**: Memberikan saran perbaikan kontekstual dilengkapi tombol aksi interaktif (misalnya `[⚡ Tangguhkan Proses (3.5s)]` atau `[⚡ Bebaskan Cache RAM]`).
  - **Act**: Mengeksekusi perbaikan nyata saat tombol diklik atau saat pengguna menjawab setuju (*"ya"*, *"lakukan"*, *"ok"*).
- **Pengenalan Bahasa Alami Offline**: Mampu memahami berbagai pertanyaan berbahasa Indonesia dan Inggris (seperti *"kenapa laptop lemot?"*, *"berapa suhu komputer?"*, *"bersihkan memori"*) secara fleksibel tanpa ketergantungan teks kaku atau peringatan API key yang tidak perlu.
- **Proactive System Alerts**: Peringatan lonjakan CPU (>85%) atau ancaman keamanan otomatis disalurkan langsung sebagai bubble chat asisten di feed percakapan Dahoo.
- **Mode Cloud AI Opsional**: Mendukung penalaran mendalam berbasis Google Gemini jika `GEMINI_API_KEY` dikonfigurasi di `.env`.

### 7. Storage Analyzer & Memory Deep Architecture
- **Deep Memory**: Mengurai RAM fisik, Paged Pool, Non-Paged Pool, Commit Charge, Commit Limit, dan System Cache via `GetPerformanceInfo`.
- **Storage Analyzer**: Menemukan file berukuran besar (> 100 MB), file lama (> 180 hari), dan pembersihan aman file sementara di folder Temp.

### 8. Network Throughput & Socket Explorer
- Kecepatan unduh dan unggah real-time per adapter aktif (Wi-Fi, Ethernet).
- Visualisasi koneksi TCP/UDP aktif beserta resolusi nama domain (reverse-DNS) asinkron.

---

## 🏗️ Arsitektur Sistem

```
┌────────────────────────────────────────────────────────┐
│                      Windows OS                        │
│    Kernel32 / PDH.dll / Advapi32 / DirectX / WMI       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Collector Layer                     │
│  cpu.py | memory.py | gpu.py | storage.py              │
│  network.py | process.py | socket.py | temperature.py  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           Monitoring & Remediation Engine              │
│  - Realtime Ring Buffer (300 samples)                  │
│  - Analysis Engine (Baselines, Thresholds, Health)     │
│  - Threat Center (Active Remediation & Cool Down)      │
│  - Storage Analyzer (Temp / Large file scanner)        │
│  - Dahoo Engine (Detect-Ask-Act + Gemini Cloud)        │
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
                              │  TailAdmin Modern SPA    │
                              │  HTML5, CSS, Vanilla JS  │
                              └──────────────────────────┘
```

---

## 📋 Persyaratan Sistem

- **Sistem Operasi**: Windows 10 atau Windows 11 (64-bit)
- **Python**: Versi 3.10 atau lebih baru (disarankan 3.11+)
- **Hak Akses**: Pengguna standar (Hak Administrator hanya diperlukan untuk menghentikan service sistem terlindungi)

---

## 🚀 Instalasi & Menjalankan Aplikasi

### 1. Masuk ke Direktori Project
```powershell
cd "c:\Users\nama\System Monitoring"
```

### 2. Aktifkan Virtual Environment & Pasang Dependensi
Virtual environment `.venv` sudah tersedia di repositori:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (Opsional)
Salin berkas template `.env.example` menjadi `.env`:
```powershell
cp .env.example .env
```
Isi konfigurasi jika ingin mengaktifkan mode Cloud AI pada Dahoo:
```env
# Server
HOST=127.0.0.1
PORT=8080

# Dahoo Cloud AI (Opsional)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```
*Catatan: Tanpa `GEMINI_API_KEY`, Dahoo tetap dapat digunakan sepenuhnya secara offline via Local Intelligence Engine.*

### 4. Jalankan Aplikasi
Jalankan satu perintah tunggal:
```powershell
python monitor.py
```
Aplikasi akan menampilkan banner di konsol terminal:
```text
=======================================
 WISMON — Windows System Monitoring
 Monitor. Analyze. Understand.
=======================================

Backend : http://127.0.0.1:8080
Frontend: http://127.0.0.1:8080

Monitoring: ONLINE (SSE Stream Active)

CPU     : 18.5%
Memory  : 52.3%
Threats : 0

Press Ctrl+C to stop.
=======================================
```

Buka browser pada alamat: **`http://127.0.0.1:8080`**

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
- **Konfirmasi Eksplisit**: Tindakan berbahaya (seperti mematikan proses `Terminate Process`) **selalu mewajibkan konfirmasi modal** dari pengguna.
- **Perlindungan Kernel**: Proses inti sistem (PID 0, PID 4) tidak dapat dimatikan melalui API.
- **Keamanan Berkas**: Berkas `.env`, folder `Bug/`, dan catatan markdown pengembangan dikecualikan dari Git repository via `.gitignore`.

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
│   │   ├── gpu.py                 # Telemetry GPU (PDH & DirectX)
│   │   ├── storage.py             # Partisi disk & live I/O
│   │   ├── network.py             # Adapter & throughput speed
│   │   ├── process.py             # Enumerasi proses Windows
│   │   ├── socket.py              # Koneksi jaringan & async DNS
│   │   ├── services.py            # Windows services & svchost
│   │   └── temperature.py         # Native PDH ACPI thermal zones & baterai
│   ├── engine/                    # Mesin analisis & Dahoo
│   │   ├── aggregator.py          # Ring buffer & SSE coordinator
│   │   ├── analysis.py            # Baseline & health scoring
│   │   ├── threat_center.py       # Active remediation & cooldown engine
│   │   ├── storage_analyzer.py    # Pemindai & pembersih file sementara
│   │   └── dahoo_engine.py        # Asisten Dahoo (Detect-Ask-Act & Gemini)
│   ├── api/                       # Router FastAPI REST & SSE
│   └── main.py                    # Entrypoint aplikasi FastAPI
├── frontend/
│   ├── index.html                 # Antarmuka web TailAdmin
│   ├── css/                       # Desain sistem & tokens CSS
│   └── js/                        # Engine charts, SSE, Dahoo & controller halaman
├── monitor.py                     # Skrip startup terpadu
├── requirements.txt               # Daftar dependensi Python
├── .env.example                   # Template konfigurasi environment
├── .gitignore                     # Konfigurasi pengecualian Git
└── README.md                      # Dokumentasi project
```

---

## 📄 Lisensi
Project ini didistribusikan untuk monitoring dan administrasi sistem Windows pribadi/organisasi.
