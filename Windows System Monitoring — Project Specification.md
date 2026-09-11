# Windows System Monitoring

## 1. Project Overview

**Windows System Monitoring** adalah aplikasi monitoring dan analysis untuk sistem operasi Windows yang dirancang untuk memberikan informasi sistem secara lebih mendalam dibandingkan Task Manager bawaan Windows.

Aplikasi tidak hanya menampilkan kondisi sistem secara real-time, tetapi juga:

- Mengumpulkan telemetry hardware dan operating system.
- Menampilkan penggunaan resource secara real-time.
- Menyimpan historical telemetry.
- Menganalisis pola penggunaan sistem.
- Mendeteksi anomaly.
- Mendeteksi indikasi aktivitas mencurigakan.
- Menganalisis proses, service, storage, dan network.
- Memberikan rekomendasi tindakan kepada pengguna.
- Membantu pengguna melalui assistant bernama **Dahoo**.
- Menyediakan pusat keamanan untuk melihat dan menangani event yang dianggap mencurigakan.

Tujuan utama project:

> **Observe → Understand → Analyze → Detect → Recommend → Act**

Project ini bukan sekadar Task Manager clone.

Task Manager menjawab:

> "Apa yang sedang digunakan oleh komputer?"

Windows System Monitoring harus mampu menjawab:

> "Apa yang sedang terjadi, mengapa terjadi, apakah normal, bagaimana polanya, dan apa yang sebaiknya dilakukan?"

---

# 2. Prinsip Utama Project

Semua implementasi harus mengikuti prinsip berikut.

## 2.1 Monitoring First

Data harus dikumpulkan terlebih dahulu sebelum melakukan analisis.

Jangan membuat analisis berdasarkan data dummy.

Semua informasi yang ditampilkan pada UI harus berasal dari:

- Windows API
- Performance Counter
- ETW
- WMI jika diperlukan
- IP Helper API
- Windows Service API
- File System
- Storage/NVMe telemetry
- Network API
- Process API
- sumber telemetry Windows lainnya yang relevan

---

## 2.2 Real-Time

Data monitoring utama harus dapat diperbarui secara real-time atau near-real-time.

UI tidak boleh membutuhkan refresh browser secara manual.

Gunakan mekanisme streaming seperti:

- Server-Sent Events (SSE)
- WebSocket
- IPC

Pemilihan teknologi harus mempertimbangkan konsumsi CPU, RAM, latency, dan kompleksitas.

---

## 2.3 Historical Data

Monitoring tidak hanya digunakan untuk melihat kondisi saat ini.

Data penting harus disimpan agar aplikasi dapat melakukan:

- trend analysis
- historical comparison
- anomaly detection
- usage statistics
- recommendation
- report

---

## 2.4 Lightweight

Aplikasi monitoring tidak boleh menjadi sumber masalah performa komputer.

Collector harus dirancang agar:

- penggunaan CPU rendah
- penggunaan RAM terkendali
- disk write tidak berlebihan
- database tidak ditulis setiap event secara individual jika tidak diperlukan
- polling interval dapat disesuaikan
- data dapat di-buffer
- data historis dapat di-retention/cleanup

Prioritas:

> Monitoring harus memberikan insight tanpa membebani sistem yang sedang dimonitor.

---

## 2.5 No Fake Data

Jangan menggunakan:

- dummy CPU percentage
- dummy temperature
- dummy network traffic
- dummy process
- dummy socket
- dummy threat
- dummy service
- dummy storage statistics

Jika sebuah metric belum dapat diperoleh dari Windows, tampilkan:

> `Unavailable`

atau:

> `Not supported`

Jangan mengarang nilai.

---

# 3. UI / UX REQUIREMENT

## 3.1 Tidak menggunakan Gentelella sebagai constraint

Project **tidak lagi bergantung pada template Gentelella**.

Gentelella boleh dihapus dari project apabila tidak diperlukan.

AI tidak boleh menganggap template lama sebagai struktur UI yang harus dipertahankan.

UI harus dibuat berdasarkan kebutuhan aplikasi ini.

Developer/AI memiliki kebebasan untuk membuat:

- layout
- sidebar
- topbar
- cards
- charts
- tables
- modal
- drawer
- notification
- command palette
- responsive layout
- dark/light theme
- component system

selama tetap sesuai dengan requirement project.

---

# 4. Struktur Navigasi Utama

Sidebar harus merepresentasikan fitur sebenarnya.

Jangan membuat sidebar berdasarkan halaman demo template.

Struktur yang direkomendasikan:

