"""
Test suite for WISMON Dahoo Assistant Engine & Session Memory.
Validates intent classification, context routing, target validation,
session memory, and safe action execution.
"""

import unittest
import asyncio
import time
from backend.db import db_manager
from backend.engine.dahoo_engine import dahoo_engine

class TestDahooEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(db_manager.initialize())

    def test_context_routing(self):
        """Verifies that context routing extracts relevant telemetry and includes security isolation."""
        dummy_telemetry = {
            "health": {"score": 85},
            "cpu": {"total_percent": 74.5},
            "memory": {"percent": 82.1, "used_bytes": 8 * 1024**3, "total_bytes": 16 * 1024**3},
            "storage": {"overall": {"percent": 65.0, "free_bytes": 120 * 1024**3}},
            "network": {"throughput": {"bytes_recv_sec": 1024*1024, "bytes_sent_sec": 512*1024}},
            "threats": [{"category": "High CPU Process", "target": "rogue.exe", "severity": "WARNING"}],
            "process": {"top_cpu": [{"pid": 1234, "name": "rogue.exe", "cpu_percent": 65.0}]},
            "hardware": {"thermal": {"cpu_temp_c": 68}}
        }

        # CPU query
        ctx_cpu = dahoo_engine._build_routed_context("kenapa cpu tinggi sekali?", dummy_telemetry)
        self.assertIn("CPU_Total=74.5%", ctx_cpu)
        self.assertIn("rogue.exe", ctx_cpu)
        self.assertIn("NOTICE: Telemetry values are raw", ctx_cpu)

        # RAM query
        ctx_ram = dahoo_engine._build_routed_context("berapa persen penggunaan ram?", dummy_telemetry)
        self.assertIn("RAM_Percent=82.1%", ctx_ram)

        # Storage query
        ctx_storage = dahoo_engine._build_routed_context("apakah storage disk penuh?", dummy_telemetry)
        self.assertIn("Storage_UsedPercent=65.0%", ctx_storage)

        # Security query
        ctx_sec = dahoo_engine._build_routed_context("apakah ada ancaman keamanan?", dummy_telemetry)
        self.assertIn("ThreatDetail: Category=High CPU Process", ctx_sec)

    def test_local_engine_intent_and_action_proposals(self):
        """Tests that local engine correctly matches intents and generates structured action proposals."""
        dummy_telemetry = {
            "health": {"score": 55},
            "cpu": {"total_percent": 88.0},
            "memory": {"percent": 85.0, "used_bytes": 14 * 1024**3, "total_bytes": 16 * 1024**3},
            "storage": {"overall": {"percent": 92.0, "free_bytes": 5 * 1024**3}},
            "network": {"throughput": {"bytes_recv_sec": 50000, "bytes_sent_sec": 10000}, "interfaces": []},
            "threats": [{"category": "High CPU Process", "target": "stress.exe", "severity": "WARNING", "id": "t1"}],
            "process": {"top_cpu": [{"pid": 9999, "name": "stress.exe", "cpu_percent": 75.0}]},
            "hardware": {"thermal": {"cpu_temp_c": 82}}
        }

        session_id = "test_sess_intent"

        # Slowness / CPU
        reply, action = asyncio.run(dahoo_engine.answer_local("kenapa laptop saya lemot?", dummy_telemetry, session_id=session_id))
        self.assertIn("stress.exe", reply)
        self.assertIsNotNone(action)
        self.assertEqual(action["type"], "COOLDOWN_PROCESS")
        self.assertEqual(action["params"]["pid"], 9999)
        self.assertTrue(action["requires_confirmation"])

        # Cancel action
        reply_cancel, action_cancel = asyncio.run(dahoo_engine.answer_local("tidak usah", dummy_telemetry, session_id=session_id))
        self.assertIn("dibatalkan", reply_cancel.lower())
        self.assertIsNone(dahoo_engine._get_pending_action(session_id))

    def test_action_validation_for_dead_pid(self):
        """Tests that attempting to cooldown an invalid/dead PID is rejected safely."""
        dead_pid = 9999999
        res = asyncio.run(dahoo_engine.execute_action("COOLDOWN_PROCESS", {"pid": dead_pid}))
        self.assertFalse(res["success"])
        self.assertIn("tidak aktif", res["message"])

    def test_session_memory_db_crud(self):
        """Tests database multi-turn session creation, retrieval, and clearing."""
        sid = asyncio.run(db_manager.create_or_get_session(None, title="Test Memory Session"))
        self.assertTrue(sid.startswith("sess_"))

        # Save turns
        asyncio.run(db_manager.save_dahoo_message("user", "Halo Dahoo", session_id=sid))
        asyncio.run(db_manager.save_dahoo_message("assistant", "Halo! Aku Dahoo.", session_id=sid))
        asyncio.run(db_manager.save_dahoo_message("user", "Berapa CPU saya?", session_id=sid))

        # Retrieve
        recent = asyncio.run(db_manager.get_recent_messages(sid, limit=5))
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0]["message"], "Halo Dahoo")
        self.assertEqual(recent[2]["message"], "Berapa CPU saya?")

        # Clear
        asyncio.run(db_manager.clear_session_messages(sid))
        recent_after = asyncio.run(db_manager.get_recent_messages(sid))
        self.assertEqual(len(recent_after), 0)

if __name__ == "__main__":
    unittest.main()
