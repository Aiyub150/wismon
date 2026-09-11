# Hasil Pengujian dan Feedback WISMON

Dokumen ini berisi hasil pengujian terhadap project **WISMON**, meliputi pengujian UI/UX, sinkronisasi data, fungsi monitoring, security feature, AI assistant, serta hasil review keamanan terhadap arsitektur dan source code project.

Tujuan pengujian bukan hanya mencari bug, tetapi juga memastikan WISMON dapat berkembang dari sekadar system monitoring menjadi **Windows endpoint monitoring/security agent** yang stabil, aman, ringan, dan dapat digunakan secara reliable.

---

# 1. Menu Dashboard Tidak Sinkron

Pada saat pengujian dengan membandingkan bagian card **CPU Usage** dengan Windows Task Manager, terdapat perbedaan waktu update.

Dengan stopwatch, update data terlihat memiliki rentang sekitar **8 detik**, sedangkan seharusnya informasi monitoring utama dapat diperbarui sekitar **1 detik** atau mendekati real-time.

Data yang dimaksud:

- CPU Usage
- Memory Usage
- Storage
- Network Throughput

Untuk data status card tersebut, sebaiknya tidak perlu menyimpan setiap nilai ke database apabila tujuan utamanya hanya menampilkan kondisi perangkat secara real-time.

Lebih baik:

```text
Windows System
      ↓
Collector
      ↓
In-memory/current state
      ↓
API / SSE / WebSocket
      ↓
Dashboard
```

Sedangkan database digunakan untuk:

- historical telemetry
- history analysis
- incident/event
- audit log
- statistik jangka panjang

### Temuan tambahan

Setelah aplikasi dihentikan menggunakan `Ctrl + C`, kemudian `.env` ditambahkan/diperbaiki dan aplikasi dijalankan kembali, data menjadi update setiap sekitar 1 detik dan terlihat lebih real-time.

Health Score juga berubah dari sekitar **60 menjadi 85**.

Hal ini perlu diperiksa lebih lanjut karena perubahan perilaku tersebut menunjukkan kemungkinan adanya:

- konfigurasi environment yang belum terbaca sebelumnya;
- collector yang tidak berjalan optimal;
- interval polling yang berbeda;
- proses background yang belum berjalan;
- SSE/stream yang belum berjalan dengan benar;
- cache/state lama;
- konfigurasi database;
- atau masalah startup sequence.

Perlu dipastikan bahwa solusi tersebut tidak hanya membuat monitoring lebih cepat tetapi juga tidak meningkatkan penggunaan:

- CPU;
- RAM;
- disk I/O;
- network;
- battery/power consumption.

---

# 2. Chart "CPU & Memory Real-Time Load (60s)" dan "Memory Allocation Trend"

Beberapa masalah UI ditemukan pada kedua chart:

- Chart terlalu panjang ke bawah sehingga melebihi area card.
- Card **CPU & Memory Real-Time Load (60s)** terlalu lebar dan dapat menyebabkan halaman bergeser ke kanan.
- Lebar card sebaiknya dikurangi sekitar 10% atau dibuat responsive mengikuti viewport.

### Hover information

Ketika pointer diarahkan ke titik/area diagram, sebaiknya diberikan informasi yang lebih detail.

Contoh:

```text
CPU Usage
18%

Time:
14:40:32
```

atau:

```text
CPU: 18%
Memory: 63%

14:40:32
```

Waktu sebaiknya menggunakan waktu sistem yang sebenarnya ketika telemetry tersebut dikumpulkan, bukan sekadar waktu ketika frontend menerima data.

Hal ini penting untuk membedakan:

```text
Collection Time
≠
API Response Time
≠
Frontend Render Time
```

---

# 3. GPU Nvidia-centric

Menu GPU saat ini terlihat terlalu berorientasi kepada GPU NVIDIA.

Seharusnya WISMON mendukung GPU secara global dan dinamis.

Target:

```text
NVIDIA
AMD
Intel
Integrated GPU
Discrete GPU
Multiple GPU
```

Contohnya sebuah laptop dapat memiliki:

```text
GPU 0:
Intel Integrated Graphics

GPU 1:
NVIDIA GeForce RTX
```

Dashboard harus mampu menampilkan keduanya secara dinamis.

Informasi yang sebaiknya tersedia:

- GPU name
- Vendor
- GPU utilization
- VRAM usage
- VRAM total
- Temperature
- Power usage jika tersedia
- Driver version jika memungkinkan