```text
SYSTEM MONITORING
│
├── Overview
│   └── Dashboard
│
├── System
│   ├── CPU
│   ├── Memory
│   ├── Storage
│   └── Network
│
├── Activity
│   ├── Processes
│   ├── Services
│   └── Connections
│
├── Security
│   ├── Threat Center
│   ├── Security Events
│   └── Mitigation
│
├── Hardware
│   ├── Temperature
│   ├── GPU
│   ├── Battery
│   └── System Information
│
├── Analysis
│   ├── Performance Analysis
│   ├── Storage Analyzer
│   ├── Network Analysis
│   └── Historical Data
│
└── Assistant
    └── Dahoo
```

Jika sebuah fitur belum diimplementasikan, jangan membuat halaman palsu hanya untuk memenuhi menu.

---

# 5. Dashboard

Dashboard merupakan halaman utama.

Tujuannya adalah memberikan gambaran kesehatan komputer dalam beberapa detik.

## Dashboard harus menampilkan:

### System Health

```text
SYSTEM HEALTH

● Healthy

CPU        32%
Memory     47%
Storage    62%
Network    Normal
Threats    0
```

Status dapat berupa:

- Healthy
- Normal
- Warning
- Critical

Status harus dihitung berdasarkan telemetry aktual.

---

## KPI Cards

Minimal:

1. CPU Usage
2. Memory Usage
3. Storage Usage
4. CPU Temperature
5. GPU Usage
6. GPU Temperature
7. Network Throughput
8. Active Threats

Tidak harus semuanya berada dalam satu baris.

Layout harus mempertimbangkan readability.

---

# 6. CPU Monitoring

Halaman CPU harus menampilkan:

## Real-Time

- Total CPU usage
- Per-core usage
- CPU frequency
- Base frequency jika tersedia
- Current frequency
- Logical processors
- Physical cores
- Processor name
- Temperature jika tersedia
- Power information jika tersedia

## Historical

Grafik:

- CPU usage
- CPU frequency
- temperature

User dapat memilih periode:

- 1 minute
- 5 minutes
- 30 minutes
- 1 hour
- 6 hours
- 24 hours
- custom

## Analysis

Contoh:

```text
CPU ANALYSIS

Current Usage       87%
Baseline            25–40%
Duration > 80%      18 minutes

Analysis:
CPU usage is significantly higher than the normal
baseline for this system.

Primary contributor:
python.exe

Recommendation:
Review the active Python process and its workload.
```

---

# 7. GPU Monitoring

GPU monitoring harus mendukung hardware yang tersedia.

Data yang dapat ditampilkan:

- GPU name
- GPU usage
- VRAM usage
- VRAM total
- GPU temperature
- GPU clock
- memory clock
- power usage jika tersedia
- process using GPU jika tersedia

Jika metric tertentu tidak tersedia pada hardware/driver:

```text
Not available on this system
```

Jangan membuat nilai estimasi palsu.

---

# 8. Memory Monitoring

Memory monitoring harus lebih dalam dibandingkan Task Manager biasa.

## Basic

- Total RAM
- Used RAM
- Available RAM
- Free RAM
- Cached RAM
- Memory percentage

## Deep Memory

- Paged Pool
- Non-Paged Pool
- Commit Charge
- Commit Limit
- Working Set
- Private Working Set
- Shareable Working Set
- Standby Cache jika dapat diperoleh

## Analysis

Sistem dapat mendeteksi:

- unusually high memory usage
- continuously increasing memory usage
- potential memory leak
- high non-paged pool
- high commit charge
- memory pressure

Contoh:

```text
MEMORY ANALYSIS

Memory usage increased from 42% → 81%
during the last 45 minutes.

Potential issue:
A process has continuously increased its
working set.

Recommended action:
Inspect process memory usage.
```

---

# 9. Process Explorer

Halaman Processes harus menjadi salah satu fitur utama.

Tampilkan:

- PID
- Process name
- Executable path
- CPU %
- Memory
- GPU %
- Threads
- Handles
- Disk I/O
- Network activity
- Start time
- User/account
- Process state

User dapat melakukan:

- sort
- filter
- search
- inspect
- melihat historical resource usage

Process detail:

```text
PROCESS DETAIL

Name
PID
Path
User
Started

CPU
Memory
Threads
Handles

Disk I/O
Network

Connections
Services
```

---

# 10. Windows Services

Windows Services harus dianalisis lebih dalam daripada daftar service biasa.

## Informasi

- Service name
- Display name
- PID
- Status
- Startup type
- Account
- Binary path
- Dependencies
- Recovery configuration

## svchost analysis

Jika service berada di dalam:

```text
svchost.exe
```

sistem harus mencoba mengidentifikasi service yang berjalan di dalam process tersebut.

Tampilkan hubungan:

