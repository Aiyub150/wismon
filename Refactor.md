# WISMON — Windows System Monitoring

## Refactor Requirements

Project ini sekarang menggunakan nama resmi:

> **WISMON — Windows System Monitoring**

Dokumen ini berisi requirement khusus untuk memperbaiki dua masalah utama yang ditemukan pada implementasi saat ini:

1. UI terlihat terlalu "AI-generated" dan tidak terasa seperti aplikasi monitoring profesional.
2. Dashboard terasa lambat karena pembaruan data menggunakan interval sekitar 3 detik.

Jangan mengubah requirement fitur utama WISMON di luar scope dokumen ini kecuali memang diperlukan untuk implementasi.

---

# 1. UI / UX REFAC​​TOR

## Problem

UI WISMON saat ini terlihat seperti dashboard yang dibuat langsung oleh AI dari nol.

Masalah yang dirasakan:

- Terlalu banyak elemen dekoratif.
- Visual hierarchy kurang natural.
- Layout terasa seperti template generative AI.
- Dashboard tidak terasa seperti aplikasi monitoring Windows profesional.
- Sidebar/navigation belum terasa seperti aplikasi dengan banyak modul.
- Beberapa komponen terlihat dibuat hanya untuk memenuhi tampilan.
- Fokus terhadap telemetry dan informasi sistem belum cukup kuat.

WISMON harus terlihat seperti **produk software monitoring sungguhan**, bukan hasil generate UI AI.

---

# 2. Gunakan TailAdmin sebagai UI Foundation

Gunakan:

**TailAdmin Free Tailwind CSS Dashboard Template**

Repository:

https://github.com/TailAdmin/tailadmin-free-tailwind-dashboard-template.git

Official repository:

https://github.com/TailAdmin/tailadmin-free-tailwind-dashboard-template

TailAdmin digunakan sebagai:

> **UI foundation / design system / layout foundation**

bukan sebagai sumber fitur WISMON.

TailAdmin menyediakan komponen seperti:

- Sidebar
- Header
- Dashboard layout
- Charts
- Tables
- Alerts
- Dropdowns
- Modals
- Dark mode
- Responsive layout

Gunakan komponen-komponen tersebut untuk membangun UI WISMON. TailAdmin memang dirancang sebagai dashboard/admin template dan menyediakan komponen yang relevan dengan aplikasi data-rich seperti WISMON.

---

# 3. Jangan Membuat UI dari Nol

Jangan membuat desain dashboard baru hanya berdasarkan interpretasi AI.

Jangan menghasilkan UI yang terlihat seperti:

- AI SaaS dashboard
- futuristic dashboard
- excessive glassmorphism
- excessive gradients
- excessive glowing effects
- excessive rounded cards
- excessive animations
- decorative elements yang tidak memiliki fungsi

Prioritas:

> **Professional > Functional > Readable > Attractive**

---

# 4. TailAdmin sebagai Kerangka, Bukan Batasan Fitur

Gunakan struktur visual TailAdmin sebagai foundation.

Contoh:

```text
┌─────────────────────────────────────────────────────────┐
│ Header / Topbar                                         │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│ Sidebar      │              Main Content                │
│              │                                          │
│ Dashboard    │                                          │
│ CPU          │                                          │
│ Memory       │                                          │
│ Storage      │                                          │
│ Network      │                                          │
│ Processes    │                                          │
│ Services     │                                          │
│ Security     │                                          │
│ Analysis     │                                          │
│ Dahoo        │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

Namun isi menu harus mengikuti fitur WISMON.

Jangan mempertahankan menu demo TailAdmin yang tidak relevan.

---

# 5. WISMON Sidebar

Sidebar harus merepresentasikan fitur nyata WISMON.

Gunakan struktur:

```text
WISMON
│
├── Overview
│   └── Dashboard
│
├── System
│   ├── CPU
│   ├── Memory
│   ├── GPU
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
│   └── Security Events
│
├── Analysis
│   ├── Performance
│   ├── Storage Analyzer
│   ├── Network Analysis
│   └── History
│
└── Assistant
    └── Dahoo
