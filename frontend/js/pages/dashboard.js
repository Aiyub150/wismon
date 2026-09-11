/**
 * Dashboard Page Controller.
 */

class DashboardPage {
  constructor() {
    this.cpuChart = null;
    this.memChart = null;
  }

  init() {
    this.cpuChart = new MiniChart('dash-cpu-canvas', {
      color: '#3C50E0',
      unit: '%',
      maxY: 100
    });
    this.memChart = new MiniChart('dash-mem-canvas', {
      color: '#259AE6',
      unit: '%',
      maxY: 100
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));
  }

  update(snap) {
    if (!snap) return;

    // 1. Health Score
    const health = snap.health || { score: 100, status: 'Healthy', badge: 'healthy' };
    const scoreElem = document.getElementById('dash-health-score');
    const statusElem = document.getElementById('dash-health-status');
    const dialElem = document.getElementById('dash-health-dial');

    if (scoreElem) scoreElem.textContent = health.score;
    if (statusElem) {
      statusElem.textContent = health.status;
      statusElem.className = `badge badge-${health.badge}`;
    }
    if (dialElem) {
      const color = health.score >= 80 ? '#10b981' : health.score >= 60 ? '#06b6d4' : health.score >= 40 ? '#f59e0b' : '#f43f5e';
      dialElem.style.borderColor = color;
      dialElem.style.boxShadow = `0 0 20px ${color}40`;
    }

    // 2. KPI Cards
    const cpu = snap.cpu || {};
    const mem = snap.memory || {};
    const storage = snap.storage || {};
    const net = snap.network || {};
    const gpu = snap.gpu || {};
    const threats = snap.threats || [];

    // CPU KPI
    const cpuVal = cpu.total_percent !== undefined ? cpu.total_percent : 0;
    this.setElemText('kpi-cpu-val', `${cpuVal}%`);
    this.setElemWidth('kpi-cpu-bar', `${cpuVal}%`, cpuVal > 80 ? 'critical' : cpuVal > 60 ? 'warning' : '');
    if (this.cpuChart) this.cpuChart.push(cpuVal);

    // RAM KPI
    const memVal = mem.percent !== undefined ? mem.percent : 0;
    const memUsedGb = roundBytesGb(mem.used_bytes || 0);
    const memTotalGb = roundBytesGb(mem.total_bytes || 0);
    this.setElemText('kpi-mem-val', `${memVal}%`);
    this.setElemText('kpi-mem-sub', `${memUsedGb} / ${memTotalGb} GB`);
    this.setElemWidth('kpi-mem-bar', `${memVal}%`, memVal > 85 ? 'critical' : memVal > 70 ? 'warning' : '');
    if (this.memChart) this.memChart.push(memVal);

    // Storage KPI
    const storOverall = storage.overall || {};
    const storVal = storOverall.percent !== undefined ? storOverall.percent : 0;
    const storFreeGb = roundBytesGb(storOverall.free_bytes || 0);
    this.setElemText('kpi-storage-val', `${storVal}%`);
    this.setElemText('kpi-storage-sub', `${storFreeGb} GB Free`);
    this.setElemWidth('kpi-storage-bar', `${storVal}%`, storVal > 90 ? 'critical' : '');

    // Thermal KPI
    const thermal = snap.hardware ? snap.hardware.thermal : {};
    if (thermal && thermal.cpu_temp_c !== null && thermal.cpu_temp_c !== undefined) {
      this.setElemText('kpi-temp-val', `${thermal.cpu_temp_c}°C`);
      this.setElemText('kpi-temp-sub', 'ACPI Sensor');
    } else {
      this.setElemText('kpi-temp-val', 'Unavailable');
      this.setElemText('kpi-temp-sub', 'Not exposed by BIOS');
    }

    // GPU Usage & Temp
    if (gpu && gpu.available) {
      this.setElemText('kpi-gpu-val', gpu.usage_percent !== null ? `${gpu.usage_percent}%` : 'Unavailable');
      this.setElemText('kpi-gpu-sub', gpu.name || 'Dedicated GPU');
      this.setElemText('kpi-gputemp-val', gpu.temperature_c !== null ? `${gpu.temperature_c}°C` : 'Unavailable');
    } else {
      this.setElemText('kpi-gpu-val', 'Not available');
      this.setElemText('kpi-gpu-sub', 'Integrated graphics');
      this.setElemText('kpi-gputemp-val', 'Not available');
    }

    // Network Throughput
    const tput = net.throughput || {};
    const totalMbps = (((tput.bytes_recv_sec || 0) + (tput.bytes_sent_sec || 0)) * 8 / (1024 * 1024)).toFixed(2);
    this.setElemText('kpi-net-val', `${totalMbps} Mbps`);
    const dlKbs = ((tput.bytes_recv_sec || 0) / 1024).toFixed(0);
    const ulKbs = ((tput.bytes_sent_sec || 0) / 1024).toFixed(0);
    this.setElemText('kpi-net-sub', `↓ ${dlKbs} KB/s  ↑ ${ulKbs} KB/s`);

    // Threats KPI
    this.setElemText('kpi-threats-val', threats.length);
    this.setElemText('kpi-threats-sub', threats.length === 0 ? 'No active anomalies' : 'Action recommended');
    const threatCard = document.getElementById('kpi-threats-card');
    if (threatCard) {
      threatCard.style.borderColor = threats.length > 0 ? 'rgba(244, 63, 94, 0.4)' : '';
    }

    // 3. Top 5 Processes Table
    const topProcs = snap.process ? snap.process.top_cpu : [];
    const procTbody = document.getElementById('dash-top-procs-tbody');
    if (procTbody && topProcs) {
      procTbody.innerHTML = topProcs.map(p => `
        <tr>
          <td class="font-mono text-secondary">${p.pid}</td>
          <td><strong>${escapeHtml(p.name)}</strong></td>
          <td class="font-mono text-cyan">${p.cpu_percent}%</td>
          <td class="font-mono">${(p.memory_bytes / (1024 * 1024)).toFixed(1)} MB</td>
          <td>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.7rem;" onclick="app.inspectProcess(${p.pid})">Inspect</button>
          </td>
        </tr>
      `).join('');
    }
  }

  setElemText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  setElemWidth(id, width, statusClass = '') {
    const el = document.getElementById(id);
    if (el) {
      el.style.width = width;
      el.className = `progress-bar ${statusClass}`;
    }
  }
}

function roundBytesGb(bytes) {
  return (bytes / (1024 * 1024 * 1024)).toFixed(1);
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
}

window.dashboardPage = new DashboardPage();