```text
svchost.exe
PID 1240
│
├── Service A
├── Service B
└── Service C
```

Jika informasi tidak dapat diperoleh secara reliable:

```text
Service mapping unavailable
```

Jangan membuat asumsi.

---

# 11. Storage Monitoring

Storage tidak hanya menampilkan kapasitas disk.

## Basic

- Drive
- Total capacity
- Used
- Free
- Usage %
- File system

## I/O

- Read bytes/sec
- Write bytes/sec
- Read operations
- Write operations
- Queue depth
- Response time / latency

## Per Process

- Read bytes
- Write bytes
- I/O operations

## Drive Health

Jika hardware mendukung:

- temperature
- health
- wear level
- SMART information
- NVMe telemetry

Jika informasi tidak tersedia:

```text
Drive telemetry unavailable
```

---

# 12. Storage Analyzer

Storage Analyzer merupakan fitur analisis.

Tujuan:

> Membantu user menemukan file yang mungkin menggunakan storage secara tidak efisien.

Analisis:

- Large files
- Old files
- Temporary files
- Duplicate files
- Downloads
- Cache
- Application data
- File type distribution

Contoh:

```text
STORAGE INSIGHT

Large files
────────────────
video.mp4       12.4 GB
backup.zip       8.1 GB
dataset.zip      6.7 GB

Potential cleanup
────────────────
Temporary files  2.1 GB
Old downloads    4.8 GB
```

## Important Safety Rule

Jangan menghapus file secara otomatis.

Sistem hanya memberikan rekomendasi.

User harus melakukan konfirmasi.

```text
[Review] [Delete]
```

File sistem penting tidak boleh direkomendasikan untuk penghapusan hanya berdasarkan umur/ukuran.

---

# 13. Network Monitoring

Network merupakan salah satu modul paling penting.

## Interface Information

Tampilkan:

- Interface
- Interface type
- SSID
- IPv4
- IPv6
- MAC address
- Gateway
- DNS
- Connection status
- Link speed jika tersedia

Contoh:

```text
NETWORK

Wi-Fi
SSID       MyWiFi
IPv4       192.168.1.15
IPv6       xxxx::xxxx
MAC        XX:XX:XX:XX:XX:XX
Gateway    192.168.1.1
Status     Connected
```

---

# 14. Network Traffic

Monitor:

- Download
- Upload
- Packets
- Connections
- Traffic over time

Grafik real-time:

```text
Network Traffic

Mbps
│
│       ╭──╮
│   ╭───╯  ╰───╮
│───╯          ╰──
└──────────────────
       Time
```

---

# 15. Network Connections / Socket Explorer

Gunakan Windows IP Helper API atau API Windows lain yang sesuai.

Informasi:

- Protocol
- Local IP
- Local Port
- Remote IP
- Remote Port
- State
- PID
- Process name
- Process path
- Remote hostname
- Connection duration
- Bytes sent
- Bytes received

Contoh:

```text
TCP

PID     Process
4812    node.exe

Local
192.168.1.15:52314

Remote
104.26.10.23:443

Host
api.github.com

State
ESTABLISHED

Traffic
↓ 8.9 KB
↑ 1.4 KB
```

---

# 16. Reverse DNS

Remote IP dapat dicoba untuk di-resolve menjadi hostname.

Namun:

- DNS lookup tidak boleh memblokir collector.
- Gunakan asynchronous lookup.
- Gunakan cache.
- Jika gagal, tampilkan IP saja.

Contoh:

```text
104.26.10.23
api.github.com
```

atau:

```text
104.26.10.23
Hostname unavailable
```

---

# 17. Network Analysis

Network Analysis harus menganalisis pola, bukan langsung menyatakan sesuatu sebagai serangan.

Contoh event:

```text
NETWORK ANOMALY

A process has created an unusually high
number of outbound connections.

Process:
unknown.exe

Connections:
184

Baseline:
12–30

Severity:
WARNING
```

Analisis dapat mempertimbangkan:

- connection frequency
- destination diversity
- unusual ports
- repeated failed connections
- connection spikes
- unusual process behavior
- traffic volume
- historical baseline

Jangan menyebut aktivitas sebagai:

> "Malware detected"

hanya berdasarkan satu indikator.

Gunakan istilah:

- Suspicious
- Anomalous
- Potential threat
- Investigation recommended

kecuali terdapat bukti kuat.

---

# 18. Security / Threat Center

Threat Center merupakan pusat keamanan aplikasi.

Kategori threat/event:

- High CPU process
- High memory process
- Suspicious process
- Unusual network activity
- Suspicious connection
- Service anomaly
- Storage anomaly
- Other system anomaly

Severity:

```text
INFO
WARNING
HIGH
CRITICAL
```

Setiap event memiliki:

```text
Timestamp
Category
Severity
Source
Target
Reason
Evidence
Status
Recommended Action
```

---

# 19. Threat Lifecycle

Setiap threat harus mempunyai lifecycle.

```text
Detected
   ↓
Analyzing
   ↓
Confirmed / Suspicious / False Positive
   ↓
Mitigation Recommended
   ↓
User Action
   ↓
Resolved
```

Jangan langsung melakukan tindakan berbahaya secara otomatis.

---

# 20. Mitigation Controller

Jika implementasi memungkinkan, sistem dapat memberikan tindakan seperti:

- Terminate process
- Stop service
- Block IP
- Quarantine file

Namun semua tindakan berisiko tinggi harus:

1. Menampilkan target.
2. Menjelaskan alasan.
3. Meminta konfirmasi user.
4. Mencatat tindakan.
5. Menampilkan hasil tindakan.

Contoh:

```text
WARNING

Process:
example.exe

Reason:
Unusual CPU and network activity.

Recommended:
Terminate process

[Cancel] [Terminate]
```

---

# 21. Historical Analysis

Sistem harus menyimpan telemetry penting.

User dapat melihat:

- CPU history
- RAM history
- GPU history
- Storage history
- Network history
- Threat history

Contoh:

```text
LAST 24 HOURS

CPU Average       31%
RAM Average       54%
Network Peak      82 Mbps
Threat Events     3
```

---

# 22. Baseline System

Aplikasi harus dapat membangun baseline.

Contoh:

```text
NORMAL BASELINE

CPU
20–45%

RAM
35–65%

Network
0.5–8 Mbps

Connections
15–40
```

Baseline dapat digunakan untuk anomaly detection.

Jangan langsung menggunakan machine learning jika rule/statistical analysis sudah cukup.

---

# 23. Analysis Engine

Gunakan beberapa tingkat analysis.

## Level 1 — Threshold

Contoh:

```text
CPU > 90%
RAM > 90%
Disk > 95%
```

## Level 2 — Duration

Contoh:

```text
CPU > 90% for 10 minutes
```

lebih relevan dibanding:

```text
CPU > 90% once
```

## Level 3 — Historical Baseline

Bandingkan kondisi sekarang dengan kondisi normal komputer.

## Level 4 — Correlation

Contoh:

```text
CPU ↑
Network ↑
Process X ↑
```

Kemungkinan event lebih signifikan daripada hanya satu metric.

## Level 5 — Prediction

Jika data historis cukup, sistem dapat melakukan prediksi:

```text
Storage is increasing approximately
8.2 GB/week.

Estimated time until 90% capacity:
14 days
```

Prediksi harus memiliki confidence/indikasi ketidakpastian.

---

# 24. Dahoo Assistant

Dahoo adalah assistant pendamping pengguna.

Dahoo bukan hanya chatbot biasa.

Dahoo harus dapat:

- Menjelaskan kondisi sistem.
- Menjawab pertanyaan user.
- Menjelaskan metric.
- Menjelaskan threat.
- Memberikan rekomendasi.
- Memberikan konteks terhadap event.
- Memberitahu user ketika terdapat event penting.

Contoh:

```text
Dahoo:

"Aww... CPU kamu sedang cukup tinggi.
Saat ini penggunaan CPU 91%.

Process yang paling banyak menggunakan CPU:
python.exe — 67%.

Kalau kamu tidak sedang menjalankan proses berat,
sebaiknya kita periksa process tersebut."
```

---

# 25. Dahoo UI

Dahoo selalu tersedia di aplikasi.

Bentuk:

- floating mascot
- chat drawer/panel
- notification bubble
- contextual suggestion

Dahoo memiliki ekspresi:

```text
happy
normal
worried
alert
sleeping
thinking
```

Ekspresi ditentukan berdasarkan system state.

---

# 26. Dahoo Interaction

Dahoo dapat memiliki interaksi ringan:

- suara "aww"
- mouse proximity
- dodge animation
- idle animation
- expression changes

Namun animasi tidak boleh menggunakan CPU secara berlebihan.

Prioritas tetap:

> Monitoring performance > animation.

---

# 27. Dahoo AI Architecture

Dahoo menggunakan pendekatan **Hybrid Assistant**.

```text
                 User Question
                       │
                       ▼
                Dahoo Router
                  /       \
                 /         \
        Local Engine      Cloud AI
             │                │
             ▼                ▼
        Rule/Context       LLM
        Analysis           Reasoning
             │                │
             └───────┬────────┘
                     ▼
                Dahoo Response
```

## Local Engine