Jangan membuat logic seperti:

```text
if NVIDIA:
    collect GPU metrics
```

Tetapi lebih baik menggunakan abstraction:

```text
GPU Collector
      ↓
Detect available GPUs
      ↓
Detect vendor
      ↓
Use appropriate backend/provider
      ↓
Normalize result
      ↓
Dashboard
```

Dengan demikian frontend tidak perlu mengetahui apakah GPU tersebut NVIDIA, AMD, atau Intel.

---

# 4. Storage Menu

## 4.1 Duplikasi menu

Sidebar saat ini memiliki:

- Storage
- Storage Analyzer

Jika kedua menu tersebut memiliki content yang sangat mirip atau saling berhubungan, sebaiknya digabung menjadi:

```text
Storage
```

Kemudian di dalam halaman tersebut dapat dibuat beberapa section:

```text
Storage Overview
Disk Throughput
Storage Analyzer
Large Files
Old Files
Insights
```

Hal ini akan membuat navigation lebih sederhana.

---

## 4.2 Live Disk Throughput Curve tidak muncul

**Live Disk Throughput Curve** tidak menampilkan data.

Perlu diperiksa apakah collector benar-benar mengambil:

```text
Read Bytes/sec
Write Bytes/sec
```

dan bukan hanya total cumulative bytes.

Idealnya:

```text
Current Read:
25 MB/s

Current Write:
8 MB/s
```

Data harus mendukung berbagai tipe storage:

- HDD
- SATA SSD
- NVMe SSD
- external storage
- USB storage jika memungkinkan

Jangan membuat collector yang hanya bekerja pada tipe storage tertentu.

---

## 4.3 Storage Analyzer — Delete Action

Pada:

**Storage Analyzer Insights (Safe Review Mode)**

sebaiknya ditambahkan action:

```text
Delete
```

Namun implementasinya harus aman.

File sebaiknya tidak langsung dihapus permanen.

Workflow yang disarankan:

```text
User memilih file
        ↓
Delete
        ↓
Confirmation
        ↓
Move to Windows Recycle Bin
        ↓
Success
```

Jangan menggunakan permanent deletion sebagai default.

Selain itu, jangan memberikan permission delete ke semua file secara sembarangan.

File system yang bersifat:

- system;
- protected;
- executable;
- Windows directory;
- application directory;

sebaiknya diberikan warning atau diblokir dari Safe Review Mode.

---

# 5. Network Menu

## 5.1 Duplikasi menu

Sidebar saat ini memiliki beberapa menu yang berkaitan dengan network, misalnya:

- Network
- Connections
- Network Analysis

Jika seluruhnya merupakan bagian dari halaman/network monitoring yang sama, sebaiknya cukup:

```text
Network
```

Kemudian satu halaman Network menampilkan:

```text
Network Overview
Network Throughput
Active Connections
Network Analysis
DNS / Remote Hosts
```

Tujuannya agar user tidak merasa bahwa satu fitur yang sama dipisahkan menjadi beberapa menu.

---

## 5.2 Bandwidth Throughput Chart

**Bandwidth Throughput (KB/s)** tidak menampilkan data.

Perlu diperiksa hubungan antara:

```text
Network Collector
        ↓
Network Throughput Data
        ↓
API/SSE
        ↓
Frontend Chart
```

Periksa khususnya apakah collector memberikan:

```text
bytes sent
bytes received
```

sebagai nilai cumulative atau sudah menjadi rate.

Jika menggunakan cumulative counter, frontend/backend perlu menghitung:

```text
throughput =
(current_bytes - previous_bytes) / elapsed_time
```

Kemudian dikonversi ke:

```text
KB/s
MB/s
```

---

# 6. Process Menu

Terdapat process:

```text
System Idle Process
```

yang menampilkan CPU usage sangat tinggi, bahkan mencapai sekitar:

```text
586%
```

atau ratusan persen.

Hal ini berpotensi membingungkan user karena CPU Usage biasanya dipahami sebagai persentase total CPU.

Perlu dijelaskan bagaimana WISMON menghitung CPU process.

Jika menggunakan konsep:

```text
CPU percentage per logical processor
```

maka nilai >100% mungkin memang dapat terjadi.

Namun UI harus memberikan penjelasan.

Contohnya:

```text
CPU Usage: 586%

Explanation:
CPU percentage is calculated across logical processors.
Values above 100% represent usage across multiple CPU cores.
```

