"""
Dahoo Assistant Engine for Windows System Monitoring.
Implements the Hybrid Assistant Architecture:
1. Local Rule & Telemetry Engine (offline, 0 tokens, real-time context)
2. Cloud AI reasoning (Gemini API via google-genai SDK, token & cost tracking)
"""

import time
import re
from typing import Dict, Any, Tuple
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, INPUT_PRICE_PER_1M, OUTPUT_PRICE_PER_1M
from backend.db import db_manager

class DahooEngine:
    def __init__(self):
        self._genai_client = None
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

    def answer_local(self, prompt: str, telemetry: Dict[str, Any]) -> str:
        """
        Local Rule Engine: Matches common user questions against live telemetry.
        Returns immediate, zero-token contextual response in Indonesian/English.
        """
        q = prompt.lower().strip()
        cpu = telemetry.get("cpu", {})
        ram = telemetry.get("memory", {})
        storage = telemetry.get("storage", {})
        network = telemetry.get("network", {})
        health = telemetry.get("health", {})
        procs = telemetry.get("process", {})
        threats = telemetry.get("threats", [])

        # CPU inquiry
        if any(w in q for w in ["cpu", "processor", "prosesor"]):
            total = cpu.get("total_percent", 0.0)
            name = cpu.get("processor_name", "Processor")
            freq = cpu.get("frequency", {}).get("current_mhz", 0)
            top_proc = procs.get("top_cpu", [{}])[0] if procs.get("top_cpu") else {}
            pname = top_proc.get("name", "none")
            pcpu = top_proc.get("cpu_percent", 0.0)

            ans = f"Aww! Penggunaan CPU kamu saat ini berada di **{total}%** pada prosesor **{name}** ({freq} MHz).\n\n"
            if total > 75:
                ans += f"⚠️ Beban CPU tergolong tinggi. Kontributor terbesar saat ini adalah proses **{pname}** ({pcpu}%)."
            else:
                ans += f"Semuanya berjalan normal. Proses teratas saat ini adalah **{pname}** ({pcpu}%)."
            return ans

        # Memory / RAM inquiry
        if any(w in q for w in ["ram", "memory", "memori"]):
            perc = ram.get("percent", 0.0)
            used_gb = round(ram.get("used_bytes", 0) / (1024**3), 1)
            total_gb = round(ram.get("total_bytes", 0) / (1024**3), 1)
            deep = ram.get("deep", {})
            paged_mb = round(deep.get("paged_pool", 0) / (1024**2), 1)
            commit_gb = round(deep.get("commit_charge", 0) / (1024**3), 1)

            ans = f"Saat ini penggunaan RAM adalah **{perc}%** ({used_gb} GB dari total {total_gb} GB).\n\n"
            ans += f"- **Paged Pool**: {paged_mb} MB\n- **Commit Charge**: {commit_gb} GB\n"
            if perc > 85:
                ans += "⚠️ Tekanan memori cukup tinggi. Sebaiknya periksa aplikasi yang menggunakan banyak memori."
            else:
                ans += "Kapasitas memori masih dalam batas aman dan stabil."
            return ans

        # Storage / Disk inquiry
        if any(w in q for w in ["storage", "disk", "penyimpanan", "harddisk", "ssd"]):
            overall = storage.get("overall", {})
            perc = overall.get("percent", 0.0)
            free_gb = round(overall.get("free_bytes", 0) / (1024**3), 1)
            read_speed = storage.get("io", {}).get("read_bytes_sec", 0.0) / (1024**2)
            write_speed = storage.get("io", {}).get("write_bytes_sec", 0.0) / (1024**2)

            return (
                f"Kondisi storage kamu saat ini terpakai **{perc}%**, dengan sisa ruang bebas **{free_gb} GB**.\n\n"
                f"- **Live Read**: {read_speed:.2f} MB/s\n"
                f"- **Live Write**: {write_speed:.2f} MB/s\n"
                f"Kamu bisa membuka menu **Storage Analyzer** jika ingin melihat file berukuran besar atau file sementara yang bisa dibersihkan."
            )

        # Network inquiry
        if any(w in q for w in ["network", "internet", "jaringan", "koneksi", "download", "upload", "bandwidth"]):
            tput = network.get("throughput", {})
            dl_mbps = round((tput.get("bytes_recv_sec", 0) * 8) / (1024 * 1024), 2)
            ul_mbps = round((tput.get("bytes_sent_sec", 0) * 8) / (1024 * 1024), 2)
            ifaces = [i["name"] for i in network.get("interfaces", []) if i.get("is_up")]

            return (
                f"Status jaringan kamu saat ini:\n\n"
                f"- **Download Throughput**: {dl_mbps} Mbps\n"
                f"- **Upload Throughput**: {ul_mbps} Mbps\n"
                f"- **Interface Aktif**: {', '.join(ifaces) if ifaces else 'Tidak terdeteksi'}\n"
                f"Koneksi aktif dapat dipantau di menu **Connections**."
            )

        # Health / Status inquiry
        if any(w in q for w in ["kesehatan", "health", "kondisi", "status", "laptop", "komputer", "sehat"]):
            score = health.get("score", 100)
            status = health.get("status", "Healthy")
            t_count = len(threats)

            return (
                f"Health Score sistem kamu saat ini adalah **{score}/100** ({status}).\n\n"
                f"- CPU: {telemetry.get('cpu', {}).get('total_percent', 0)}%\n"
                f"- RAM: {ram.get('percent', 0)}%\n"
                f"- Ancaman Aktif: {t_count}\n\n"
                f"{'Semua subsistem berjalan prima tanpa kendala.' if score >= 80 else 'Perlu perhatian pada modul yang membebani sistem.'}"
            )

        # Security / Threats inquiry
        if any(w in q for w in ["threat", "keamanan", "security", "bahaya", "virus", "malware"]):
            t_count = len(threats)
            if t_count == 0:
                return "Kabar baik! Saat ini **tidak ada ancaman atau anomali aktif** yang terdeteksi di Threat Center. Sistem aman."
            else:
                top_t = threats[0]
                return (
                    f"⚠️ Terdapat **{t_count} event anomali aktif** di Threat Center:\n\n"
                    f"- **Kategori**: {top_t.get('category')}\n"
                    f"- **Target**: {top_t.get('target')}\n"
                    f"- **Tingkat**: {top_t.get('severity')}\n"
                    f"- **Rekomendasi**: {top_t.get('recommended_action')}\n\n"
                    f"Silakan buka tab **Threat Center** untuk meninjau opsi mitigasi."
                )

        # Process inquiry
        if any(w in q for w in ["process", "proses", "aplikasi", "task"]):
            top = procs.get("top_cpu", [])
            lines = [f"{i+1}. **{p['name']}** (PID {p['pid']}) — CPU: {p['cpu_percent']}%, RAM: {round(p['memory_bytes']/(1024**2), 1)} MB" for i, p in enumerate(top[:3])]
            return "Top 3 proses terberat saat ini:\n\n" + "\n".join(lines)

        # Fallback local response
        return (
            "Aww! Aku Dahoo, asisten pemantau sistemmu.\n\n"
            "Kamu bisa menanyakan hal seperti:\n"
            "- *Bagaimana kondisi CPU saat ini?*\n"
            "- *Berapa penggunaan RAM dan Commit Charge?*\n"
            "- *Apakah ada anomali atau ancaman aktif?*\n"
            "- *Berapa kecepatan download & upload jaringan?*\n"
            "- *Proses apa yang membebani komputer?*\n\n"
            "Jika GEMINI_API_KEY dikonfigurasi di `.env`, kamu juga bisa mengaktifkan mode Cloud AI untuk analisis lebih mendalam!"
        )

    async def chat(self, message: str, telemetry: Dict[str, Any], use_cloud: bool = False) -> Dict[str, Any]:
        """Processes a chat query with automatic routing to local engine or Gemini Cloud LLM."""
        if not use_cloud or not self._genai_client:
            reply = self.answer_local(message, telemetry)
            await db_manager.save_dahoo_message("user", message)
            await db_manager.save_dahoo_message("assistant", reply, model="local-rule-engine", in_tokens=0, out_tokens=0, cost=0.0)
            return {
                "reply": reply,
                "engine": "local",
                "model": "Dahoo Local Engine (Offline)",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0
            }

        # Cloud AI reasoning via Gemini
        system_context = (
            f"You are Dahoo, a friendly, ultra-competent mascot and system engineer assistant in Windows System Monitoring. "
            f"Current System State: Health={telemetry.get('health', {}).get('score', 100)}/100 ({telemetry.get('health', {}).get('status', 'Healthy')}), "
            f"CPU={telemetry.get('cpu', {}).get('total_percent', 0)}% on {telemetry.get('cpu', {}).get('processor_name', 'Windows')}, "
            f"RAM={telemetry.get('memory', {}).get('percent', 0)}%, "
            f"Active Threats={len(telemetry.get('threats', []))}. "
            f"Always provide insightful, concise, technical yet friendly recommendations. Keep it grounded in real telemetry."
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
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "estimated_cost": round(cost, 6)
            }
        except Exception as e:
            fallback = self.answer_local(message, telemetry)
            return {
                "reply": f"*(Cloud AI unreachable: {e}. Menjawab menggunakan Local Engine)*\n\n{fallback}",
                "engine": "local-fallback",
                "model": "local-fallback",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0
            }

dahoo_engine = DahooEngine()
