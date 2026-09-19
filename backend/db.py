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
                await db.commit()
            logger.info("Database initialized successfully with WAL mode and session schema.")
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise

    async def insert_system_info(self, data: Dict[str, Any]):
        """Queue a system_info record for batched writing."""
        async with self._lock:
            self._batch_queue.append(data)
            if len(self._batch_queue) >= 5:
                await self._flush_queue()

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
                    records
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
        """Aggregate total token usage and estimated cost."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT SUM(input_tokens), SUM(output_tokens), SUM(estimated_cost), COUNT(*)
                    FROM dahoo_messages WHERE role = 'assistant'
                    """
                ) as cursor:
                    row = await cursor.fetchone()
                    return {
                        "total_input_tokens": row[0] or 0,
                        "total_output_tokens": row[1] or 0,
                        "total_tokens": (row[0] or 0) + (row[1] or 0),
                        "total_cost": round(row[2] or 0.0, 5),
                        "assistant_responses": row[3] or 0
                    }
        except Exception as e:
            logger.error(f"Error fetching Dahoo metrics: {e}")
            return {"total_input_tokens": 0, "total_output_tokens": 0, "total_tokens": 0, "total_cost": 0.0, "assistant_responses": 0}

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