Selain itu, setiap process sebaiknya mempunyai informasi/deskripsi yang membantu user memahami:

- process name;
- executable path;
- user;
- PID;
- CPU;
- memory;
- status;
- parent process jika tersedia;
- alasan process dianggap suspicious jika masuk Threat Center.

---

# 7. Security

## 7.1 Duplikasi menu

Jika dua menu Security memiliki content yang sama, sebaiknya cukup:

```text
Security Events
```

Kemudian seluruh event security ditampilkan pada satu halaman.

---

## 7.2 Resolve Security Event

Ketika user menekan:

```text
Resolve
```

event berpindah ke log dengan status:

```text
Resolved
```

Perlu dipastikan apakah `Resolve` hanya:

```text
mengubah status database
```

atau benar-benar melakukan:

```text
tindakan remediation
```

Contohnya:

```text
Threat detected
       ↓
Resolve
       ↓
Apakah hanya status berubah?
```

atau:

```text
Threat detected
       ↓
Resolve
       ↓
Process terminated
File quarantined
Connection blocked
Persistence removed
       ↓
Status Resolved
```

Jika Resolve hanya mengubah status, UI sebaiknya menggunakan istilah yang lebih tepat seperti:

```text
Mark as Resolved
```

Sedangkan jika memang melakukan remediation, harus ditampilkan dengan jelas tindakan apa yang dilakukan.

---

# 8. Analysis

## 8.1 Duplikasi Performance dan History

Jika:

```text
Performance
History
```

memiliki content yang sama atau overlap terlalu besar, sebaiknya navigation disederhanakan.

Contohnya:

```text
Analysis
 ├── Performance
 └── History
```

atau jika memang tidak ada perbedaan signifikan, cukup:

```text
Performance
```

dengan opsi:

```text
Live
Historical
```

di dalam halaman.

---

## 8.2 Historical Telemetry Curve

**Historical Telemetry Curve (SQLite DB)** tidak menampilkan data.

Perlu diperiksa apakah sistem memang membutuhkan waktu tertentu, misalnya satu jam, sebelum data muncul.

Jika demikian, UI harus memberikan informasi:

```text
Collecting historical data...

Historical chart will become available
after sufficient telemetry has been collected.
```

Namun jika data seharusnya langsung tersimpan, perlu diperiksa:

```text
Collector
   ↓
Database
   ↓
SQLite table
   ↓
Query
   ↓
Historical API
   ↓
Chart
```

Periksa juga apakah:

- SQLite benar-benar menerima insert;
- timestamp benar;
- query menggunakan range waktu yang benar;
- database path sesuai `.env`;
- timezone benar;
- frontend membaca response yang benar;
- data historical terhapus/overwrite secara tidak sengaja.

---

# 9. Dahoo

## 9.1 Navigation Dahoo

Menurut pengujian, menu Dahoo di sidebar tidak diperlukan jika sudah terdapat floating chat.

Sebaiknya cukup:

```text
Floating Dahoo Button
        ↓
Chat Panel
```

di pojok kanan bawah.

---

## 9.2 Cloud AI / Gemini

Fitur:

```text
Enable Cloud AI (Gemini)
```

saat ini terasa kurang jelas.

Ketika user menekan tombol, tidak terdapat feedback yang cukup mengenai apakah mode benar-benar berubah.

Minimal perlu ada status:

```text
Local AI
```

atau:

```text
Gemini Cloud
```

dan ketika terjadi kegagalan:

```text
Gemini unavailable
Using Local AI
```

Jika koneksi internet/Gemini tidak tersedia, aplikasi sebaiknya melakukan fallback otomatis:

```text
User
 ↓
Dahoo
 ↓
Check Cloud AI
 ├── Available → Gemini
 └── Unavailable → Local Response
```

Ketika koneksi kembali:

```text
Cloud available
      ↓
Automatically switch back
```

Jika fitur Gemini memang tidak dianggap penting, fitur tersebut dapat dihilangkan untuk menyederhanakan aplikasi.

Namun jika dipertahankan, status koneksi dan perubahan mode harus dibuat jelas.

---

## 9.3 Chat UI

UI chat sebaiknya menggunakan model bubble seperti aplikasi messaging.

Contoh:

```text
                    ┌──────────────────┐
                    │ User message     │
                    └──────────────────┘

┌──────────────────────────────┐
│ Dahoo response               │
│ CPU terlihat normal...       │
└──────────────────────────────┘
```

User message dan AI response harus dapat dibedakan dengan jelas.