Digunakan untuk pertanyaan yang dapat dijawab langsung berdasarkan telemetry.

Contoh:

- CPU berapa?
- RAM berapa?
- kondisi sistem?
- process tertinggi?
- berapa threat aktif?

Keuntungan:

- offline
- 0 token
- cepat
- murah

## Cloud AI

Digunakan ketika user membutuhkan:

- penjelasan natural language
- analisis kompleks
- troubleshooting
- contextual reasoning

Model AI harus dikonfigurasi melalui environment variable.

Jangan menyimpan API key di source code.

---

# 28. AI Cost Transparency

Jika cloud AI digunakan, simpan:

- model
- request timestamp
- input tokens
- output tokens
- total tokens
- estimated cost

UI Dahoo harus menyediakan:

```text
AI MODEL

Provider
Model
Input Tokens
Output Tokens
Total Tokens
Estimated Cost
```

Cost harus menggunakan pricing yang dikonfigurasi, bukan hardcoded tanpa dokumentasi.

Jika pricing berubah, konfigurasi harus mudah diperbarui.

---

# 29. API Key Security

API key:

- tidak boleh berada di Git repository
- tidak boleh berada di Markdown specification
- tidak boleh di-hardcode
- tidak boleh dikirim ke frontend
- tidak boleh ditampilkan di UI
- gunakan `.env`
- `.env` harus masuk `.gitignore`

Contoh:

```env
GEMINI_API_KEY=your_key_here
```

Repository hanya boleh memiliki:

```text
.env.example
```

---

# 30. Database

Gunakan:

```text
SQLite
```

Database:

```text
database/
└── monitoring.db
```

Gunakan WAL jika sesuai.

Gunakan buffered/batched writes untuk telemetry berfrekuensi tinggi.

---

# 31. Database Tables

Minimal:

## system_info

Menyimpan:

- timestamp
- CPU
- RAM
- paged pool
- non-paged pool
- commit charge
- commit limit
- disk metrics
- network metrics

## process

Menyimpan:

- timestamp
- PID
- process name
- path
- CPU
- memory
- threads
- handles
- I/O

## socket

Menyimpan:

- timestamp
- protocol
- local endpoint
- remote endpoint
- hostname
- PID
- process
- state
- bytes sent
- bytes received
- duration

## service

Menyimpan:

- service name
- display name
- PID
- status
- startup mode
- account
- binary path
- dependencies

## threat

Menyimpan:

- timestamp
- category
- severity
- target
- reason
- evidence
- status
- mitigation action

## dahoo

Menyimpan:

- timestamp
- user message
- response
- model
- input tokens
- output tokens
- total cost
- proactive alert status

---

# 32. Data Retention

Telemetry tidak boleh disimpan selamanya tanpa batas.

Sediakan retention policy.

Contoh:

```text
Realtime buffer
60–300 samples

Detailed telemetry
24 hours

Aggregated telemetry
7–30 days

Threat history
Long-term
```

Retention harus dapat dikonfigurasi.

---

# 33. Architecture

Recommended architecture:

```text
┌──────────────────────────────────────┐
│               Windows                │
│                                      │
│ Hardware / Kernel / Network / Files  │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│            Collector Layer            │
│                                      │
│ CPU                                  │
│ Memory                               │
│ GPU                                  │
│ Storage                              │
│ Network                              │
│ Process                              │
│ Services                             │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│          Monitoring Engine            │
│                                      │
│ Normalization                        │
│ Aggregation                          │
│ Buffering                            │
│ Event Processing                     │
└───────────────────┬──────────────────┘
                    │
             ┌──────┴──────┐
             ▼             ▼
┌──────────────────┐ ┌─────────────────┐
│ SQLite           │ │ Analysis Engine │
│ Historical Data  │ │ Baseline        │
└──────────────────┘ │ Anomaly         │
                     │ Threat          │
                     │ Recommendation  │
                     └────────┬────────┘
                              │
                              ▼
┌──────────────────────────────────────┐
│                 API                  │
│                                      │
│ REST / SSE / WebSocket / IPC         │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│               Frontend               │
│                                      │
│ Dashboard                            │
│ CPU                                  │
│ Memory                               │
│ Storage                              │
│ Network                              │
│ Processes                            │
│ Services                             │
│ Threat Center                        │
│ Analysis                             │
│ Dahoo                                │
└──────────────────────────────────────┘
```

---

# 34. Recommended Technology

Technology dapat dipilih berdasarkan kebutuhan implementasi.

## Backend

Prioritas:

```text
Python / C# / Rust
```

Untuk Windows low-level monitoring, C# atau Rust dapat dipertimbangkan.

Python tetap dapat digunakan jika kebutuhan native API dapat dipenuhi dengan baik.