```

Tidak semua menu harus langsung aktif jika backend-nya belum tersedia.

Jika suatu fitur belum selesai:

- jangan membuat dummy page
- jangan membuat dummy data
- boleh memberikan placeholder yang jelas

---

# 6. Dashboard WISMON

Dashboard harus terasa seperti **Windows system monitoring console**.

Jangan membuat dashboard seperti:

- ecommerce dashboard
- sales dashboard
- finance dashboard
- AI SaaS dashboard

Dashboard harus berorientasi kepada telemetry.

Prioritas informasi:

```text
System Health
      ↓
CPU / Memory / GPU / Storage
      ↓
Network
      ↓
Processes
      ↓
Security
      ↓
Analysis
```

---

# 7. Dashboard Layout

Contoh struktur:

```text
SYSTEM HEALTH
────────────────────────────────────────────

CPU       Memory       GPU       Storage
32%       48%         18%        67%


CPU & MEMORY
────────────────────────────────────────────
Real-time chart


NETWORK
────────────────────────────────────────────
Inbound / Outbound


TOP PROCESSES
────────────────────────────────────────────
Process | CPU | Memory | Network


SECURITY
────────────────────────────────────────────
Threat / Event summary
```

Tidak perlu membuat semua informasi menjadi card terpisah.

Gunakan:

- table
- chart
- compact metric
- status indicator

jika lebih cocok.

---

# 8. Visual Style

Gunakan visual style TailAdmin yang sudah tersedia.

Prioritas:

- clean
- professional
- compact
- readable
- consistent
- minimal animation
- responsive
- dark mode support

Gunakan warna untuk menyampaikan status.

Contoh:

```text
Normal       → neutral/green
Warning      → yellow/orange
Critical     → red
Information  → blue
```

Jangan menggunakan warna hanya sebagai dekorasi.

---

# 9. Jangan Overdesign

Hindari:

```text
❌ Giant hero section
❌ Excessive gradients
❌ Excessive glow
❌ Animated background
❌ Excessive glass effect
❌ Floating decorative particles
❌ Large unnecessary illustrations
❌ Excessive rounded cards
❌ Animation pada setiap metric
```

WISMON adalah **monitoring application**, bukan landing page.

---

# 10. Real-Time Monitoring

## Problem

Dashboard saat ini terasa delay karena data diperbarui sekitar setiap 3 detik.

Untuk aplikasi monitoring, pendekatan ini tidak ideal.

Jangan menjadikan:

```text
collect
↓
wait 3 seconds
↓
update UI
```

sebagai mekanisme utama.

---

# 11. Pisahkan Tiga Layer

Monitoring harus mempunyai tiga layer:

```text
Windows Telemetry
       │
       ▼
Collector
       │
       ▼
Realtime State
       │
       ├──────────────► Frontend
       │
       ▼
Historical Storage
```

Jangan menggunakan database sebagai sumber utama untuk setiap update UI.

---

# 12. Realtime State

Collector harus menyimpan state terbaru di memory.

Contoh:

```python
current_state = {
    "cpu": ...,
    "memory": ...,
    "gpu": ...,
    "storage": ...,
    "network": ...,
    "processes": ...,
    "threats": ...
}
```

Frontend mengambil data terbaru dari realtime stream.

Database digunakan untuk historical data, bukan sebagai perantara setiap update UI.

---

# 13. Gunakan Streaming

Prioritaskan:

> **Server-Sent Events (SSE)**

atau:

> **WebSocket**

daripada polling frontend setiap 3 detik.

Contoh:

```text
Windows Collector
       │
       │ new telemetry
       ▼
Realtime Event Bus
       │
       ▼
SSE / WebSocket
       │
       ▼
WISMON Frontend
       │
       ▼
Update affected components
```

Frontend tidak perlu:

```text
GET /metrics
wait 3 sec
GET /metrics
wait 3 sec
GET /metrics
```

---

# 14. UI Update Frequency

Realtime tidak berarti semua komponen harus melakukan render ulang setiap millisecond.

Gunakan pendekatan:

> **high-frequency collection + efficient UI update**

Contoh target:

```text
CPU                  ~500ms–1s
Memory               ~1s
GPU                  ~500ms–1s
Network throughput   ~500ms–1s
Process statistics   ~1s
Sockets              ~1–2s
Services             ~5–10s
Storage health       ~10–60s
File analysis        On demand
```

Interval tersebut adalah target awal, bukan angka mutlak.

Sesuaikan berdasarkan resource consumption dan kemampuan Windows API.

---

# 15. Jangan Menggunakan `sleep(3)` untuk Semua Collector

Jangan membuat architecture seperti:

```python
while True:
    collect_everything()
    save_everything()
    sleep(3)