Tambahkan:

- avatar;
- timestamp;
- user bubble;
- AI bubble;
- loading indicator;
- error state;
- typing indicator jika memungkinkan.

---

## 9.4 Dahoo Mascot

Icon Dahoo dapat dikembangkan menjadi maskot:

```text
Wolf / Serigala
```

dengan ekspresi berbeda berdasarkan kondisi device.

Contoh:

```text
Normal:
Serigala tersenyum

High CPU:
Serigala terlihat kepanasan

Threat detected:
Serigala waspada

Critical:
Serigala panik/siaga

Healthy:
Serigala senang
```

Hal ini dapat menjadi identitas visual WISMON.

---

# 10. SECURITY AUDIT — API Authentication

Ini merupakan salah satu temuan keamanan terpenting dari review source code.

API WISMON saat ini tidak terlihat memiliki mekanisme authentication/authorization yang memadai pada endpoint utama.

Beberapa endpoint yang perlu mendapatkan perhatian khusus antara lain:

```text
/api/telemetry/current
/api/activity/processes
/api/activity/process/{pid}
/api/activity/sockets
/api/activity/services
/api/security/threats
/api/security/events
/api/security/mitigate
/api/analysis/history
/api/dahoo/chat
```

Masalahnya menjadi lebih serius jika WISMON nantinya diubah dari:

```text
localhost-only application
```

menjadi:

```text
LAN-accessible
```

atau:

```text
Internet-accessible
```

Default bind ke:

```text
127.0.0.1
```

merupakan keputusan yang baik dan sebaiknya dipertahankan sampai authentication tersedia.

---

# 11. CRITICAL — Process Termination API

Endpoint process termination merupakan attack surface yang sangat penting.

Endpoint:

```text
POST /api/activity/process/terminate
```

dapat melakukan termination terhadap process berdasarkan PID.

Konsep keamanan saat ini tidak boleh hanya bergantung pada:

```text
confirm = true
```

karena `confirm` bukan authentication.

Request seperti:

```json
{
    "pid": 1234,
    "confirm": true
}
```

tidak seharusnya cukup untuk melakukan privileged action jika API dapat diakses oleh pihak lain.

Workflow yang disarankan:

```text
Client
  ↓
Authentication
  ↓
Authorization
  ↓
Confirmation
  ↓
PID validation
  ↓
Process ownership validation
  ↓
Terminate
  ↓
Audit log
```

Tambahkan juga audit:

```text
Who:
admin/user/agent

When:
timestamp

What:
process termination

PID:
1234

Process:
example.exe

Reason:
Threat mitigation

Result:
Success/Failed
```

---

# 12. HIGH — Security Mitigation API

Endpoint:

```text
/api/security/mitigate
```

juga perlu dilindungi secara ketat.

Jika action dapat melakukan:

```text
TERMINATE_PROCESS
```

maka endpoint tersebut harus dianggap sebagai:

```text
Privileged Security Action
```

Jangan hanya menggunakan:

```text
confirm=true
```

sebagai perlindungan.

Harus terdapat:

- authentication;
- authorization;
- role checking;
- audit trail;
- confirmation;
- target validation;
- error handling.

---

# 13. HIGH — Sensitive Telemetry Exposure

WISMON mengumpulkan informasi yang cukup sensitif, misalnya:

### Process

```text
PID
Process Name
Executable Path
Username
CPU
Memory
Threads
Handles
Created Time
```

### Network

```text
Local Address
Remote Address
Remote IP
Remote Port
Hostname
PID
Process Name
Connection State
```

Informasi tersebut dapat membocorkan:

- username Windows;
- struktur filesystem;
- aplikasi yang sedang berjalan;
- lokasi executable;
- koneksi network;
- remote host;
- aktivitas perangkat.

Oleh karena itu telemetry harus dianggap sebagai:

```text
Sensitive Endpoint Data
```

dan tidak boleh diberikan ke client tanpa authentication.

---

# 14. HIGH — SSE / Real-Time Stream Security

Endpoint real-time seperti:

```text
/api/stream/realtime
```

juga perlu mendapatkan authentication.

SSE yang tidak terlindungi dapat menyebabkan telemetry dikirim secara terus menerus kepada client yang tidak seharusnya mendapatkannya.

Target:

```text
Authenticated Client
       ↓
SSE Connection
       ↓
Real-time Telemetry
```

bukan:

```text
Anyone who can access port
       ↓
Real-time Telemetry
```

