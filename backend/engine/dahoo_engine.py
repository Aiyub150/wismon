"""
Dahoo Assistant Engine for Windows System Monitoring.
Implements the Hybrid Assistant Architecture with Detect-Ask-Act:
1. Local Intelligence & Telemetry Engine (offline, 0 tokens, real-time context, Detect-Ask-Act)
2. Cloud AI reasoning (Gemini API via google-genai SDK, token & cost tracking)
"""

import time
import re
from typing import Dict, Any, Tuple, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, INPUT_PRICE_PER_1M, OUTPUT_PRICE_PER_1M
from backend.db import db_manager
from backend.engine.threat_center import threat_center
from backend.engine.storage_analyzer import storage_analyzer

class DahooEngine:
    def __init__(self):
        self._genai_client = None
        self._pending_action: Optional[Dict[str, Any]] = None
        self._last_alert_time: float = 0.0
        self._last_alert_type: str = ""

        if GEMINI_API_KEY:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception:
                self._genai_client = None

    def get_expression(self, health_score: int, threat_count: int, cpu_percent: float) -> str:
        """Determines Dahoo's visual expression based on system condition."""
        if threat_count > 0 or health_score < 40:
            return "alert"
        if cpu_percent > 85 or health_score < 65:
            return "worried"
        if health_score >= 85:
            return "happy"
        return "normal"

    async def execute_action(self, action_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a real remedial action confirmed by the user.
        Part of the Detect-Ask-Act capability.
        """
        params = params or {}

        # 1. Throttle / Cooldown high CPU process
        if action_type in ("COOLDOWN_PROCESS", "THROTTLE_PROCESS"):
            pid = params.get("pid")
            if not pid and self._pending_action and self._pending_action.get("type") in ("COOLDOWN_PROCESS", "THROTTLE_PROCESS"):
                pid = self._pending_action.get("params", {}).get("pid")
            if not pid:
                return {"success": False, "message": "Tidak ada target PID proses yang valid untuk ditangguhkan."}

            res = await threat_center.throttle_and_cooldown_process(int(pid), duration=3.5)
            self._pending_action = None
            return res

        # 2. Trim working set RAM
        elif action_type in ("TRIM_MEMORY", "OPTIMIZE_RAM"):
            res = threat_center.trim_system_memory()
            self._pending_action = None
            return res

        # 3. Clean temporary files
        elif action_type in ("CLEAN_TEMP", "CLEANUP_TEMP"):
            res = storage_analyzer.clean_user_temp_files()
            self._pending_action = None
            return res

        # 4. Resolve Security Threat
        elif action_type == "RESOLVE_THREAT":
            threat_id = params.get("threat_id")
            if not threat_id and self._pending_action:
                threat_id = self._pending_action.get("params", {}).get("threat_id")
            if not threat_id:
                return {"success": False, "message": "ID ancaman tidak ditemukan."}

            # If there's an active process attached, also cooldown
            t_obj = next((t for t in threat_center.get_threats() if t["id"] == threat_id), None)
            if t_obj and t_obj.get("pid"):
                await threat_center.throttle_and_cooldown_process(t_obj["pid"], duration=3.5)

            await threat_center.update_threat_status(threat_id, "RESOLVED", action="Dimediasi dan diselesaikan via Dahoo Assistant")
            self._pending_action = None
            return {"success": True, "message": f"Ancaman {threat_id} berhasil dimitigasi dan ditandai selesai."}

        return {"success": False, "message": f"Aksi '{action_type}' tidak dikenali."}

    async def answer_local(self, prompt: str, telemetry: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Local Rule Engine: Matches user questions against live telemetry using flexible intent recognition.
        Returns: (reply_text, optional_action_dict)
        """
        q = prompt.lower().strip()
        cpu = telemetry.get("cpu", {})
        ram = telemetry.get("memory", {})
        storage = telemetry.get("storage", {})
        network = telemetry.get("network", {})
        health = telemetry.get("health", {})
        procs = telemetry.get("process", {})
        threats = telemetry.get("threats", [])
        hw = telemetry.get("hardware", {})
        gpu = telemetry.get("gpu", {})

        top_procs = procs.get("top_cpu", [])
        active_top_proc = next((p for p in top_procs if p.get("pid", 0) > 0 and not ("idle" in p.get("name", "").lower())), None)
        if not active_top_proc and top_procs:
            active_top_proc = top_procs[0]

        # 0. User Confirmation / Act on Pending Action
        confirm_words = ["ya", "yes", "oke", "ok", "lakukan", "setuju", "eksekusi", "jalankan", "perbaiki", "bantu", "boleh", "sip", "yup", "siap", "tangguhkan", "bersihkan", "gas"]
        cancel_words = ["tidak", "no", "batal", "jangan", "skip", "abaikan", "ga usah", "gak", "nggak", "nanti"]

        if any(q == w or q.startswith(w + " ") or q.endswith(" " + w) for w in confirm_words):
            if self._pending_action:
                act = self._pending_action
                res = await self.execute_action(act["type"], act.get("params", {}))
                if res.get("success"):
                    return f"✅ **Tindakan Berhasil Dijalankan!**\n\n{res.get('message')}\n\nSistem kini terpantau lebih optimal dan stabil.", None
                else:
                    return f"⚠️ **Upaya tindakan mengalami kendala:** {res.get('message')}", None
            else:
                return "Aww, saat ini belum ada tindakan perbaikan yang tertunda. Ada yang ingin kamu tanyakan tentang CPU, RAM, Suhu, atau Keamanan?", None

        if any(q == w or q.startswith(w + " ") or q.endswith(" " + w) for w in cancel_words):
            if self._pending_action:
                self._pending_action = None
                return "Baik! Tindakan dibatalkan. Aku akan tetap memantau sistemmu seperti biasa. Hubungi aku kapan saja jika butuh bantuan! 🐺", None

        # 1. Slowness / Performance / Lag inquiry
        if any(w in q for w in ["lemot", "lambat", "lag", "berat", "lelet", "macet", "freeze", "kinerja", "performa", "tangguh", "hang", "slow", "bikin berat", "kenapa"]):
            total_cpu = cpu.get("total_percent", 0.0)
            ram_pct = ram.get("percent", 0.0)
            pname = active_top_proc.get("name", "Proses Sistem") if active_top_proc else "None"
            ppid = active_top_proc.get("pid", 0) if active_top_proc else 0
            pcpu = active_top_proc.get("cpu_percent", 0.0) if active_top_proc else 0.0

            ans = f"Aku telah memeriksa kondisi sistem saat ini:\n\n"
            ans += f"- **Beban CPU**: {total_cpu}%\n"
            ans += f"- **Penggunaan RAM**: {ram_pct}%\n"

            if active_top_proc and (pcpu > 20.0 or total_cpu > 65.0):
                ans += f"- **Aplikasi Paling Berat**: **{pname}** (PID: {ppid}) menyerap **{pcpu}% CPU**.\n\n"
                ans += f"💡 **Saran Dahoo**: Mau aku bantu **menangguhkan (pause) proses {pname} selama 3.5 detik** agar CPU stabil dan dingin kembali?"
                self._pending_action = {
                    "type": "COOLDOWN_PROCESS",
                    "params": {"pid": ppid, "name": pname},
                    "label": f"Tangguhkan {pname} (3.5s)"
                }
                return ans, self._pending_action
            elif ram_pct > 80.0:
                ans += f"\n⚠️ RAM kamu cukup padat ({ram_pct}%). Mau aku bantu **bersihkan working set memori** sekarang?"
                self._pending_action = {
                    "type": "TRIM_MEMORY",
                    "params": {},
                    "label": "Bebaskan Cache Memori"
                }
                return ans, self._pending_action
            else:
                ans += f"\nSecara umum sistem berjalan dalam batas toleransi normal. Tidak ada proses anomali yang membebani secara kritis."
                return ans, None

        # 2. CPU / Processor inquiry
        if any(w in q for w in ["cpu", "processor", "prosesor", "core"]):
            total = cpu.get("total_percent", 0.0)
            name = cpu.get("processor_name", "Processor")
            freq = cpu.get("frequency", {}).get("current_mhz", 0)
            pname = active_top_proc.get("name", "none") if active_top_proc else "None"
            ppid = active_top_proc.get("pid", 0) if active_top_proc else 0
            pcpu = active_top_proc.get("cpu_percent", 0.0) if active_top_proc else 0.0

            ans = f"Penggunaan CPU saat ini berada di **{total}%** pada **{name}** ({freq} MHz).\n\n"
            if total > 70 and active_top_proc:
                ans += f"⚠️ Proses **{pname}** (PID: {ppid}) adalah kontributor terbesar saat ini ({pcpu}%).\n\n"
                ans += f"Apakah kamu ingin aku **menangguhkan proses {pname} sejenak (3.5 detik)** untuk meredakan beban prosesor?"
                self._pending_action = {
                    "type": "COOLDOWN_PROCESS",
                    "params": {"pid": ppid, "name": pname},
                    "label": f"Tangguhkan {pname} (3.5s)"
                }
                return ans, self._pending_action
            else:
                ans += f"Proses teratas saat ini adalah **{pname}** ({pcpu}%). Kinerja prosesor masih dalam batas aman."
                return ans, None

        # 3. Memory / RAM inquiry
        if any(w in q for w in ["ram", "memory", "memori", "commit", "paged"]):
            perc = ram.get("percent", 0.0)
            used_gb = round(ram.get("used_bytes", 0) / (1024**3), 1)
            total_gb = round(ram.get("total_bytes", 0) / (1024**3), 1)
            deep = ram.get("deep", {})
            paged_mb = round(deep.get("paged_pool", 0) / (1024**2), 1)
            commit_gb = round(deep.get("commit_charge", 0) / (1024**3), 1)

            ans = f"Saat ini penggunaan RAM mencapai **{perc}%** ({used_gb} GB dari total {total_gb} GB).\n\n"
            ans += f"- **Paged Pool**: {paged_mb} MB\n"
            ans += f"- **Commit Charge**: {commit_gb} GB\n\n"

            if perc > 75:
                ans += f"💡 **Saran Dahoo**: Memori cukup padat. Mau aku bantu **bersihkan cache working set RAM** agar ruang memori lebih lega?"
                self._pending_action = {
                    "type": "TRIM_MEMORY",
                    "params": {},
                    "label": "Bebaskan Cache RAM"
                }
                return ans, self._pending_action
            else:
                ans += "Kapasitas RAM masih stabil dan tidak membutuhkan pembersihan darurat."
                return ans, None

        # 4. Temperature / Thermal inquiry
        if any(w in q for w in ["suhu", "panas", "temperatur", "temperature", "thermal", "overheat", "kipas", "fan", "adem", "dingin"]):
            thermal = hw.get("thermal", {})
            cpu_temp = thermal.get("cpu_temp_c")
            gpu_temp = gpu.get("temperature_c")

            ans = f"Pemantauan suhu perangkat saat ini:\n\n"
            if cpu_temp is not None:
                ans += f"- **Suhu CPU / SoC**: **{cpu_temp}°C** ({'Normal' if cpu_temp < 70 else 'Hangat' if cpu_temp < 85 else 'Kritis ⚠️'})\n"
            else:
                ans += f"- **Suhu CPU**: Sensor sedang membaca siklus termal.\n"

            if gpu_temp is not None:
                ans += f"- **Suhu GPU**: **{gpu_temp}°C** ({'Dingin' if gpu_temp < 65 else 'Optimal' if gpu_temp < 80 else 'Tinggi ⚠️'})\n"
            else:
                ans += f"- **Suhu GPU**: Mengikuti diode thermal SoC package.\n"

            if (cpu_temp and cpu_temp > 80) or (gpu_temp and gpu_temp > 80):
                if active_top_proc:
                    ans += f"\nSuhu sedang agak tinggi karena beban komputasi. Mau aku bantu menangguhkan proses **{active_top_proc.get('name')}** (PID: {active_top_proc.get('pid')}) selama 3.5 detik untuk membantu pendinginan?"
                    self._pending_action = {
                        "type": "COOLDOWN_PROCESS",
                        "params": {"pid": active_top_proc.get("pid"), "name": active_top_proc.get("name")},
                        "label": f"Pendinginan via {active_top_proc.get('name')}"
                    }
                    return ans, self._pending_action

            ans += "\nSecara keseluruhan profil pendinginan laptop/komputer bekerja dengan baik."
            return ans, None

        # 5. GPU / Graphics inquiry
        if any(w in q for w in ["gpu", "vga", "grafis", "graphics", "display adapter", "iris", "radeon", "nvidia", "geforce"]):
            g_name = gpu.get("name", "Integrated Graphics")
            g_vendor = gpu.get("vendor", "Intel/AMD")
            g_util = gpu.get("usage_percent", 0.0)
            g_vram_u = round((gpu.get("vram_used_bytes", 0) or 0) / (1024**2), 0)
            g_vram_t = round((gpu.get("vram_total_bytes", 0) or 0) / (1024**2), 0)
            g_temp = gpu.get("temperature_c", "—")

            return (
                f"Informasi GPU yang aktif:\n\n"
                f"- **Model**: **{g_name}** ({g_vendor})\n"
                f"- **Engine Utilization**: **{g_util}%**\n"
                f"- **VRAM Digunakan**: {g_vram_u} / {g_vram_t} MB\n"
                f"- **Suhu Diode**: {g_temp}°C\n\n"
                f"GPU terdeteksi dan dipantau penuh melalui Windows DirectX/PDH Subsystem."
            ), None

        # 6. Storage / Disk inquiry
        if any(w in q for w in ["storage", "disk", "penyimpanan", "harddisk", "ssd", "sampah", "temp", "temporary"]):
            overall = storage.get("overall", {})
            perc = overall.get("percent", 0.0)
            free_gb = round(overall.get("free_bytes", 0) / (1024**3), 1)

            ans = (
                f"Kondisi storage kamu saat ini:\n\n"
                f"- **Terpakai**: **{perc}%**\n"
                f"- **Sisa Ruang Bebas**: **{free_gb} GB**\n\n"
                f"Mau aku bantu **membersihkan file temporary (sampah) di folder Temp** sekarang untuk menghemat ruang disk?"
            )
            self._pending_action = {
                "type": "CLEAN_TEMP",
                "params": {},
                "label": "Bersihkan File Temp"
            }
            return ans, self._pending_action

        # 7. Network inquiry
        if any(w in q for w in ["network", "internet", "jaringan", "koneksi", "download", "upload", "bandwidth"]):
            tput = network.get("throughput", {})
            dl_mbps = round((tput.get("bytes_recv_sec", 0) * 8) / (1024 * 1024), 2)
            ul_mbps = round((tput.get("bytes_sent_sec", 0) * 8) / (1024 * 1024), 2)
            ifaces = [i["name"] for i in network.get("interfaces", []) if i.get("is_up")]

            return (
                f"Status throughput jaringan kamu saat ini:\n\n"
                f"- **Kecepatan Download**: {dl_mbps} Mbps\n"
                f"- **Kecepatan Upload**: {ul_mbps} Mbps\n"
                f"- **Interface Aktif**: {', '.join(ifaces) if ifaces else 'Terkoneksi'}\n\n"
                f"Koneksi jaringan dan socket aktif berjalan stabil."
            ), None

        # 8. Security / Threat inquiry
        if any(w in q for w in ["threat", "keamanan", "security", "bahaya", "virus", "malware", "anomali", "aman"]):
            t_count = len(threats)
            if t_count == 0:
                return "Kabar baik! Saat ini **tidak ada ancaman atau anomali aktif** yang terdeteksi di Threat Center. Sistem aman terkendali. 🛡️", None
            else:
                top_t = threats[0]
                ans = (
                    f"⚠️ Terdapat **{t_count} anomali keamanan** aktif di Threat Center:\n\n"
                    f"- **Kategori**: {top_t.get('category')}\n"
                    f"- **Target**: {top_t.get('target')}\n"
                    f"- **Tingkat Bahaya**: {top_t.get('severity')}\n"
                    f"- **Rekomendasi**: {top_t.get('recommended_action')}\n\n"
                    f"Apakah kamu ingin aku **langsung memitigasi anomali ini** sekarang?"
                )
                self._pending_action = {
                    "type": "RESOLVE_THREAT",
                    "params": {"threat_id": top_t.get("id")},
                    "label": "Mitigasi Ancaman Ini"
                }
                return ans, self._pending_action

        # 9. General Greeting / Identity / Help
        if any(w in q for w in ["halo", "hai", "hello", "hi", "siapa kamu", "bisa apa", "fitur", "help", "bantuan", "pagi", "siang", "malam", "dahoo"]):
            return (
                "Aww! Halo, aku **Dahoo**, asisten pemantau dan optimasi sistem Windows kamu! 🐺\n\n"
                "Dalam mode offline cerdas ini, aku dapat langsung membantu kamu:\n"
                "- ⚡ **Deteksi & Stabilkan Beban CPU** (menangguhkan sejenak proses yang membuat lag)\n"
                "- 🧹 **Bebaskan Cache RAM** (membersihkan working set memori agar komputer tidak berat)\n"
                "- 🌡️ **Cek Suhu Hardware** (memantau suhu CPU & GPU dari sensor ACPI/DirectX)\n"
                "- 🛡️ **Mitigasi Ancaman Keamanan** (mengatasi anomali di Threat Center)\n"
                "- 🗑️ **Bersihkan File Temp / Sampah** (menghemat ruang penyimpanan disk)\n\n"
                "Silakan tanyakan: *'Kenapa komputer berat?'*, *'Berapa suhu CPU saat ini?'*, atau *'Bersihkan RAM'*!"
            ), None

        # 10. Fallback for completely unrelated queries (General knowledge, poems, etc.)
        return (
            "Aww! Aku Dahoo, asisten khusus pemantau dan pemeliharaan performa Windows.\n\n"
            "Pertanyaan ini di luar cakupan pemantauan performa & hardware komputermu. "
            "Untuk percakapan umum atau penalaran kreatif mendalam, kamu dapat mengaktifkan Cloud AI dengan menambahkan `GEMINI_API_KEY` di `.env`.\n\n"
            "Jika ingin memeriksa kondisi komputermu, coba tanyakan: *'Bagaimana kondisi CPU dan RAM saat ini?'*"
        ), None

    async def chat(self, message: str, telemetry: Dict[str, Any], use_cloud: bool = False) -> Dict[str, Any]:
        """Processes a chat query with automatic routing to local engine or Gemini Cloud LLM."""
        if not use_cloud or not self._genai_client:
            reply, action_data = await self.answer_local(message, telemetry)
            await db_manager.save_dahoo_message("user", message)
            await db_manager.save_dahoo_message("assistant", reply, model="local-rule-engine", in_tokens=0, out_tokens=0, cost=0.0)
            return {
                "reply": reply,
                "engine": "local",
                "model": "Dahoo Local Engine (Offline)",
                "action": action_data,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0
            }

        # Cloud AI reasoning via Gemini (with sanitized telemetry context)
        cpu_name = telemetry.get('cpu', {}).get('processor_name', 'Windows Processor')
        system_context = (
            f"You are Dahoo, a friendly, ultra-competent mascot and system observability assistant in WISMON (Windows System Monitoring). "
            f"Current System State: Health={telemetry.get('health', {}).get('score', 100)}/100 ({telemetry.get('health', {}).get('status', 'Healthy')}), "
            f"CPU={telemetry.get('cpu', {}).get('total_percent', 0)}% on {cpu_name}, "
            f"RAM={telemetry.get('memory', {}).get('percent', 0)}%, "
            f"Active Threats={len(telemetry.get('threats', []))}. "
            f"Always provide insightful, concise, technical yet friendly recommendations. Keep it grounded in real telemetry. "
            f"Do not ask for or output sensitive credentials or full Windows user account directories."
        )

        try:
            from google.genai import types
            response = self._genai_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=system_context,
                    temperature=0.7,
                )
            )
            reply = response.text or "Aww, maaf aku sedang kesulitan berpikir saat ini."
            in_tokens = 0
            out_tokens = 0
            if response.usage_metadata:
                in_tokens = response.usage_metadata.prompt_token_count or 0
                out_tokens = response.usage_metadata.candidates_token_count or 0

            cost = ((in_tokens / 1_000_000) * INPUT_PRICE_PER_1M) + ((out_tokens / 1_000_000) * OUTPUT_PRICE_PER_1M)

            await db_manager.save_dahoo_message("user", message)
            await db_manager.save_dahoo_message("assistant", reply, model=GEMINI_MODEL, in_tokens=in_tokens, out_tokens=out_tokens, cost=cost)

            return {
                "reply": reply,
                "engine": "cloud",
                "model": GEMINI_MODEL,
                "action": None,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "estimated_cost": round(cost, 6)
            }
        except Exception:
            reply, action_data = await self.answer_local(message, telemetry)
            return {
                "reply": f"*(Cloud AI sementara tidak tersedia. Beralih otomatis ke Local Engine)*\n\n{reply}",
                "engine": "local-fallback",
                "model": "Local Telemetry Rule Engine (Offline Fallback)",
                "action": action_data,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0
            }

dahoo_engine = DahooEngine()
