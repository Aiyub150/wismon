# WISMON — Windows System Monitoring

> **Monitor. Analyze. Understand.**

WISMON (**WIndows System MONitoring**) adalah aplikasi monitoring Windows berbasis Python yang membantu pengguna melihat kondisi komputer secara real-time, memahami penggunaan resource, menemukan aktivitas yang tidak biasa, dan melakukan beberapa tindakan pemeliharaan secara langsung.

WISMON berjalan sebagai aplikasi web lokal. Backend dan frontend dijalankan dari satu proses Python, lalu dashboard dibuka melalui browser pada komputer yang sama.

> **Status project:** Open-source / dalam pengembangan  
> **Platform:** Windows 10/11 64-bit  
> **Mode AI:** Local Intelligence tersedia tanpa API key; Google Gemini bersifat opsional.

---

## 📑 Daftar Isi

- [Apa yang Bisa Dilakukan WISMON?](#-apa-yang-bisa-dilakukan-wismon)
- [Tampilan dan Menu](#-tampilan-dan-menu)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Instalasi dari Nol](#-instalasi-dari-nol)
- [Quick Start](#-quick-start)
- [Konfigurasi `.env`](#-konfigurasi-env)
- [Cara Menggunakan WISMON](#-cara-menggunakan-wismon)
- [Cara Memahami Status WISMON](#-cara-memahami-status-wismon)
- [Contoh Workflow Komputer Lambat](#-contoh-workflow-komputer-lambat)
- [Google Gemini / Cloud AI](#-google-gemini--cloud-ai)
- [Database dan Retensi Data](#-database-dan-retensi-data)
- [Hak Akses Administrator](#-hak-akses-administrator)
- [Troubleshooting](#-troubleshooting)
- [Catatan Keamanan](#-catatan-keamanan)
- [Batasan WISMON](#-batasan-wismon)
- [Struktur Project](#-struktur-project)
- [Untuk Developer](#-untuk-developer)
- [Lisensi](#-lisensi)

---

# 🧭 Apa yang Bisa Dilakukan WISMON?

WISMON mengumpulkan telemetry dari Windows dan menampilkannya melalui dashboard web lokal.

Fitur utamanya meliputi:

- **Ultra-Fast Telemetry Loop & Low CPU Overhead**: Latensi loop ~17ms dengan arsitektur worker adaptif (interval 4.5s–8.0s untuk proses, 6.0s–12.0s untuk soket, 10.0s–15.0s untuk hardware) dan ThreadPoolExecutor (3 workers) untuk resolusi DNS, menjaga penggunaan CPU latar belakang sangat rendah (< 2%).
- **WISMON Self-Protection & EDR Guardrails**: Perlindungan bawaan mutlak bagi proses server WISMON (`python.exe`) dan agen keamanan/antivirus (Bitdefender, Windows Defender) dari tindakan penangguhan atau terminasi yang dapat membekukan server atau melemahkan endpoint.
- **Hardware-Aware Storage Detection**: Mendeteksi model hardware asli melalui WMI (`Win32_DiskDrive`), membedakan Samsung NVMe SSD, SanDisk USB Flashdisk, dan SDHC Card secara akurat.
- **Multi-Drive Storage Analyzer**: Memindai drive terpilih (`C:`, `D:`, `E:`, atau semua drive), mendeteksi folder sampah/cache raksasa (`node_modules`, `.cache`, `CrashDumps` > 20MB) dan file besar (> 100MB).
- **Safe Review & Recycle Bin**: Pembersihan aman file dan folder dengan memindahkannya ke Windows Recycle Bin (dilengkapi OS guardrails yang melindungi `C:\Windows`, `Program Files`, dan sistem penting).
- **Socket Explorer dengan Prioritas Internet**: Menyorot koneksi internet eksternal aktif (seperti TikTok, streaming, remote IP) di baris teratas, dilengkapi filter instan (`🌐 Internet Saja`, `Semua`, `ESTABLISHED`, `LISTENING`) dan search bar domain/IP.
- **Batch Threat Mitigation**: Menindak seluruh anomali keamanan secara simultan via tombol *Tindak Semua* atau perintah asisten, dengan pelaporan status jujur (`MITIGATED`, `PROTECTED_SKIPPED`, atau `ACTION_FAILED`).
- **Agentic Dahoo Assistant (Gemini 3.8 Flash Streaming & Auto-Failover)**: Mampu melakukan streaming end-to-end (SSE) tanpa respons terpotong ke Gemini 3.8 Flash saat online dan failover transparan ke Local Engine saat offline, mengeksekusi mitigasi sistem secara langsung dari chat dengan validasi 2 fase dan verifikasi status real-time.
- **Universal CPU & Memory Optimizer**: Tombol one-click *⚡ Optimalkan CPU* (meredam proses terberat non-sistem) pada halaman CPU dan *⚡ Optimalkan Memori* (membersihkan cache working set RAM via Win32 `EmptyWorkingSet`) pada halaman Memory.
- **Decoupled Telemetry & Batch Persistence**: Siklus telemetri real-time 1.0s murni berjalan di RAM (<15ms), sementara penulisan riwayat ke SQLite ditangani oleh background worker setiap 5 detik, mencegah disk lock dan lonjakan I/O.
- CPU usage dan telemetry per-core.
- RAM dan statistik memory kernel tingkat lanjut (Paged/Non-paged pool, Commit Charge).
- GPU dan hardware telemetry.
- Disk/storage throughput I/O real-time.
- Process Explorer dan Windows Services Explorer.
- Performance History dengan retensi lokal SQLite.
- Dark Mode dan Light Mode terintegrasi TailAdmin.
- Streaming telemetry real-time menggunakan Server-Sent Events (SSE).

Secara arsitektur, WISMON menggunakan FastAPI sebagai backend/API berlatensi ultra-rendah, SQLite sebagai database lokal, collector Windows sebagai sumber telemetry, dan TailAdmin HTML/CSS/JavaScript murni sebagai dashboard. Struktur repository saat ini memisahkan `backend/`, `frontend/`, `database/`, `Fix/`, serta `monitor.py` sebagai entry point utama.

---

# 🖥️ Tampilan dan Menu

Sidebar WISMON saat ini dibagi menjadi:

| Kelompok | Menu | Fungsi |
|---|---|---|
| Overview | Dashboard | Ringkasan kondisi komputer |
| System | CPU | Analisis penggunaan CPU |
| System | Memory | Analisis RAM dan memory kernel |
| System | GPU & Hardware | Informasi GPU dan hardware |
| System | Storage | Kapasitas dan aktivitas storage |
| System | Network | Adapter, throughput, dan koneksi |
| Activity | Processes | Daftar proses Windows |
| Activity | Services | Daftar Windows Services |
| Security | Security Events | Anomali/event keamanan |
| Analysis | Performance & History | Analisis performa dan history |
| Assistant | Dahoo | Asisten monitoring dan troubleshooting |

---

# 💻 Persyaratan Sistem

## Wajib

- Windows 10 atau Windows 11 64-bit.
- Python **3.10 atau lebih baru**.
- Git untuk mengunduh repository.
- Browser modern seperti Chrome, Edge, atau Firefox.

Python **3.11** direkomendasikan untuk development.

Dependency utama yang digunakan repository saat ini antara lain `psutil`, `fastapi`, `uvicorn`, `aiosqlite`, `pydantic`, `python-dotenv`, dan `google-genai`.

> **Catatan:** versi package ditentukan oleh `requirements.txt` dan dapat berubah mengikuti perkembangan project.

---

# 🚀 Instalasi dari Nol

Bagian ini ditulis untuk pengguna yang **belum pernah menjalankan WISMON sebelumnya**.

## 1. Install Git

Download dan install Git:

<https://git-scm.com/download/win>

Setelah selesai, buka **PowerShell** dan jalankan:

```powershell
git --version
```

Jika muncul versi Git, berarti instalasi berhasil.

---

## 2. Install Python

Download Python:

<https://www.python.org/downloads/windows/>

Saat installer Python dibuka, centang:

```text
Add Python.exe to PATH
```

Setelah instalasi selesai, buka PowerShell baru:

```powershell
python --version
```

atau:

```powershell
py --version
```

Pastikan versinya minimal 3.10. Python 3.11 direkomendasikan.

---

## 3. Download Repository

Pilih lokasi tempat WISMON akan disimpan.

Contoh:

```powershell
cd $HOME
git clone https://github.com/Aiyub150/wismon.git
```

Setelah selesai:

```powershell
cd wismon
```

Cek isi folder:

```powershell
dir
```

Anda seharusnya melihat file/folder seperti:

```text
backend
frontend
monitor.py
requirements.txt
.env.example
README.md
```

---

## 4. Masuk ke Folder WISMON

Jika PowerShell dibuka dari lokasi lain:

```powershell
cd "C:\path\ke\wismon"
```

Contoh:

```powershell
cd "C:\Users\Aiyub\wismon"
```

> Ganti path contoh dengan lokasi repository Anda sendiri.

---

## 5. Buat Virtual Environment

Buat environment Python lokal untuk WISMON:

```powershell
py -3.11 -m venv .venv
```

Jika `py -3.11` tidak tersedia tetapi `python` tersedia:

```powershell
python -m venv .venv
```

Setelah selesai, folder berikut akan dibuat:

```text
wismon/
└── .venv/
```

> **Penting:** jangan mengandalkan `.venv` dari komputer atau repository lain. Virtual environment sebaiknya dibuat pada mesin pengguna sendiri.

---

## 6. Aktifkan Virtual Environment

Di PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Jika berhasil, prompt biasanya berubah menjadi:

```text
(.venv) PS C:\Users\Aiyub\wismon>
```

### Jika PowerShell menolak menjalankan script

Jika muncul pesan bahwa script execution diblokir:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Kemudian coba lagi:

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatifnya, gunakan Command Prompt:

```cmd
cd C:\Users\Aiyub\wismon
.venv\Scripts\activate.bat
```

---

## 7. Install Dependency

Pastikan `.venv` aktif, kemudian:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Untuk pengecekan sederhana:

```powershell
python -c "import fastapi, psutil, aiosqlite; print('WISMON dependencies OK')"
```

Jika berhasil:

```text
WISMON dependencies OK
```

---

## 8. Buat File `.env`

Repository menyediakan:

```text
.env.example
```

Buat salinan:

```powershell
Copy-Item .env.example .env
```

Kemudian buka:

```powershell
notepad .env
```

### Konfigurasi minimum

Untuk penggunaan lokal, Anda dapat memakai:

```env
HOST=127.0.0.1
PORT=8080
```

File `.env.example` juga menyediakan interval monitoring serta retention data seperti:

```env
INTERVAL_REALTIME=1.0
INTERVAL_PROCESS=2.0
INTERVAL_SOCKETS=3.0
INTERVAL_SERVICES=5.0
INTERVAL_STORAGE_IO=1.0

DETAILED_RETENTION_HOURS=24
AGGREGATED_RETENTION_DAYS=7
```

### Gemini tidak wajib

Biarkan kosong jika belum ingin mengaktifkan Cloud AI:

```env
GEMINI_API_KEY=
```

Dahoo tetap dapat menggunakan Local Intelligence Engine.

---

## 9. Jalankan WISMON

Pastikan berada di root repository dan `.venv` aktif:

```powershell
python monitor.py
```

Jika startup berhasil, terminal akan menunjukkan alamat server, secara default:

```text
http://127.0.0.1:8080
```

---

## 10. Buka Dashboard

Buka browser dan akses:

```text
http://127.0.0.1:8080
```

**Jangan membuka frontend sebagai `file:///...`**. Dashboard disajikan oleh backend WISMON.

---

# ⚡ Quick Start

Setelah Git dan Python sudah terinstall:

```powershell
git clone https://github.com/Aiyub150/wismon.git
cd wismon

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env

python monitor.py
```

Kemudian buka:

```text
http://127.0.0.1:8080
```

---

# ⚙️ Konfigurasi `.env`

Contoh konfigurasi lengkap:

```env
# Server
HOST=127.0.0.1
PORT=8080

# Monitoring intervals (seconds)
INTERVAL_REALTIME=1.0
INTERVAL_PROCESS=2.0
INTERVAL_SOCKETS=3.0
INTERVAL_SERVICES=5.0
INTERVAL_STORAGE_IO=1.0

# Dahoo Cloud AI (optional)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
GEMINI_THINKING_LEVEL=medium
DAHOO_MAX_OUTPUT_TOKENS=2048

# Dahoo Session & Memory
DAHOO_MEMORY_ENABLED=true
DAHOO_ACTION_TTL_SECONDS=60
DAHOO_MAX_CONTEXT_TURNS=10
DAHOO_DEFAULT_LANGUAGE=id

# Data retention
DETAILED_RETENTION_HOURS=24
AGGREGATED_RETENTION_DAYS=7
```

Konfigurasi tersebut sesuai dengan parameter yang saat ini disediakan oleh `.env.example` dan `backend/config.py`.

> **Catatan dokumentasi:** jangan menyalin API key ke README, source code, screenshot, atau commit Git.

---

# 📖 Cara Menggunakan WISMON

## 1. Dashboard

Buka:

```text
Overview → Dashboard
```

Dashboard digunakan untuk menjawab:

> **"Apakah komputer saya sedang dalam kondisi normal?"**

Periksa ringkasan seperti:

- CPU Usage
- Memory Usage
- GPU
- Storage
- Network
- Temperature jika tersedia
- Health Status
- Health Score
- Security/Threat information

### Cara membacanya

Sebagai contoh:

```text
CPU       25%
Memory    55%
Storage   68%
```

Gunakan hasil ini sebagai petunjuk awal:

- CPU tinggi terus-menerus → periksa **Processes**.
- RAM sangat tinggi → periksa **Memory** dan **Processes**.
- Disk hampir penuh → periksa **Storage**.
- Ada security event → periksa **Security Events**.

---

## 2. CPU

Buka:

```text
System → CPU
```

Gunakan untuk melihat penggunaan CPU dan pola beban CPU, termasuk per-core telemetry jika tersedia.

Cocok digunakan ketika:

- laptop terasa lambat,
- kipas berputar kencang,
- CPU terus tinggi,
- suhu meningkat.

---

## 3. Memory

Buka:

```text
System → Memory
```

Gunakan ketika RAM terasa penuh atau komputer mulai lambat.

WISMON juga menyediakan statistik memory tingkat lanjut, termasuk:

- Physical RAM
- Paged Pool
- Non-Paged Pool
- Commit Charge
- Commit Limit
- System Cache

---

## 4. GPU & Hardware

Buka:

```text
System → GPU & Hardware
```

Digunakan untuk melihat telemetry GPU/hardware yang dapat dibaca dari Windows.

Perangkat yang berbeda dapat menghasilkan data berbeda. Jika suatu sensor tidak tersedia, `Unavailable` tidak otomatis berarti hardware rusak.

---

## 5. Storage

Buka:

```text
System → Storage
```

Gunakan untuk:

- **Melihat Kapasitas & Hardware Model Asli**: Menampilkan kartu drive dengan model perangkat keras (Samsung NVMe SSD, SanDisk USB, SDHC card), tipe antarmuka (NVMe, USB, SCSI), status partisi, dan ruang bebas.
- **Memantau Aktivitas Disk I/O**: Grafik throughput disk live (Read Rate & Write Rate dalam MB/s serta I/O ops/sec).
- **Storage Analyzer Multi-Drive**: Pilih target pemindaian (`Semua Drive`, `Drive C:\`, `Drive D:\`, atau `Drive E:\`).
- **Mendeteksi Folder Sampah/Cache**: Menemukan direktori `node_modules`, `.cache`, `.gradle`, dan `CrashDumps` yang memakan ruang > 20 MB.
- **Mencari File Besar (> 100 MB)**: Menemukan file video, arsip zip, ISO, installer, dan backup yang membebani disk.
- **Safe Review Mode & Recycle Bin**: Setiap pembersihan file atau folder dipindahkan ke **Windows Recycle Bin** (bukan dihapus permanen), sehingga dapat dipulihkan sewaktu-waktu. Dilengkapi guardrails ketat yang mencegah penghapusan folder sistem `C:\Windows` atau `Program Files`.

---

## 6. Network

Buka:

```text
System → Network
```

Gunakan untuk memahami:

- **Adapter Jaringan Aktif**: Menampilkan IP internal, gateway, MAC address, link speed, dan status adapter (Wi-Fi, Ethernet, Virtual).
- **Live Throughput Curve**: Grafik bandwidth real-time dengan pemisahan laju Download (KB/s) dan Upload (KB/s).
- **Socket Explorer dengan Prioritas Internet**: Menampilkan koneksi jaringan aktif yang secara cerdas memprioritaskan koneksi eksternal remote (seperti TikTok, YouTube, web browsing, remote server) di baris teratas agar tidak tertimbun oleh koneksi loopback lokal.
- **Pencarian Domain & IP**: Kolom pencarian instan untuk memfilter host domain, alamat IP tujuan, PID, atau nama proses.
- **Filter Koneksi Interaktif**:
  - `🌐 Internet / Eksternal Saja` (default: langsung menampilkan aktivitas koneksi ke dunia luar).
  - `Semua Koneksi (All)`.
  - `ESTABLISHED Saja`.
  - `LISTENING Saja`.

---

## 7. Processes

Buka:

```text
Activity → Processes
```

Ini adalah halaman yang sangat berguna saat komputer terasa lambat.

Informasi yang tersedia mencakup:

- PID
- Process name
- CPU
- Memory
- Threads
- Handles
- Username
- description/path jika tersedia

Daftar proses dapat dicari dan diurutkan.

### Contoh

Jika:

```text
CPU = 95%
```

buka **Processes**, kemudian urutkan berdasarkan CPU.

### Inspect

Gunakan **Inspect** untuk melihat informasi proses sebelum mengambil tindakan.

### End

Tombol **End** digunakan untuk menghentikan proses.

**Jangan menghentikan process Windows hanya karena namanya terlihat asing.**

Jika tidak yakin:

1. Inspect process.
2. Periksa description/path.
3. Cari tahu fungsi process tersebut.
4. Tanyakan kepada Dahoo.
5. Baru pertimbangkan tindakan.

---

## 8. Services

Buka:

```text
Activity → Services
```

Digunakan untuk melihat Windows Services.

Menu ini berguna untuk troubleshooting service Windows, tetapi perubahan pada service sebaiknya hanya dilakukan jika Anda mengetahui dampaknya.

---

## 9. Security Events

Buka:

```text
Security → Security Events
```

Menampilkan anomali keamanan sistem secara komprehensif:

- **Kategori Anomali Terdeteksi**:
  - Penggunaan CPU ekstrem dan proses rogue (High CPU).
  - Tekanan memori dan kebocoran working set.
  - Disk space menipis (< 10% atau < 5 GB).
  - Lonjakan koneksi socket keluar (Outbound Connection Spike).
  - Eksekusi file mencurigakan dari direktori Temp (`AppData\Local\Temp`).
- **Batch Remediation Engine**:
  - Tombol **⚡ Tindak Semua (Mitigate All)** pada antarmuka untuk memitigasi seluruh anomali aktif secara otomatis dalam satu klik.
  - Membebaskan memory working set proses, mendinginkan proses CPU tinggi, membersihkan temp junk, dan memperbarui status secara jujur (`MITIGATED` atau `ACTION_FAILED`).
  - Sinkronisasi real-time: setelah mitigasi, event `threat-resolved` dipancarkan sehingga dashboard langsung ter-update tanpa reload.

### Penting: WISMON bukan antivirus

Security Events adalah indikator untuk investigasi, bukan bukti absolut malware.

---

## 10. Performance & History

Buka:

```text
Analysis → Performance & History
```

Gunakan untuk melihat data performa dan histori telemetry sehingga Anda dapat membandingkan kondisi komputer dari waktu ke waktu.

---

## 11. Dahoo Assistant

Klik tombol **Dahoo** pada topbar.

Dahoo adalah asisten AI monitoring dan troubleshooting otonom yang dapat bekerja dalam dua mode: **Local Intelligence** (bawaan tanpa internet/API key) dan **Google Gemini Cloud AI**.

### Kemampuan Agentik Baru (Gemini 3.5 Flash & Two-Phase Execution):
- **Gemini 3.5 Flash & Thinking Config**: Menggunakan model resmi `gemini-3.5-flash` dengan konfigurasi reasoning level native (`low`, `medium`, `high`) via `ThinkingConfig` tanpa parameter sampling usang. Model ini dipilih secara eksklusif karena kestabilan tinggi, kecepatan inferensi, dan efisiensi resource.
- **Multi-Turn Conversation Memory**: Mendukung percakapan multi-turn berkelanjutan dengan isolasi sesi (`session_id`), tombol `🔄 Sesi Baru`, serta persistensi riwayat di SQLite (`dahoo_sessions`).
- **Two-Phase Safe Agent Execution**: Dahoo tidak langsung mematikan proses atau menjalankan aksi drastis; melainkan mengajukan **Action Proposal Card** dengan validasi TTL 60 detik yang membutuhkan konfirmasi pengguna (`[Konfirmasi Tindakan]` atau `[Batalkan]`).
- **Validasi Target PID Ketat**: Memverifikasi keberadaan PID dan kesesuaian nama proses sebelum eksekusi untuk mencegah *PID re-assignment hazard*.
- **Verifikasi Metrik Real (Before vs After)**: Mengukur delta penggunaan CPU dan RAM riil sebelum dan sesudah eksekusi (`cpu_before` vs `cpu_after`, `ram_before` vs `ram_after`) serta menampilkan penghematan resource secara transparan.
- **Context Routing & Token Optimization**: Mengklasifikasikan intent pengguna untuk hanya menyertakan telemetry yang relevan (menghemat token dari ~2000+ menjadi ~200-500 tokens) sekaligus mengisolasi nama proses OS dari prompt injection.
- **Proteksi Timeout 10 Detik**: Menggunakan `AbortController` untuk mencegah Dahoo stuck/hang jika ada proses sistem yang membutuhkan waktu lama.

### Contoh pertanyaan & perintah

```text
Kenapa laptop saya lemot?
```

```text
Berapa penggunaan RAM saya?
```

```text
Lakukan tindakan untuk menyelesaikan semua masalah sistem
```

```text
Bersihkan memori dan optimalkan komputer
```

```text
Proses mana yang paling banyak menggunakan CPU?
```

---


# 🔄 Cara Memahami Status WISMON

Pada topbar terdapat status:

```text
LIVE
RECONNECTING
OFFLINE
```

## LIVE

Browser terhubung ke telemetry stream WISMON.

## RECONNECTING

Browser sedang mencoba menyambungkan kembali telemetry stream.

## OFFLINE

Koneksi ke backend/stream belum tersedia atau terputus.

### Jika tidak kembali ke LIVE

1. Pastikan terminal WISMON masih berjalan.
2. Periksa error di terminal.
3. Refresh browser.
4. Coba buka `http://127.0.0.1:8080`.
5. Periksa konflik port.

---

# 🐢 Contoh Workflow: Komputer Terasa Lambat

## Langkah 1 — Dashboard

Periksa:

```text
CPU
Memory
Storage
Health
```

## Langkah 2 — CPU tinggi?

Jika CPU tinggi, buka:

```text
Activity → Processes
```

## Langkah 3 — Cari process yang berat

Sort berdasarkan CPU atau Memory.

## Langkah 4 — Inspect

Klik:

```text
Inspect
```

## Langkah 5 — Gunakan Dahoo

Contoh:

```text
Kenapa proses ini menggunakan CPU tinggi?
```

## Langkah 6 — Ambil tindakan

Jika memang aman dan Anda memahami dampaknya, gunakan action yang tersedia.

## Langkah 7 — Verifikasi

Kembali ke Dashboard dan periksa apakah:

```text
CPU ↓
Temperature ↓
Memory ↓
Health ↑
```

---

# 🤖 Google Gemini / Cloud AI & Cara Kerja Dahoo Assistant

WISMON mengintegrasikan **Dahoo Assistant** dengan arsitektur hybrid yang menggabungkan model cloud **Google Gemini 3.8 Flash** (`gemini-3.8-flash`) dengan dukungan **End-to-End SSE Streaming** dan **Dahoo Local Intelligence Rule Engine**.

---

### 📌 Model Versi yang Digunakan: Gemini 3.8 Flash (`gemini-3.8-flash`)

WISMON secara terstandarisasi menggunakan **`gemini-3.8-flash`** sebagai model AI berbasis cloud. 

#### Keunggulan & Spesifikasi `gemini-3.8-flash`:
1. **End-to-End Server-Sent Events (SSE) Streaming**: Respon dihasilkan secara langsung dan bertahap ke antarmuka pengguna (`/api/dahoo/chat/stream`), mengeliminasi respon terpotong, waktu tunggu kaku, atau keharusan mengetik "lanjutkan".
2. **Ketersediaan & Kestabilan Tinggi**: Model `gemini-3.8-flash` merupakan model resmi Google Gemini yang tersedia luas pada akun Google AI Studio tanpa kendala kuota khusus atau pembatasan tier tertentu.
3. **Latensi Sangat Rendah & Respon Cepat**: Sebagai model kelas "Flash", inferensi berlangsung dalam hitungan detik, sangat cocok untuk asisten pemantauan sistem yang membutuhkan respon cepat saat terjadi insiden performa.
4. **Dukungan Native Reasoning (`ThinkingConfig`)**: Menggunakan parameter penalaran resmi Google GenAI SDK (`google-genai`) dengan level `low`, `medium` (default), dan `high` tanpa parameter sampling usang (`temperature`, `top_p`, `top_k`).
5. **Kapasitas Output Token Lega (`DAHOO_MAX_OUTPUT_TOKENS=2048`)**: Dahoo dapat memberikan analisis diagnosis dan rekomendasi troubleshooting lengkap tanpa batasan kalimat buatan yang kaku.
6. **Efisiensi & Transparansi Biaya Token**: Penghitungan token selaras dengan Google AI Studio, di mana *thinking tokens* dilaporkan secara transparan bersama *prompt tokens* dan *candidates tokens*, memberikan estimasi biaya yang presisi pada badge UI Dahoo.

---

### ⚙️ Cara Kerja Dahoo (End-to-End Pipeline)

Dahoo bekerja melalui pipeline 7 tahap terintegrasi yang menjamin keamanan sistem Windows, efisiensi bandwidth, dan keakuratan analisis:

```text
               ┌─────────────────────────────────────────────────────────┐
               │                Input Pengguna (Chat/Perintah)           │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │ 1. Intent Classification & Context Routing              │
               │    (CPU / RAM / Disk / Security / Network / General)    │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │ 2. Telemetry Sanitization & Prompt Injection Shield     │
               │    (Hanya metrik relevan yang disisipkan; teks OS aman) │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                               [GEMINI_API_KEY Aktif & Online?]
                                            │
                             ┌──────────────┴──────────────┐
                            YES                            NO
                             │                              │
                  ┌──────────▼──────────┐        ┌──────────▼──────────┐
                  │ 3. Gemini 3.8 Flash │        │ 3. Dahoo Local Rule │
                  │    SSE Stream Engine│        │    Intelligence     │
                  └──────────┬──────────┘        └──────────┬──────────┘
                             │ (Gagal / 503 / Offline)      │
                             └──────────────┬───────────────┘
                                            │ (Fallback Transparan)
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │ 4. Multi-Turn Session Memory (SQLite Persistence)       │
               │    (Menyimpan riwayat percakapan per session_id)        │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                               [Apakah Ada Aksi Remediasi?]
                                            │
                             ┌──────────────┴──────────────┐
                            YES                            NO
                             │                              │
                  ┌──────────▼──────────┐                   │
                  │ 5. Two-Phase Safe   │                   │
                  │    Action Proposal  │                   │
                  │    (TTL 60 Detik)   │                   │
                  └──────────┬──────────┘                   │
                             │                              │
                  [Konfirmasi Pengguna?]                    │
                             │                              │
                   ┌─────────┴─────────┐                    │
                  YES                 NO/Timeout            │
                   │                   │                    │
        ┌──────────▼──────────┐   ┌────▼───────────────┐    │
        │ 6. Strict Guardrail │   │ Aksi Dibatalkan /  │    │
        │    Check & Eksekusi │   │ Proposal Expired   │    │
        └──────────┬──────────┘   └────────────────────┘    │
                   │                                        │
                   ▼                                        │
        ┌─────────────────────┐                             │
        │ 7. Real-Time Metric │                             │
        │    Verification     │                             │
        │    (Before vs After)│                             │
        └──────────┬──────────┘                             │
                   │                                        │
                   └───────────────────┬────────────────────┘
                                       │
                                       ▼
               ┌─────────────────────────────────────────────────────────┐
               │         Output Jawaban & Laporan Status ke UI           │
               └─────────────────────────────────────────────────────────┘
```

#### 1. Klasifikasi Intent & Routing Konteks Telemetri (*Context Routing*)
Alih-alih membuang seluruh snapshot sistem (ribuan baris data proses, soket, layanan) ke dalam prompt yang menghabiskan 2.000–4.000+ token, Dahoo menganalisis intent pertanyaan terlebih dahulu:
- **CPU Intent**: Menyertakan ringkasan beban CPU, core count, dan Top 5 proses CPU tertinggi.
- **Memory Intent**: Menyertakan RAM total, terpakai, paged/non-paged pool, commit charge, dan Top 5 proses RAM terbesar.
- **Disk / Storage Intent**: Menyertakan status partisi drive, folder sampah cache, dan file besar.
- **Security Intent**: Menyertakan daftar anomali keamanan aktif dan proses yang memicu peringatan.
- **General Chat**: Hanya menyertakan status kesehatan umum sistem (*Health Score*), menghemat kuota token hingga 85% (hanya ~200–500 token).

#### 2. Sanitasi Telemetri & Perlindungan Prompt Injection
Data dari sistem operasi (seperti nama proses atau judul jendela) dapat berpotensi mengandung karakter berbahaya atau instruksi tersembunyi (*prompt injection*). Dahoo menyaring dan men-sanitasi seluruh string telemetri sebelum digabungkan ke system prompt.

#### 3. Arsitektur Hybrid & Failover Otomatis (Cloud + Local)
- **Mode Cloud (Gemini 3.5 Flash)**: Menggunakan SDK resmi Google GenAI (`google-genai`) dengan model `gemini-3.5-flash` dan `ThinkingConfig(thinking_level="medium")`. Otomatis menonaktifkan Automatic Function Calling (AFC) legacy untuk memastikan komunikasi stabil dan bebas dari peringatan deprecated.
- **Mode Local Intelligence (Offline Rule Engine)**: Jika API key belum dikonfigurasi, kuota habis, atau koneksi internet terputus, sistem secara instan dan mulus melakukan failover ke Local Rule Engine. Local Engine menganalisis metrik sistem menggunakan aturan heuristik bawaan tanpa jeda dan tanpa menampilkan pesan error ke pengguna.

#### 4. Memori Percakapan Multi-Turn (*Conversational Memory*)
Dahoo dilengkapi dengan manajemen sesi percakapan:
- Setiap tab atau pengguna diberikan `session_id` unik yang disimpan di `localStorage` browser.
- Riwayat percakapan disimpan secara persisten di database SQLite lokal (`dahoo_sessions` dan `dahoo_messages`).
- Konteks percakapan sebelumnya diumpankan kembali ke prompt (hingga 10 turn terakhir) sehingga pengguna dapat mengajukan pertanyaan lanjutan (contoh: *"Berapa RAM-nya?"* lalu dilanjutkan *"Proses mana yang paling banyak memakannya?"*).
- Pengguna dapat mereset konteks kapan saja melalui tombol **`🔄 Sesi Baru`**.

#### 5. Two-Phase Safe Agent Execution (*Human-in-the-Loop*)
Dahoo tidak pernah mematikan proses, menangguhkan layanan, atau membersihkan disk secara sepihak tanpa izin:
- **Fase 1 (Proposal)**: Jika Dahoo merekomendasikan tindakan mitigasi, Dahoo memancarkan objek `Action Proposal` terstruktur dengan batas waktu kedaluwarsa (**TTL 60 detik**). Di UI chat, muncul kartu interaktif dengan tombol **`[Konfirmasi Tindakan]`** dan **`[Batalkan]`**.
- **Fase 2 (Konfirmasi & Eksekusi)**: Tindakan hanya dijalankan jika pengguna secara sadar mengklik tombol konfirmasi sebelum batas waktu 60 detik habis. Token sekali pakai (*nonce-based token*) mencegah eksekusi ganda atau replay attack.

#### 6. Strict Guardrails & Perlindungan Endpoint Mutlak
Sebelum aksi apapun dieksekusi oleh backend, permintaan melewati lapisan pengaman wajib:
- **WISMON Self-Protection**: Server backend WISMON (`python.exe` / current PID) dilindungi secara mutlak dari operasi `kill`, `suspend`, atau `cooldown` untuk mencegah server mati atau UI membeku.
- **EDR & Antivirus Protection**: Agen keamanan seperti Bitdefender (`bdservicehost.exe`, `vsserv.exe`), Windows Defender (`msmpeng.exe`), dan produk keamanan lainnya diblokir dari terminasi demi menjaga integritas komputer.
- **Windows Kernel Protection**: Proses sistem inti (PID 0, PID 4 `System`, `smss.exe`, `csrss.exe`, dll.) diblokir dari intervensi agar tidak menyebabkan Blue Screen of Death (BSOD).
- **Validasi PID Ulang (*Re-assignment Protection*)**: Memverifikasi bahwa PID target masih memiliki nama proses dan waktu pembuatan (*create_time*) yang sama dengan saat proposal dibuat, mencegah terminasi proses baru yang kebetulan menggunakan PID daur ulang.

#### 7. Verifikasi Metrik Real-Time (Before vs After)
Setelah mitigasi selesai:
- Dahoo secara otomatis membaca kembali telemetri sistem secara riil.
- Menghitung delta perubahan performa (`cpu_before` vs `cpu_after`, `ram_before` vs `ram_after`).
- Melaporkan hasil konkret kepada pengguna, misalnya: *"Berhasil mengoptimalkan proses. Penggunaan RAM turun 450 MB dan CPU kembali normal di 12%."*

---

## Konfigurasi

Tambahkan konfigurasi berikut ke file `.env`:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.6-flash
GEMINI_THINKING_LEVEL=medium
```

Setelah `.env` diperbarui, restart server WISMON:

```powershell
python monitor.py
```

### Privasi Data Telemetri

Data telemetri hardware Windows diisolasi dan dirutekan secara lokal. Hanya ringkasan metrik mentah yang dikirim ke Gemini API untuk keperluan analisis sesi aktif. Tidak ada data pribadi atau konten file yang diunggah ke cloud.

---

# 🗄️ Database dan Retensi Data

Database lokal default berada di:

```text
database/monitoring.db
```

WISMON menggunakan SQLite untuk penyimpanan lokal.

Konfigurasi retention saat ini tersedia melalui:

```env
DETAILED_RETENTION_HOURS=24
AGGREGATED_RETENTION_DAYS=7
```

Ring buffer realtime digunakan untuk telemetry terbaru di memory.

### Reset database

Jika ingin mereset data lokal, hentikan WISMON terlebih dahulu sebelum mengubah atau menghapus database.

---

# 🔐 Hak Akses Administrator

WISMON dirancang agar monitoring dasar dapat dijalankan oleh user biasa.

Namun Windows dapat membatasi operasi tertentu terhadap process/service yang dilindungi.

Jika muncul:

```text
Access Denied
```

itu tidak otomatis berarti WISMON rusak.

Jangan menjalankan WISMON sebagai Administrator hanya untuk mengatasi semua masalah. Gunakan hak akses minimum yang diperlukan.

---

# 🛠️ Troubleshooting

## 1. `python is not recognized`

Coba:

```powershell
py --version
```

Jika tidak tersedia, install Python dan pastikan PATH/launcher tersedia.

---

## 2. `git is not recognized`

Install Git:

<https://git-scm.com/download/win>

Kemudian buka PowerShell baru.

---

## 3. `.venv\Scripts\Activate.ps1` gagal

Gunakan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

lalu:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Dependency gagal diinstall

Pastikan `.venv` aktif:

```powershell
python --version
python -m pip --version
```

Kemudian:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika tetap gagal, simpan pesan error lengkap dari terminal untuk debugging/issue.

---

## 5. Port 8080 sudah digunakan

Periksa:

```powershell
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
```

Anda juga dapat melihat process yang menggunakan port tersebut:

```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess
```

Alternatifnya, ubah `.env`:

```env
PORT=8081
```

Kemudian restart WISMON.

---

## 6. Browser tidak dapat membuka WISMON

Periksa apakah terminal masih menjalankan:

```powershell
python monitor.py
```

Pastikan tidak ada error seperti:

```text
Traceback
ImportError
ModuleNotFoundError
OSError
```

Kemudian coba:

```text
http://127.0.0.1:8080
```

---

## 7. Dashboard terbuka tetapi data tidak bergerak

Periksa status:

```text
LIVE
```

Jika `RECONNECTING` atau `OFFLINE`:

1. pastikan backend masih berjalan;
2. refresh browser;
3. periksa terminal;
4. pastikan port yang digunakan benar.

---

## 8. GPU tidak terdeteksi

Periksa:

- driver GPU,
- jenis GPU,
- dukungan counter/telemetry Windows,
- apakah hardware mengekspos metrik yang dibutuhkan.

---

## 9. Temperature tidak tersedia

Sensor temperature berbeda antar vendor/perangkat. Tidak semua Windows PC mengekspos telemetry yang dapat digunakan WISMON.

---

## 10. Dahoo Cloud AI tidak aktif

Periksa `.env`:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash
```

Kemudian restart:

```powershell
python monitor.py
```

Jika tidak ingin menggunakan Cloud AI, gunakan Local Intelligence.

---

## 11. Processes kosong

Periksa:

```text
Activity → Processes
```

Jika tidak muncul:

1. tunggu beberapa detik;
2. refresh halaman;
3. periksa terminal;
4. pastikan backend aktif.

---

# 🛡️ Catatan Keamanan

WISMON bukan aplikasi read-only. Beberapa fitur dapat melakukan tindakan terhadap sistem, termasuk:

- suspend process,
- terminate process,
- memory cleanup,
- file cleanup tertentu.

Karena itu:

- jangan menjalankan tindakan yang tidak Anda pahami;
- jangan menghentikan process Windows yang tidak Anda kenali;
- backup data penting;
- jangan membagikan API key;
- jangan membuka WISMON ke internet tanpa review keamanan terlebih dahulu;
- gunakan least privilege.

## Jangan menganggap WISMON sebagai antivirus

Security Events/anomaly detection adalah alat monitoring dan investigasi, bukan pengganti antivirus, EDR, atau endpoint security platform.

---

# ⚠️ Batasan WISMON

WISMON bergantung pada API dan telemetry yang tersedia pada sistem Windows dan hardware masing-masing perangkat.

Karena itu hasil dapat berbeda antar laptop/PC.

Contoh:

- GPU telemetry dapat berbeda.
- Temperature sensor dapat tidak tersedia.
- Beberapa process tidak dapat diakses.
- Protected process dapat menolak operasi.
- Hardware vendor dapat mengekspos telemetry yang berbeda.

WISMON sebaiknya dipahami sebagai:

> **Windows monitoring and troubleshooting tool**

bukan sumber kebenaran absolut untuk seluruh kondisi hardware/software.

---

# 🗂️ Struktur Project

```text
wismon/
├── backend/
│   ├── api/
│   ├── collectors/
│   ├── engine/
│   ├── config.py
│   ├── db.py
│   └── main.py
│
├── frontend/
│   ├── css/
│   ├── js/
│   └── index.html
│
├── database/
│   └── monitoring.db
│
├── monitor.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 👨‍💻 Untuk Developer

## Jalankan environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## Install dependency

```powershell
python -m pip install -r requirements.txt
```

## Jalankan server

```powershell
python monitor.py
```

## Frontend

Frontend menggunakan HTML/CSS/Vanilla JavaScript dan disajikan oleh backend. File `frontend/index.html` memuat controller halaman seperti Dashboard, CPU, Memory, Storage, Network, Processes, Services, Security, Hardware, dan Analysis.

## Konfigurasi

`backend/config.py` memuat konfigurasi environment seperti:

- HOST
- PORT
- monitoring intervals
- retention
- Gemini configuration

---

# 🧪 Checklist Setelah Instalasi

## Backend

```text
[ ] python monitor.py berjalan tanpa traceback
[ ] server dapat diakses
[ ] http://127.0.0.1:8080 terbuka
```

## Realtime

```text
[ ] status = LIVE
[ ] CPU berubah
[ ] Memory berubah
[ ] telemetry/chart menerima data
```

## Activity

```text
[ ] Processes dapat dibuka
[ ] process muncul
[ ] search/sort bekerja
```

## Dahoo

```text
[ ] Dahoo dapat dibuka
[ ] pertanyaan sederhana mendapat response
[ ] Local Intelligence bekerja tanpa Gemini
```

## Cloud AI (opsional)

```text
[ ] GEMINI_API_KEY terisi
[ ] GEMINI_MODEL terisi (default: gemini-3.5-flash)
[ ] Automatic Provider Routing aktif (● Gemini 3.5 Flash (Auto))
```

---

# ❓ FAQ

## Apakah WISMON perlu Node.js?

Tidak untuk menjalankan aplikasi sebagaimana struktur repository saat ini. Frontend disajikan oleh backend Python.

## Apakah harus memakai Administrator?

Tidak untuk monitoring dasar. Beberapa operasi terhadap process/service tertentu dapat memerlukan hak akses lebih tinggi atau tetap ditolak oleh Windows.

## Apakah Gemini wajib?

Tidak. Dahoo dapat digunakan dengan Local Intelligence.

## Apakah WISMON memakai MySQL/PostgreSQL?

Tidak. Database lokal menggunakan SQLite.

## Berapa port default?

```text
127.0.0.1:8080
```

## Bagaimana menghentikan WISMON?

Kembali ke terminal tempat WISMON berjalan dan tekan:

```text
Ctrl+C
```

---

# 📌 Catatan untuk Contributor

Sebelum membuat perubahan pada collector, engine, API, atau frontend, pertimbangkan:

- Apakah perubahan menambah beban CPU?
- Apakah perubahan menambah disk I/O?
- Apakah data dapat berasal dari sumber yang tidak dipercaya?
- Apakah output frontend dirender sebagai HTML?
- Apakah tindakan remediation membutuhkan confirmation?
- Apakah fitur tetap aman ketika permission Windows ditolak?
- Apakah error dikembalikan ke UI dengan pesan yang dapat dipahami pengguna?

Untuk perubahan UI, prioritaskan:

```text
Detect
  ↓
Explain
  ↓
Recommend
  ↓
Confirm
  ↓
Act
  ↓
Show Result
```

---

# 📄 Lisensi

Lihat file `LICENSE` pada repository untuk ketentuan lisensi project.

---

# 🔗 Repository

GitHub:

<https://github.com/Aiyub150/wismon>