```

Ini menyebabkan:

- latency
- burst workload
- UI terasa lambat
- telemetry tidak benar-benar realtime
- collector berbeda memiliki interval yang tidak sesuai kebutuhan

Gunakan collector independen atau scheduler yang memungkinkan setiap metric memiliki frequency berbeda.

---

# 16. Collector Scheduling

Contoh:

```text
CPU Collector
    └── high frequency

Memory Collector
    └── high frequency

GPU Collector
    └── high frequency

Network Collector
    └── high frequency

Process Collector
    └── medium frequency

Socket Collector
    └── medium frequency

Service Collector
    └── low frequency

Storage Health
    └── low frequency
```

Jangan memaksa semua collector bekerja pada interval yang sama.

---

# 17. Database Write Strategy

Realtime data tidak harus langsung ditulis ke SQLite setiap kali collector mendapatkan data.

Gunakan:

```text
Collector
   ↓
In-memory buffer
   ↓
Aggregation / batching
   ↓
SQLite
```

Contoh:

```text
CPU:
Realtime → ~1 second

SQLite:
Aggregated/batched → every few seconds
```

Dengan demikian:

- UI tetap realtime.
- SQLite tidak mengalami excessive write.
- SSD tidak dibebani write berlebihan.

---

# 18. Frontend Rendering Optimization

Jangan melakukan full-page refresh.

Jangan melakukan:

```javascript
location.reload()
```

untuk mendapatkan telemetry terbaru.

Update hanya component yang berubah.

Contoh:

```text
CPU event
   ↓
CPU metric update
CPU chart update

Memory event
   ↓
Memory metric update
Memory chart update
```

Tidak perlu merender ulang seluruh dashboard.

---

# 19. Chart Optimization

Chart realtime harus memiliki buffer terbatas.

Contoh:

```text
Current chart window:

60–120 samples
```

Ketika sample baru masuk:

```text
remove oldest
+
add newest
```

Jangan menyimpan ribuan sample dalam browser hanya untuk menampilkan beberapa menit terakhir.

Historical data harus diambil dari backend ketika user memilih periode lama.

---

# 20. Realtime Connection Status

UI harus menunjukkan status koneksi monitoring.

Contoh:

```text
● LIVE
```

Jika koneksi terputus:

```text
● RECONNECTING
```

Jika backend tidak tersedia:

```text
● OFFLINE
```

Frontend harus mencoba reconnect otomatis.

---

# 21. Jangan Membuat Fake Realtime

Jangan membuat:

```javascript
setInterval(() => {
    randomizeCPU();
}, 3000);
```

atau variasi lainnya.

Semua realtime metric harus berasal dari Windows telemetry aktual.

---

# 22. Dashboard Performance

Target UX:

Ketika backend sudah berjalan:

```text
Telemetry generated
      ↓
Backend receives
      ↓
Frontend receives event
      ↓
Metric updated
```

latency harus sekecil mungkin.

Jangan menunggu fixed 3-second polling cycle hanya untuk menampilkan perubahan CPU/RAM/network.

---

# 23. Resource Efficiency

Realtime bukan berarti:

```text
CPU usage 100%
```

Monitoring harus tetap ringan.

Jika frequency dinaikkan:

- ukur CPU usage
- ukur memory usage
- ukur disk I/O
- ukur network overhead

Jika collector terlalu berat:

- kurangi frequency
- gunakan native API
- cache data
- batch database writes
- gunakan asynchronous processing
- gunakan ring buffer

---

# 24. Dahoo

Dahoo tetap tersedia sebagai assistant WISMON.

Namun Dahoo tidak boleh menjadi penyebab dashboard lambat.

Jangan meminta AI model setiap kali metric berubah.

Contoh yang SALAH:

```text
CPU update
   ↓
Call Gemini
   ↓
CPU update
   ↓
Call Gemini
```

Yang benar:

```text
CPU update
   ↓
Local analysis
   ↓
Potential anomaly
   ↓
Dahoo notification
   ↓
