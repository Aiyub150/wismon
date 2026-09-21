"""
Database management module for Windows System Monitoring.
Uses SQLite with WAL mode and asynchronous queries via aiosqlite.
Implements batched inserts and data retention cleanup.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
import aiosqlite
from backend.config import DB_PATH, DB_DIR, DETAILED_RETENTION_HOURS

logger = logging.getLogger("SystemMonitoring.DB")

# Create database directory if it does not exist
DB_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS system_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    cpu_percent REAL NOT NULL,
    ram_percent REAL NOT NULL,
    ram_used INTEGER NOT NULL,
    ram_total INTEGER NOT NULL,
    paged_pool INTEGER,
    nonpaged_pool INTEGER,
    commit_charge INTEGER,
    commit_limit INTEGER,
    disk_read_bytes_sec REAL,
    disk_write_bytes_sec REAL,
    net_sent_bytes_sec REAL,
    net_recv_bytes_sec REAL,
    health_score INTEGER NOT NULL,
    health_status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sysinfo_timestamp ON system_info(timestamp);

CREATE TABLE IF NOT EXISTS process_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    pid INTEGER NOT NULL,
    name TEXT NOT NULL,
    path TEXT,
    cpu_percent REAL,
    memory_bytes INTEGER,
    threads INTEGER,
    handles INTEGER
);

CREATE INDEX IF NOT EXISTS idx_proc_timestamp ON process_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_proc_name ON process_history(name);

CREATE TABLE IF NOT EXISTS socket_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    protocol TEXT NOT NULL,
    local_endpoint TEXT NOT NULL,
    remote_endpoint TEXT NOT NULL,
    hostname TEXT,
    pid INTEGER,
    process_name TEXT,
    state TEXT,
    bytes_sent INTEGER,
    bytes_recv INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sock_timestamp ON socket_history(timestamp);

CREATE TABLE IF NOT EXISTS services (
    name TEXT PRIMARY KEY,
    display_name TEXT,
    pid INTEGER,
    status TEXT,
    startup_type TEXT,
    account TEXT,
    binary_path TEXT,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS threat (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT,
    target TEXT,
    reason TEXT NOT NULL,
    evidence TEXT,
    status TEXT NOT NULL,
    recommended_action TEXT,
    action_taken TEXT,
    resolved_at REAL
);

CREATE INDEX IF NOT EXISTS idx_threat_status ON threat(status);
CREATE INDEX IF NOT EXISTS idx_threat_timestamp ON threat(timestamp);

CREATE TABLE IF NOT EXISTS dahoo_sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS dahoo_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT DEFAULT 'default',
    timestamp REAL NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    model TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    estimated_cost REAL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_dahoo_timestamp ON dahoo_messages(timestamp);

CREATE TABLE IF NOT EXISTS system_baseline (
    metric TEXT PRIMARY KEY,
    baseline_min REAL,
    baseline_max REAL,
    average REAL,
    p95 REAL,
    sample_count INTEGER,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS dahoo_knowledge_curated (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    keywords TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source TEXT DEFAULT 'curated',
    confidence REAL DEFAULT 1.0,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON dahoo_knowledge_curated(category);
"""