## Frontend

Boleh menggunakan:

```text
React
Vue
Svelte
Vanilla JS
```

Pilih berdasarkan kompleksitas dan maintainability.

## Database

```text
SQLite
```

## Charts

Gunakan library chart yang ringan dan mendukung real-time update.

---

# 35. Collector Design

Collector harus modular.

Contoh:

```text
collectors/
├── cpu.py
├── memory.py
├── gpu.py
├── storage.py
├── network.py
├── process.py
├── services.py
└── temperature.py
```

Jangan membuat satu collector besar yang menangani semua hal.

---

# 36. Monitoring Intervals

Tidak semua metric harus dikumpulkan dengan interval sama.

Contoh:

```text
CPU              1 sec
RAM              1 sec
Network          1 sec
Process          1–2 sec
GPU              1 sec
Storage I/O      1 sec
Sockets          2–5 sec
Services         5–10 sec
SMART            30–60 sec
File Analysis    On demand
```

Interval dapat disesuaikan berdasarkan cost.

---

# 37. Error Handling

Jika collector gagal:

Jangan membuat seluruh aplikasi berhenti.

Contoh:

```text
GPU temperature unavailable
```

bukan:

```text
Application crashed
```

Collector harus memiliki isolation.

```text
CPU Collector
      │
      ├── success
      │
      └── failure → log + continue
```

---

# 38. Logging

Gunakan structured logging.

Minimal:

```text
INFO
WARNING
ERROR
DEBUG
```

Log harus membantu developer melakukan troubleshooting.

Jangan memasukkan:

- API key
- password
- credential
- sensitive data

ke log.

---

# 39. Frontend Design Philosophy

UI harus:

- modern
- clean
- professional
- readable
- responsive
- information dense tetapi tidak membingungkan
- cocok untuk monitoring dashboard

Prioritas visual:

```text
System Status
      ↓
Important Metrics
      ↓
Trend
      ↓
Detailed Information
      ↓
Analysis
      ↓
Action
```

---

# 40. Sidebar Behavior

Sidebar harus selalu menunjukkan struktur fitur aplikasi.

Contoh:

```text
┌─────────────────────────┐
│ 🖥 System Monitoring    │
├─────────────────────────┤
│ OVERVIEW                │
│  Dashboard              │
│                         │
│ SYSTEM                  │
│  CPU                    │
│  Memory                 │
│  Storage                │
│  Network                │
│                         │
│ ACTIVITY                │
│  Processes              │
│  Services               │
│  Connections            │
│                         │
│ SECURITY                │
│  Threat Center          │
│  Security Events        │
│                         │
│ HARDWARE                │
│  GPU                    │
│  Temperature            │
│  Battery                │
│  System Information     │
│                         │
│ ANALYSIS                │
│  Performance            │
│  Storage Analyzer       │
│  Network Analysis       │
│  History                │
│                         │
│ ASSISTANT               │
│  Dahoo                  │
└─────────────────────────┘
```

Menu tersebut bukan contoh dekorasi.

**Setiap menu harus mempunyai fungsi nyata.**

---

# 41. Topbar

Topbar dapat berisi:

```text
System Monitoring

[ Search ]

System Status: ● Online

[Notifications]

[Dahoo]

[Settings]
```

Search dapat mencari:

- process
- service
- socket
- threat
- setting
- page

---

# 42. Notification System

Notification harus digunakan untuk event penting.

Contoh:

```text
⚠ High CPU

python.exe has used >90% CPU
for 12 minutes.

[View Process]
```

atau:

```text
🔴 Suspicious Network Activity

A process created 180 outbound
connections within 2 minutes.

[Investigate]
```

Jangan menampilkan notification untuk setiap metric normal.

---

# 43. Responsive Design

UI harus tetap usable pada:

- laptop
- desktop
- window kecil

Sidebar dapat berubah menjadi:

```text
Expanded
    ↓
Collapsed
    ↓
Mobile drawer
```

---

# 44. Accessibility

Perhatikan:

- readable text
- contrast
- keyboard navigation
- tooltips
- meaningful labels
- tidak hanya menggunakan warna untuk menunjukkan status

Contoh:

Jangan:

```text
🔴
```

saja.

Gunakan:

```text
🔴 CRITICAL
```

---

# 45. Security Principles

System monitoring memiliki akses sensitif terhadap Windows.

Karena itu:

- jangan meminta administrator privilege jika tidak diperlukan
- gunakan least privilege
- tindakan destructive membutuhkan confirmation
- jangan menjalankan command arbitrary dari frontend
- validasi semua input
- jangan percaya data dari process/network
- sanitasi path
- jangan expose local API ke public network tanpa alasan