Cloud AI hanya jika diperlukan
```

---

# 25. Dahoo Proactive Alert

Dahoo boleh memberikan notifikasi ketika terjadi event penting.

Contoh:

```text
CPU > 90% for 10 minutes
```

bukan:

```text
CPU = 91%
CPU = 92%
CPU = 90%
CPU = 91%
```

Jangan membuat Dahoo spam user.

Gunakan:

- threshold
- duration
- cooldown
- event deduplication

---

# 26. Refactor Strategy

Jangan langsung rewrite seluruh backend.

Urutan:

### Step 1

Audit project saat ini.

Identifikasi:

- backend
- frontend
- collector
- API
- SSE/WebSocket
- SQLite
- current dashboard
- current polling mechanism

### Step 2

Integrasikan TailAdmin sebagai UI foundation.

### Step 3

Migrasikan layout:

```text
Sidebar
Header
Main Content
Footer jika diperlukan
```

### Step 4

Migrasikan Dashboard.

### Step 5

Migrasikan page lainnya.

### Step 6

Perbaiki realtime architecture.

### Step 7

Optimasi database write.

### Step 8

Benchmark CPU/RAM.

---

# 27. Jangan Mengubah Fitur Backend Tanpa Alasan

Refactor UI tidak berarti:

> Rewrite seluruh backend.

Pertahankan collector yang sudah bekerja.

Jika backend sudah menyediakan SSE, gunakan kembali.

Jika backend masih menggunakan polling, ubah hanya bagian yang diperlukan untuk mencapai realtime architecture.

---

# 28. Testing Requirement

Setelah refactor:

## UI

Pastikan:

- sidebar bekerja
- routing bekerja
- dashboard bekerja
- dark mode bekerja
- responsive
- table bekerja
- chart bekerja

## Realtime

Pastikan:

- CPU berubah tanpa refresh
- RAM berubah tanpa refresh
- Network berubah tanpa refresh
- Process data berubah tanpa refresh
- connection reconnect bekerja

## Performance

Monitor:

```text
WISMON CPU usage
WISMON RAM usage
SQLite write frequency
Frontend render frequency
Network traffic
```

---

# 29. Acceptance Criteria

Refactor dianggap berhasil jika:

### UI

- [ ] Menggunakan TailAdmin sebagai UI foundation.
- [ ] Tidak terlihat seperti AI-generated dashboard.
- [ ] Tidak menggunakan excessive visual effects.
- [ ] Sidebar mencerminkan fitur WISMON.
- [ ] Dashboard terlihat seperti monitoring application.
- [ ] Layout konsisten.
- [ ] UI responsive.
- [ ] Dark mode tersedia jika didukung template.

### Realtime

- [ ] Dashboard tidak bergantung pada polling 3 detik.
- [ ] Telemetry dikirim menggunakan SSE/WebSocket atau mekanisme streaming yang setara.
- [ ] CPU dapat berubah secara realtime.
- [ ] Memory dapat berubah secara realtime.
- [ ] Network dapat berubah secara realtime.
- [ ] Process data dapat diperbarui tanpa page refresh.
- [ ] Connection reconnect tersedia.

### Performance

- [ ] Tidak melakukan full-page reload.
- [ ] Tidak melakukan unnecessary rendering.
- [ ] Database tidak ditulis setiap telemetry event jika tidak diperlukan.
- [ ] Chart menggunakan bounded buffer.
- [ ] Collector memiliki frequency berbeda sesuai kebutuhan.
- [ ] Monitoring tidak memberikan beban CPU/RAM berlebihan.

---

# 30. Important Instruction for Gemini

Jangan membuat keputusan UI berdasarkan:

> "Menurut saya dashboard modern biasanya seperti ini."

Gunakan:

> **TailAdmin + kebutuhan WISMON + usability monitoring**

sebagai dasar.

Jangan mengubah WISMON menjadi:

- AI dashboard
- SaaS dashboard
- futuristic dashboard
- generic analytics dashboard

WISMON harus tetap terasa seperti:

> **Professional Windows System Monitoring Application**

---

# Project Identity

Nama:

**WISMON**

Kepanjangan:

**Windows System Monitoring**

Deskripsi singkat:

> WISMON is a Windows system monitoring and analysis application that provides real-time visibility into system performance, hardware, processes, storage, network activity, and security events.

Tagline opsional:

> **Monitor. Analyze. Understand.**

---

# END OF REFACTOR REQUIREMENTS