class DatabaseManager:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._batch_queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize database tables, indexes, and run migrations."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(SCHEMA_SQL)
                # Check for session_id column migration in dahoo_messages
                async with db.execute("PRAGMA table_info(dahoo_messages)") as cursor:
                    columns = [row[1] for row in await cursor.fetchall()]
                    if "session_id" not in columns:
                        await db.execute("ALTER TABLE dahoo_messages ADD COLUMN session_id TEXT DEFAULT 'default'")
                # Safely create index on session_id now that column is guaranteed
                await db.execute("CREATE INDEX IF NOT EXISTS idx_dahoo_session ON dahoo_messages(session_id)")

                # Seed curated knowledge bank if empty
                async with db.execute("SELECT COUNT(*) FROM dahoo_knowledge_curated") as cur:
                    count_row = await cur.fetchone()
                    if count_row and count_row[0] == 0:
                        now = time.time()
                        seeds = [
                            (
                                "thermal", "kipas,fan,berisik,panas,suhu,overheat,thermal",
                                "Kenapa kipas laptop berputar kencang dan bersuara berisik?",
                                "Kipas laptop berputar kencang menandakan prosesor (CPU) atau chip grafis sedang bekerja keras dan mencapai suhu di atas 70–80°C.\n\n"
                                "💡 **Solusi Praktis Dahoo:**\n"
                                "1. Pastikan lubang ventilasi dan exhaust tidak tertutup (hindari meletakkan laptop di atas kasur/bantal).\n"
                                "2. Periksa aplikasi terberat di tab **CPU** WISMON dan gunakan tombol **⚡ Optimalkan CPU** untuk mendinginkan beban kerja.\n"
                                "3. Gunakan profil daya 'Balanced' pada pengaturan baterai Windows.\n"
                                "4. Jika laptop sudah berumur >1 tahun, bersihkan debu pendingin dan pertimbangkan repaste thermal paste.",
                                "curated_seed", 1.0, now
                            ),
                            (
                                "memory", "commit charge,paged pool,non-paged pool,virtual memory,pagefile,alokasi",
                                "Apa arti Commit Charge, Paged Pool, dan Non-Paged Pool di tab Memory?",
                                "Berikut adalah arsitektur memori Windows yang dipantau WISMON:\n\n"
                                "- **Commit Charge**: Total kapasitas memori virtual yang telah dipesan oleh seluruh aplikasi aktif (kombinasi RAM fisik + Pagefile di disk). Jika Commit Charge mendekati batas limit, aplikasi bisa crash karena Out of Memory.\n"
                                "- **Paged Pool**: Alokasi memori untuk kernel Windows dan driver yang dapat dipindahkan (swapped) ke harddisk jika RAM fisik dibutuhkan oleh aplikasi lain.\n"
                                "- **Non-Paged Pool**: Memori khusus kernel yang **wajib selalu berada di RAM fisik** dan tidak boleh dipindahkan ke disk (misalnya penanganan hardware interrupt dan network buffer). Kebocoran memori driver biasanya terlihat jika nilai ini terus membengkak di atas 800 MB.\n\n"
                                "Gunakan tombol **⚡ Optimalkan Memori** untuk membersihkan working set cache RAM.",
                                "curated_seed", 1.0, now
                            ),
                            (
                                "gaming", "game,gaming,lag,fps drop,stutter,patah-patah,lemot saat main",
                                "Bagaimana cara mengatasi lag atau FPS drop saat bermain game di Windows?",
                                "Untuk mendapatkan performa gaming maksimal dan mengurangi stutter:\n\n"
                                "1. **Bebaskan RAM**: Tekan tombol **⚡ Optimalkan Memori** di WISMON sebelum memulai game untuk mengosongkan cache working set.\n"
                                "2. **Tutup Background Hogs**: Tutup browser (Chrome/Edge), Discord Hardware Acceleration, dan aplikasi torrent yang menyerap CPU/RAM di latar belakang.\n"
                                "3. **Aktifkan Windows Game Mode**: Buka *Settings > Gaming > Game Mode* dan pastikan statusnya ON.\n"
                                "4. **Pantau Suhu**: Pastikan suhu CPU dan GPU di bawah 85°C agar hardware tidak mengalami thermal throttling (penurunan clock speed otomatis demi keselamatan).\n"
                                "5. **Power Plan**: Ubah skema daya Windows ke 'High Performance' saat terhubung ke charger.",
                                "curated_seed", 1.0, now
                            ),
                            (
                                "storage", "disk c penuh,storage penuh,sampah,temp,disk 100%,clean disk",
                                "Bagaimana cara mengatasi disk C: yang hampir penuh atau Disk 100%?",
                                "Penyimpanan penuh dapat membuat Windows lambat dan gagal melakukan update:\n\n"
                                "1. **Bersihkan File Temp**: Gunakan fitur pembersihan Temp di WISMON atau ketik *'Bersihkan temp'* di Dahoo untuk membuang file cache sampah.\n"
                                "2. **Windows Storage Sense**: Aktifkan fitur *Penyimpanan Cerdas* di *Settings > System > Storage*.\n"
                                "3. **Disk Cleanup (cleanmgr)**: Tekan Win+R, ketik `cleanmgr`, pilih Drive C:, lalu klik *'Clean up system files'* untuk menghapus sisa Windows Update lama.\n"
                                "4. **Jika Disk 100%**: Jika menggunakan HDD mekanis, nonaktifkan layanan *Windows Search Indexing* sejenak atau pertimbangkan migrasi ke SSD NVMe untuk kecepatan 10x lipat.",
                                "curated_seed", 1.0, now
                            ),
                            (
                                "core_process", "system,csrss,csrss.exe,lsass,lsass.exe,runtime broker,svchost",
                                "Apa fungsi proses System, csrss.exe, dan lsass.exe, dan apakah boleh dihentikan?",
                                "Proses-proses tersebut adalah **Komponen Inti Kernel & Keamanan Windows**:\n\n"
                                "- **System (PID 4)**: Wadah thread kernel Windows yang mengelola driver perangkat keras, I/O, dan alokasi memori fisik.\n"
                                "- **csrss.exe**: Client/Server Runtime Subsystem yang mengelola jendela konsol dan siklus hidup pembuatan thread pengguna.\n"
                                "- **lsass.exe**: Local Security Authority yang menangani verifikasi kata sandi pengguna, token login, dan kebijakan keamanan Windows.\n\n"
                                "⚠️ **Penting**: Proses-proses ini **DILINDUNGI PENUH** oleh WISMON dan tidak boleh ditangguhkan maupun dihentikan, karena penghentian paksa akan langsung memicu Blue Screen of Death (BSOD) demi keselamatan sistem.",
                                "curated_seed", 1.0, now
                            ),
                            (
                                "antivirus", "bitdefender,bdservicehost,msmpeng,defender,vsserv,antivirus berat",
                                "Kenapa Antivirus (Bitdefender / Windows Defender) terkadang memakan CPU tinggi?",
                                "Proses seperti `bdservicehost.exe` (Bitdefender) atau `MsMpEng.exe` (Windows Defender) bertugas memindai setiap file yang dibaca, ditulis, atau diunduh secara real-time.\n\n"
                                "Lonjakan beban CPU adalah hal yang wajar ketika:\n"
                                "- Sedang berlangsung background scheduled scan.\n"
                                "- Anda baru saja menginstal atau mengunduh aplikasi berukuran besar.\n"
                                "- Terdapat aktivitas compiling kode atau transfer ribuan file kecil.\n\n"
                                "🛡️ **Proteksi WISMON**: WISMON memproteksi agen antivirus dari penangguhan (cooldown) paksa agar laptop Anda tidak kehilangan perisai keamanan.",
                                "curated_seed", 1.0, now
                            )
                        ]
                        await db.executemany(
                            """
                            INSERT INTO dahoo_knowledge_curated (category, keywords, question, answer, source, confidence, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            seeds
                        )

                await db.commit()
            logger.info("Database initialized successfully with WAL mode, session schema, and curated knowledge bank.")
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise

    async def get_curated_knowledge(self, query: str) -> Optional[str]:
        """Search curated Q&A knowledge base for matching answers."""
        q = query.lower().strip()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT category, keywords, question, answer, confidence FROM dahoo_knowledge_curated ORDER BY confidence DESC") as cur:
                    rows = await cur.fetchall()
                    for r in rows:
                        kws = [k.strip().lower() for k in r["keywords"].split(",") if k.strip()]
                        # If query contains any of the explicit multi-word keywords or 2+ single keywords
                        for kw in kws:
                            if len(kw.split()) > 1 and kw in q:
                                return r["answer"]
                        # Count matching single keywords
                        match_count = sum(1 for kw in kws if kw in q)
                        if match_count >= 2 or (len(kws) == 1 and kws[0] in q):
                            return r["answer"]
        except Exception as e:
            logger.error(f"Error querying curated knowledge: {e}")
        return None

    async def save_curated_knowledge(self, category: str, keywords: str, question: str, answer: str, source: str = "curated"):
        """Save high-quality Q&A to the persistent knowledge bank."""
        now = time.time()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO dahoo_knowledge_curated (category, keywords, question, answer, source, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, 1.0, ?)
                    """,
                    (category, keywords, question, answer, source, now)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving curated knowledge: {e}")

    async def insert_system_info(self, data: Dict[str, Any]):
        """Queue a system_info record for decoupled background writing."""
        async with self._lock:
            self._batch_queue.append(data)
            # Prevent memory overflow if worker is stalled
            if len(self._batch_queue) > 600:
                self._batch_queue = self._batch_queue[-300:]

    async def flush(self):
        """Explicitly flush pending records."""
        async with self._lock:
            await self._flush_queue()

    async def _flush_queue(self):
        if not self._batch_queue:
            return
        records = list(self._batch_queue)
        self._batch_queue.clear()
        try:
            normalized = []
            for r in records:
                normalized.append({
                    "timestamp": r.get("timestamp", time.time()),
                    "cpu_percent": r.get("cpu_percent", 0.0),
                    "ram_percent": r.get("ram_percent", 0.0),
                    "ram_used": r.get("ram_used", 0),
                    "ram_total": r.get("ram_total", 0),
                    "paged_pool": r.get("paged_pool"),
                    "nonpaged_pool": r.get("nonpaged_pool"),
                    "commit_charge": r.get("commit_charge"),
                    "commit_limit": r.get("commit_limit"),
                    "disk_read_bytes_sec": r.get("disk_read_bytes_sec", 0.0),
                    "disk_write_bytes_sec": r.get("disk_write_bytes_sec", 0.0),
                    "net_sent_bytes_sec": r.get("net_sent_bytes_sec", 0.0),
                    "net_recv_bytes_sec": r.get("net_recv_bytes_sec", 0.0),
                    "health_score": r.get("health_score", 100),
                    "health_status": r.get("health_status", "HEALTHY")
                })
            async with aiosqlite.connect(self.db_path) as db:
                await db.executemany(
                    """
                    INSERT INTO system_info (
                        timestamp, cpu_percent, ram_percent, ram_used, ram_total,
                        paged_pool, nonpaged_pool, commit_charge, commit_limit,
                        disk_read_bytes_sec, disk_write_bytes_sec,
                        net_sent_bytes_sec, net_recv_bytes_sec,
                        health_score, health_status
                    ) VALUES (
                        :timestamp, :cpu_percent, :ram_percent, :ram_used, :ram_total,
                        :paged_pool, :nonpaged_pool, :commit_charge, :commit_limit,
                        :disk_read_bytes_sec, :disk_write_bytes_sec,
                        :net_sent_bytes_sec, :net_recv_bytes_sec,
                        :health_score, :health_status
                    )
                    """,
                    normalized
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error flushing system_info batch to DB: {e}")

    async def get_history(self, duration_seconds: int = 3600, limit: int = 300) -> List[Dict[str, Any]]:
        """Fetch historical system telemetry for charts."""
        cutoff = time.time() - duration_seconds
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT timestamp, cpu_percent, ram_percent,
                           disk_read_bytes_sec, disk_write_bytes_sec,
                           net_sent_bytes_sec, net_recv_bytes_sec,
                           health_score
                    FROM system_info
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                    (cutoff, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    async def save_threat(self, threat_data: Dict[str, Any]):
        """Insert or update a threat event."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO threat (
                        id, timestamp, category, severity, source, target,
                        reason, evidence, status, recommended_action, action_taken, resolved_at
                    ) VALUES (
                        :id, :timestamp, :category, :severity, :source, :target,
                        :reason, :evidence, :status, :recommended_action, :action_taken, :resolved_at
                    )
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        action_taken = excluded.action_taken,
                        resolved_at = excluded.resolved_at
                    """,
                    threat_data
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving threat: {e}")

    async def get_active_threats(self) -> List[Dict[str, Any]]:
        """Fetch active unresolved threats."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT * FROM threat
                    WHERE status != 'RESOLVED' AND status != 'FALSE_POSITIVE'
                    ORDER BY timestamp DESC
                    """
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching active threats: {e}")
            return []

    async def get_all_threats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all threat events for Security History."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM threat ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching threats: {e}")
            return []

    async def create_or_get_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Ensure a session exists or create a new one."""
        import uuid
        now = time.time()
        sid = (session_id or "").strip() or f"sess_{uuid.uuid4().hex[:10]}"
        t = title or "Percakapan Baru"
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO dahoo_sessions (session_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET updated_at = excluded.updated_at
                    """,
                    (sid, t, now, now)
                )
                await db.commit()
            return sid
        except Exception as e:
            logger.error(f"Error creating/getting session {sid}: {e}")
            return sid

    async def get_recent_messages(self, session_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent conversation messages for a session (for multi-turn context)."""
        sid = (session_id or "default").strip()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT role, message, timestamp, model
                    FROM dahoo_messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (sid, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    # Return in chronological order
                    return [dict(r) for r in reversed(rows)]
        except Exception as e:
            logger.error(f"Error fetching recent messages for session {sid}: {e}")
            return []

    async def clear_session_messages(self, session_id: str):
        """Clear all messages belonging to a session."""
        sid = (session_id or "default").strip()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM dahoo_messages WHERE session_id = ?", (sid,))
                await db.execute("DELETE FROM dahoo_sessions WHERE session_id = ?", (sid,))
                await db.commit()
        except Exception as e:
            logger.error(f"Error clearing session {sid}: {e}")

    async def save_dahoo_message(self, role: str, message: str, session_id: str = "default", model: str = "", in_tokens: int = 0, out_tokens: int = 0, cost: float = 0.0):
        """Save a Dahoo conversation message with session_id and token usage."""
        sid = (session_id or "default").strip()
        now = time.time()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO dahoo_messages (session_id, timestamp, role, message, model, input_tokens, output_tokens, estimated_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sid, now, role, message, model, in_tokens, out_tokens, cost)
                )
                # Update session timestamp
                await db.execute(
                    """
                    INSERT INTO dahoo_sessions (session_id, title, created_at, updated_at)
                    VALUES (?, 'Percakapan', ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET updated_at = excluded.updated_at
                    """,
                    (sid, now, now)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving Dahoo message: {e}")

    async def get_dahoo_metrics(self) -> Dict[str, Any]:
        """Aggregate total token usage, remaining tokens, and estimated cost."""
        from backend.config import DAHOO_MAX_CONTEXT_TOKENS
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT SUM(input_tokens), SUM(output_tokens), SUM(estimated_cost), COUNT(*)
                    FROM dahoo_messages WHERE role = 'assistant'
                    """
                ) as cursor:
                    row = await cursor.fetchone()
                    in_toks = row[0] or 0
                    out_toks = row[1] or 0
                    consumed = in_toks + out_toks
                    remaining = max(0, DAHOO_MAX_CONTEXT_TOKENS - consumed)
                    return {
                        "total_input_tokens": in_toks,
                        "total_output_tokens": out_toks,
                        "total_tokens": consumed,
                        "total_cost": round(row[2] or 0.0, 5),
                        "assistant_responses": row[3] or 0,
                        "max_tokens": DAHOO_MAX_CONTEXT_TOKENS,
                        "remaining_tokens": remaining
                    }
        except Exception as e:
            logger.error(f"Error fetching Dahoo metrics: {e}")
            from backend.config import DAHOO_MAX_CONTEXT_TOKENS
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "assistant_responses": 0,
                "max_tokens": DAHOO_MAX_CONTEXT_TOKENS,
                "remaining_tokens": DAHOO_MAX_CONTEXT_TOKENS
            }

    async def purge_old_data(self):
        """Retention cleanup: delete records older than DETAILED_RETENTION_HOURS."""
        cutoff = time.time() - (DETAILED_RETENTION_HOURS * 3600)
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM system_info WHERE timestamp < ?", (cutoff,))
                await db.execute("DELETE FROM process_history WHERE timestamp < ?", (cutoff,))
                await db.execute("DELETE FROM socket_history WHERE timestamp < ?", (cutoff,))
                await db.commit()
            logger.info("Executed telemetry retention purge.")
        except Exception as e:
            logger.error(f"Error purging old telemetry: {e}")

db_manager = DatabaseManager()