---

# 46. Project Startup

Gunakan satu entry point sederhana:

```bash
python monitor.py
```

Script tersebut bertanggung jawab untuk menjalankan komponen aplikasi yang diperlukan.

Startup harus memberikan informasi yang jelas:

```text
=======================================
 Windows System Monitoring
=======================================

Backend : http://localhost:8080
Frontend: http://localhost:9173

Monitoring: ONLINE

CPU     : 24%
Memory  : 47%
Threats : 0

Press Ctrl+C to stop.
```

Jika startup gagal, tampilkan alasan yang jelas.

---

# 47. README

README.md harus selalu diperbarui.

README minimal menjelaskan:

- Project overview
- Features
- Architecture
- Requirements
- Installation
- Configuration
- API key configuration
- Database
- Running application
- Troubleshooting
- Security
- Development
- License

README harus mencerminkan kondisi aplikasi yang sebenarnya.

---

# 48. Git

Jangan commit:

```text
.env
*.db
temporary logs
cache
API keys
credentials
```

Markdown specification internal dapat dikecualikan dari repository jika memang tidak diperlukan.

Namun:

```text
README.md
```

harus tetap tersedia.

---

# 49. Development Rules untuk AI Coding Agent

AI yang mengerjakan project ini harus mengikuti aturan berikut.

## Rule 1

Jangan membuat fitur berdasarkan asumsi.

Jika requirement tidak jelas, gunakan implementasi paling sederhana dan aman atau tandai sebagai TODO.

## Rule 2

Jangan menggunakan dummy telemetry.

## Rule 3

Jangan mengubah arsitektur besar tanpa alasan.

## Rule 4

Jangan menghapus fitur yang sudah bekerja tanpa alasan.

## Rule 5

Setiap perubahan backend harus dipastikan tidak merusak frontend.

## Rule 6

Setiap perubahan database harus mempertimbangkan migration/backward compatibility.

## Rule 7

Setiap collector harus fail-safe.

## Rule 8

Optimasi adalah requirement utama.

## Rule 9

Jangan menambahkan library besar jika fitur dapat dilakukan dengan dependency yang sudah tersedia.

## Rule 10

Jangan menambahkan fitur hanya karena terlihat menarik.

Fitur harus memberikan nilai nyata.

---

# 50. UI Development Rule

**Jangan menggunakan template admin sebagai batasan desain.**

Jika menggunakan template/library UI:

> Template adalah sumber komponen, bukan sumber requirement.

Requirement ditentukan oleh:

```text
Project Specification
       ↓
Feature
       ↓
User Workflow
       ↓
UI
```

Bukan:

```text
Template
       ↓
Cari fitur yang cocok
       ↓
Paksa fitur masuk template
```

---

# 51. Feature-to-Page Mapping

Setiap fitur harus memiliki halaman yang jelas.

| Feature | Page |
|---|---|
| CPU | CPU |
| RAM | Memory |
| GPU | GPU |
| Storage | Storage |
| File analysis | Storage Analyzer |
| Network | Network |
| Socket | Connections |
| Process | Processes |
| Windows Service | Services |
| Threat | Threat Center |
| Historical telemetry | History |
| Performance analysis | Performance |
| Network analysis | Network Analysis |
| Dahoo | Assistant |

Jika satu halaman menjadi terlalu kompleks, pecah menjadi subpage.

---

# 52. Dashboard-to-Detail Workflow

User harus dapat berpindah dari summary ke detail.

Contoh:

```text
Dashboard
   │
   ├── CPU 91%
   │       │
   │       └── View CPU
   │               │
   │               └── Top Process
   │                       │
   │                       └── Process Detail
   │
   └── Threat Detected
           │
           └── Threat Center
                   │
                   └── Process Detail
```

Dashboard bukan endpoint.

Dashboard harus menjadi titik masuk ke investigasi.

---

# 53. Example User Workflow

## Scenario: Laptop terasa lambat

User membuka:

```text
Dashboard
```

Sistem menunjukkan:

```text
System Health: WARNING

CPU: 94%
RAM: 83%
Disk: 91%
```

User klik:

```text
CPU
```

Kemudian:

```text
Top Process

python.exe
CPU 71%
```

User membuka process detail.

Dahoo memberikan:

```text
CPU usage is unusually high.

python.exe is responsible for approximately
71% of current CPU utilization.

Would you like to inspect this process?
```

Ini adalah workflow yang diharapkan.

---

# 54. Example Storage Workflow

User melihat:

```text
Storage
C:
82% used
```

Klik:

```text
Storage Analyzer
```

Sistem menemukan:

```text
Large Files       34 GB
Old Files         21 GB
Duplicates        8 GB
Temporary         3 GB
```

User memilih:

```text
Large Files
```

Kemudian sistem menampilkan file.

Tidak langsung menghapus.

---

# 55. Example Security Workflow

Network Analysis mendeteksi:

```text
Potentially unusual traffic
```

Threat Center menerima event:

```text
WARNING
Unusual outbound connection pattern
```

Dahoo:

```text
"Aww... aku menemukan pola koneksi yang
berbeda dari kebiasaan sistem.

Process:
example.exe

Connections:
183

Biasanya:
10–30

Sebaiknya kita periksa process ini."
```

User dapat:

```text
[Investigate]
```

bukan langsung:

```text
[Kill]
```

---

# 56. MVP

Versi pertama tidak perlu mengimplementasikan semuanya.

MVP:

```text
Dashboard
├── CPU
├── RAM
├── Storage
├── Network
├── Process
├── Basic Temperature
└── Dahoo Local Engine
```

Kemudian:

```text
Phase 2
├── GPU
├── Deep Memory
├── Services
├── Socket Explorer
└── Historical Data
```

Kemudian:

```text
Phase 3
├── Storage Analyzer
├── Network Analysis
├── Threat Center
└── Mitigation
```

Kemudian:

```text
Phase 4
├── Baseline
├── Anomaly Detection
├── Prediction
└── Cloud AI Dahoo
```

---

# 57. Future AI/ML

AI/ML tidak wajib pada versi pertama.

Prioritas:

```text
Telemetry
   ↓
Rules
   ↓
Statistics
   ↓
Baseline
   ↓
Anomaly Detection
   ↓
Machine Learning
```

Jangan menggunakan neural network hanya untuk mendeteksi:

```text
CPU > 90%
```

Rule sederhana lebih tepat.

ML digunakan jika terdapat problem yang memang membutuhkan model.

Contoh:

- anomaly detection
- workload prediction
- storage growth prediction
- behavioral baseline
- unusual network behavior

---

# 58. Definition of Done

Sebuah fitur dianggap selesai jika:

1. Backend collector bekerja.
2. Data berasal dari Windows sebenarnya.
3. Data tervalidasi.
4. API/stream bekerja.
5. UI menampilkan data.
6. Loading/error state tersedia.
7. Tidak menggunakan dummy data.
8. Tidak menyebabkan crash ketika collector gagal.
9. Konsumsi resource masih wajar.
10. Dokumentasi diperbarui.
11. Feature dapat diuji secara manual.

---

# 59. Final Product Vision

Pada akhirnya aplikasi harus terasa seperti:

```text
              WINDOWS SYSTEM MONITORING

                         ┌─────────────┐
                         │   HEALTH    │
                         │    82/100   │
                         └──────┬──────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
        CPU                   MEMORY               STORAGE
         31%                    48%                  72%
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                         SYSTEM ANALYSIS
                                │
                ┌───────────────┼───────────────┐
                │               │               │
             Process         Network          Security
                │               │               │
                └───────────────┼───────────────┘
                                │
                              DAHOO
                                │
                       "How can I help?"
```

Tujuan akhirnya bukan sekadar:

> "Menampilkan angka."

Tetapi:

> **Collect → Visualize → Understand → Analyze → Detect → Recommend**

---

# 60. Instruksi Final untuk AI Coding Agent

Sebelum melakukan perubahan pada project:

1. Baca `README.md`.
2. Baca specification project ini.
3. Periksa struktur project aktual.
4. Identifikasi fitur yang sudah benar-benar bekerja.
5. Jangan menganggap fitur hanya ada karena tertulis di dokumentasi.
6. Verifikasi backend dan frontend.
7. Jangan menggunakan dummy data.
8. Jangan mempertahankan template UI lama hanya karena template tersebut pernah digunakan.
9. UI harus mengikuti feature requirement pada specification ini.
10. Jangan membuat halaman yang tidak memiliki fungsi nyata.
11. Jangan menghapus data atau file penting tanpa alasan.
12. Jangan mengubah API key atau credential menjadi hardcoded.
13. Gunakan environment variable untuk secret.
14. Setelah perubahan, lakukan testing.
15. Perbarui README jika behavior aplikasi berubah.

## Prioritas ketika terdapat konflik

Gunakan urutan berikut:

```text
1. Security
2. Correctness
3. Real Windows Telemetry
4. Stability
5. Performance / Resource Efficiency
6. User Experience
7. Visual Design
8. Convenience
```

Jangan mengorbankan correctness demi visual.

Jangan mengorbankan performance demi animation.

Jangan mengorbankan security demi convenience.

---

# END OF SPECIFICATION