---

# 15. HIGH — CORS Configuration

Konfigurasi CORS yang terlalu permisif perlu diperbaiki.

Konfigurasi seperti:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

sebaiknya tidak digunakan untuk production security application.

Gunakan daftar origin yang memang dipercaya.

Contoh konsep:

```text
Allowed Origin:
http://localhost:3000
```

atau domain production tertentu.

Method dan header juga sebaiknya dibatasi sesuai kebutuhan.

---

# 16. MEDIUM — Rate Limiting

API penting sebaiknya mempunyai rate limiting.

Endpoint yang perlu diperhatikan:

```text
/api/dahoo/chat
/api/analysis/storage/scan
/api/stream/realtime
/api/security/mitigate
/api/activity/process/terminate
```

Contohnya:

```text
Storage Scan
→ jangan dapat dipanggil ratusan kali per detik

Dahoo Chat
→ batasi request

Security Mitigation
→ sangat ketat

Process Termination
→ sangat ketat
```

---

# 17. MEDIUM — Storage Analyzer Performance / DoS

Storage Analyzer melakukan recursive filesystem scanning.

Jika target directory memiliki sangat banyak file, operasi tersebut dapat menjadi berat.

Jika endpoint scan dapat dipanggil berkali-kali, dapat terjadi:

```text
Request
 ↓
Filesystem scan
 ↓
Thousands of files
 ↓
CPU / Disk I/O meningkat
 ↓
Request berikutnya
 ↓
Resource exhaustion
```

Lebih baik menggunakan background job:

```text
POST /storage/scan
       ↓
Create Job
       ↓
Return job_id
       ↓
Background scan
       ↓
GET /storage/scan/{job_id}
```

Tambahkan rate limiting dan pembatasan target directory.

---

# 18. MEDIUM — Cloud AI Privacy

Jika Dahoo menggunakan Gemini Cloud, perlu diperhatikan bahwa data yang dikirim ke Cloud AI dapat mengandung informasi dari user.

Jangan mengirim seluruh telemetry endpoint secara mentah tanpa filtering.

Contoh data yang sebaiknya dipertimbangkan untuk disanitasi:

```text
Windows username
Full filesystem path
Private IP
Remote IP
Process information
Potentially sensitive filenames
```

Sebaiknya Dahoo menggunakan:

```text
Raw telemetry
      ↓
Sanitization
      ↓
Relevant summary
      ↓
Cloud AI
```

bukan:

```text
Entire endpoint database
      ↓
Cloud AI
```

UI juga harus menjelaskan kapan Cloud AI digunakan.

---

# 19. MEDIUM — Error Information Disclosure

Error dari third-party service seperti Gemini sebaiknya tidak langsung diberikan secara mentah kepada user.

Untuk development:

```text
logger.exception(...)
```

dapat digunakan untuk mendapatkan detail.

Tetapi user sebaiknya hanya mendapatkan:

```text
Cloud AI temporarily unavailable.
Using Local AI instead.
```

Hindari menampilkan detail internal seperti:

- API error;
- stack trace;
- internal request information;
- provider configuration;
- internal exception.

---

# 20. MEDIUM — Dependency Security

Dependency project sebaiknya tidak hanya menggunakan:

```text
package>=version
```

untuk production.

Lebih baik menggunakan dependency yang telah diuji dan dipin versinya.

Selain itu tambahkan vulnerability scanning secara berkala.

Contohnya workflow:

```text
Git Push
   ↓
Dependency Scan
   ↓
SAST
   ↓
Unit Test
   ↓
Build
   ↓
Security Test
   ↓
Release
```

---

# 21. Threat Center — Jangan Langsung Menganggap Malware

Konsep Threat Center saat ini sebaiknya tetap menggunakan pendekatan anomaly/suspicious detection.

Contoh rule:

```text
CPU > 75%
RAM > 94%
High network connections
```

tidak otomatis berarti:

```text
MALWARE
```

Lebih tepat menggunakan classification seperti:

```text
NORMAL
LOW RISK
ANOMALOUS
SUSPICIOUS
HIGH RISK
CONFIRMED
```

Karena:

```text
High CPU
```

bisa disebabkan oleh:

- rendering;
- compiling;
- gaming;
- video encoding;
- antivirus scan;
- Windows Update;
- legitimate application.

Threat Center sebaiknya menggabungkan beberapa indikator sebelum menaikkan severity.

---

# 22. Rekomendasi Arsitektur WISMON

