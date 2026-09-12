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

    const timeStr = snap.timestamp ? new Date(snap.timestamp * 1000).toLocaleTimeString('en-GB') : null;

    // CPU KPI
    const cpuVal = cpu.total_percent !== undefined ? cpu.total_percent : 0;
    this.setElemText('kpi-cpu-val', `${cpuVal}%`);
    this.setElemWidth('kpi-cpu-bar', `${cpuVal}%`, cpuVal > 80 ? 'critical' : cpuVal > 60 ? 'warning' : '');
    if (this.cpuChart) this.cpuChart.push(cpuVal, timeStr);

    // RAM KPI
    const memVal = mem.percent !== undefined ? mem.percent : 0;
    const memUsedGb = roundBytesGb(mem.used_bytes || 0);
    const memTotalGb = roundBytesGb(mem.total_bytes || 0);
    this.setElemText('kpi-mem-val', `${memVal}%`);
    this.setElemText('kpi-mem-sub', `${memUsedGb} / ${memTotalGb} GB`);
    this.setElemWidth('kpi-mem-bar', `${memVal}%`, memVal > 85 ? 'critical' : memVal > 70 ? 'warning' : '');
    if (this.memChart) this.memChart.push(memVal, timeStr);

    // Storage KPI
    const storOverall = storage.overall || {};
    const storVal = storOverall.percent !== undefined ? storOverall.percent : 0;
    const storFreeGb = roundBytesGb(storOverall.free_bytes || 0);
    this.setElemText('kpi-storage-val', `${storVal}%`);
    this.setElemText('kpi-storage-sub', `${storFreeGb} GB Free`);
    this.setElemWidth('kpi-storage-bar', `${storVal}%`, storVal > 90 ? 'critical' : '');

    // Thermal KPI (CPU)
    const thermal = snap.hardware ? snap.hardware.thermal : {};
    if (thermal && thermal.cpu_temp_c !== null && thermal.cpu_temp_c !== undefined) {
      const cTemp = thermal.cpu_temp_c;
      this.setElemText('kpi-temp-val', `${cTemp}°C`);
      this.setElemText('kpi-temp-sub', 'ACPI Thermal Zone');
      const tempPercent = Math.min(100, Math.max(0, (cTemp / 100) * 100));
      this.setElemWidth('kpi-temp-bar', `${tempPercent}%`, cTemp > 85 ? 'critical' : cTemp > 70 ? 'warning' : '');
    } else {
      this.setElemText('kpi-temp-val', 'Unavailable');
      this.setElemText('kpi-temp-sub', 'Thermal zone inactive');
      this.setElemWidth('kpi-temp-bar', '0%');
    }

    // GPU Usage & Temp (Dynamic Multi-GPU Support)
    if (gpu && gpu.available) {
      const gpuName = gpu.name || 'Primary GPU';
      const gpuUtil = gpu.usage_percent !== null && gpu.usage_percent !== undefined ? gpu.usage_percent : 0;
      this.setElemText('kpi-gpu-val', `${gpuUtil}%`);
      this.setElemText('kpi-gpu-sub', `${gpuName} (${gpu.vendor || 'GPU'})`);
      this.setElemWidth('kpi-gpu-bar', `${Math.min(100, gpuUtil)}%`, gpuUtil > 80 ? 'critical' : gpuUtil > 60 ? 'warning' : '');

      if (gpu.temperature_c !== null && gpu.temperature_c !== undefined) {
        const gTemp = gpu.temperature_c;
        this.setElemText('kpi-gputemp-val', `${gTemp}°C`);
        this.setElemText('kpi-gputemp-sub', gpu.is_discrete ? 'Dedicated Diode' : 'SoC Package Diode');
        const gTempPercent = Math.min(100, Math.max(0, (gTemp / 100) * 100));
        this.setElemWidth('kpi-gputemp-bar', `${gTempPercent}%`, gTemp > 85 ? 'critical' : gTemp > 70 ? 'warning' : '');
      } else {
        this.setElemText('kpi-gputemp-val', 'Unavailable');
        this.setElemText('kpi-gputemp-sub', 'Sensor diode offline');
        this.setElemWidth('kpi-gputemp-bar', '0%');
      }
    } else {
      this.setElemText('kpi-gpu-val', 'Not available');
      this.setElemText('kpi-gpu-sub', 'No display adapter');
      this.setElemWidth('kpi-gpu-bar', '0%');
      this.setElemText('kpi-gputemp-val', 'Not available');
      this.setElemWidth('kpi-gputemp-bar', '0%');
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

    // 3. Top 5 Processes Table with Clear Descriptions & Idle Explanation
    const topProcs = snap.process ? snap.process.top_cpu : [];
    const procTbody = document.getElementById('dash-top-procs-tbody');
    if (procTbody && topProcs) {
      procTbody.innerHTML = topProcs.map(p => {
        const isIdle = p.is_idle || p.pid === 0 || p.name.toLowerCase().includes('idle');
        const cpuText = isIdle 
          ? `${p.cpu_percent_normalized || (p.cpu_percent / 8).toFixed(1)}% <span class="text-muted" style="font-size:0.65rem;">(Idle)</span>`
          : `${p.cpu_percent}%`;

        return `
          <tr>
            <td class="font-mono text-secondary">${p.pid}</td>
            <td>
              <strong>${escapeHtml(p.name)}</strong>
              ${isIdle ? '<span class="badge badge-neutral font-mono" style="margin-left: 6px; font-size: 0.65rem;">Kernel Idle</span>' : ''}
              <div class="text-muted" style="font-size: 0.7rem;">${escapeHtml(p.description || '')}</div>
            </td>
            <td class="font-mono ${isIdle ? 'text-secondary' : 'text-cyan'}">${cpuText}</td>
            <td class="font-mono">${(p.memory_bytes / (1024 * 1024)).toFixed(1)} MB</td>
            <td>
              <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.7rem;" onclick="app.inspectProcess(${p.pid})">Inspect</button>
            </td>
          </tr>
        `;
      }).join('');
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