Jika project ini akan dikembangkan lebih jauh menjadi endpoint monitoring/security platform, arsitektur yang disarankan:

```text
                    WISMON
                       │
        ┌──────────────┴──────────────┐
        │                             │
 Windows Endpoint                Management UI
        │                             │
   WISMON Agent                       │
        │                             │
        └──────────────┬──────────────┘
                       │
                  Secure API
                       │
              Authentication
                       │
              Authorization
                       │
                 Telemetry
                       │
             Event / Database
                       │
              Threat Detection
                       │
                Response
```

Agent sebaiknya mempunyai:

```text
Agent ID
Agent Version
Authentication Credential
Heartbeat
Last Seen
OS Information
Hardware Information
Telemetry
Security Events
```

---

# 23. Roadmap Pengembangan

## Phase 1 — Stability

Prioritas pertama:

```text
[ ] Fix dashboard real-time update
[ ] Fix GPU monitoring
[ ] Fix disk throughput
[ ] Fix network throughput
[ ] Fix historical telemetry
[ ] Fix chart responsive layout
[ ] Improve process CPU calculation
[ ] Improve UI navigation
```

---

## Phase 2 — Security

```text
[ ] Authentication
[ ] Authorization
[ ] RBAC
[ ] CORS restriction
[ ] Rate limiting
[ ] HTTPS
[ ] Audit logging
[ ] Secure API error handling
[ ] Process termination authorization
[ ] Security mitigation authorization
```

---

## Phase 3 — Endpoint Agent

```text
[ ] Agent registration
[ ] Agent ID
[ ] Heartbeat
[ ] Secure communication
[ ] Agent authentication
[ ] Agent update mechanism
[ ] Agent health status
```

---

## Phase 4 — Advanced Detection

```text
[ ] Process tree
[ ] Parent-child process analysis
[ ] Windows Event Log
[ ] PowerShell monitoring
[ ] Startup persistence
[ ] DNS monitoring
[ ] File hash
[ ] Network anomaly detection
[ ] Behavioral detection
```

---

## Phase 5 — Response

```text
[ ] Process termination
[ ] File quarantine
[ ] Network isolation
[ ] Evidence collection
[ ] Incident timeline
[ ] Response audit
```

---

# 24. Prioritas Perbaikan

Urutan perbaikan yang disarankan:

### 🔴 Critical

1. Authentication API
2. Authorization
3. Secure Process Termination
4. Secure Security Mitigation

### 🟠 High

5. Sensitive telemetry protection
6. SSE authentication
7. CORS restriction
8. Rate limiting

### 🟡 Medium

9. Storage scan optimization
10. Cloud AI privacy
11. Error sanitization
12. Dependency pinning
13. Historical telemetry reliability

### 🔵 Functional/UI

14. Dashboard real-time
15. GPU global support
16. Network throughput
17. Disk throughput
18. Chart responsive
19. Navigation simplification
20. Dahoo UI

---

# 25. Kesimpulan

WISMON memiliki potensi yang cukup besar untuk berkembang dari sebuah **Windows System Monitoring Dashboard** menjadi **lightweight endpoint monitoring/security agent**.

Kelebihan utama project:

- real-time telemetry;
- process monitoring;
- socket/network monitoring;
- storage analysis;
- security event;
- threat detection;
- historical telemetry;
- local AI;
- optional cloud AI;
- dashboard architecture;
- collector/engine/API separation.

Namun, jika WISMON akan digunakan sebagai **security product** atau API-nya akan dibuka melalui LAN/Internet, aspek security harus menjadi prioritas utama.

Masalah paling penting yang harus diperbaiki adalah:

```text
Authentication
Authorization
Process Termination Security
Security Mitigation Security
Telemetry Protection
SSE Protection
CORS
Rate Limiting
Audit Logging
```

Default:

```text
127.0.0.1
```

sebaiknya tetap dipertahankan sampai security boundary tersebut selesai.

Target akhirnya sebaiknya bukan sekadar:

```text
Task Manager versi Web
```

tetapi:

```text
Windows Endpoint
      ↓
WISMON Agent
      ↓
Telemetry
      ↓
Detection
      ↓
Risk Assessment
      ↓
Investigation
      ↓
Controlled Response
      ↓
Audit
```

Dengan arah tersebut, WISMON dapat menjadi project yang jauh lebih kuat untuk menunjukkan kemampuan **endpoint monitoring, system observability, security monitoring, dan defensive security**.