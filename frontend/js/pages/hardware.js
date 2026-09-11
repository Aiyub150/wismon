/**
 * Hardware, GPU, Battery & Platform Page Controller.
 */

class HardwarePage {
  constructor() {}

  init() {
    window.addEventListener('telemetry-update', (e) => this.update(e.detail));
  }

  update(snap) {
    if (!snap) return;
    const hw = snap.hardware || {};
    const gpu = snap.gpu || {};
    const sys = hw.system_info || {};
    const battery = hw.battery || {};
    const thermal = hw.thermal || {};

    // 1. GPU Card
    const gpuNameEl = document.getElementById('hw-gpu-name');
    const gpuUsageEl = document.getElementById('hw-gpu-usage');
    const gpuVramEl = document.getElementById('hw-gpu-vram');
    const gpuTempEl = document.getElementById('hw-gpu-temp');
    const gpuStatusEl = document.getElementById('hw-gpu-status');

    if (gpuNameEl) gpuNameEl.textContent = gpu.name || 'Unavailable';
    if (gpuUsageEl) gpuUsageEl.textContent = gpu.usage_percent !== null && gpu.usage_percent !== undefined ? `${gpu.usage_percent}%` : 'Unavailable';
    if (gpuVramEl) {
      if (gpu.vram_total_bytes) {
        const totalMb = (gpu.vram_total_bytes / (1024**2)).toFixed(0);
        const usedMb = gpu.vram_used_bytes ? (gpu.vram_used_bytes / (1024**2)).toFixed(0) : '—';
        gpuVramEl.textContent = `${usedMb} / ${totalMb} MB`;
      } else {
        gpuVramEl.textContent = 'Unavailable';
      }
    }
    if (gpuTempEl) gpuTempEl.textContent = gpu.temperature_c !== null && gpu.temperature_c !== undefined ? `${gpu.temperature_c}°C` : 'Unavailable';
    if (gpuStatusEl) gpuStatusEl.textContent = gpu.status || 'Unavailable';

    // 2. Battery Card
    const batPercentEl = document.getElementById('hw-battery-percent');
    const batStateEl = document.getElementById('hw-battery-state');
    const batBar = document.getElementById('hw-battery-bar');

    if (battery.available) {
      if (batPercentEl) batPercentEl.textContent = `${battery.percent}%`;
      if (batStateEl) batStateEl.textContent = battery.power_plugged ? '⚡ Plugged In (Charging)' : 'Discharging';
      if (batBar) batBar.style.width = `${battery.percent}%`;
    } else {
      if (batPercentEl) batPercentEl.textContent = 'Not Supported';
      if (batStateEl) batStateEl.textContent = 'Desktop Workstation (AC Power)';
      if (batBar) batBar.style.width = '100%';
    }

    // 3. Thermal Zones
    const thermalContainer = document.getElementById('hw-thermal-zones');
    if (thermalContainer) {
      if (thermal.available && thermal.zones && thermal.zones.length > 0) {
        thermalContainer.innerHTML = thermal.zones.map(z => `
          <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-subtle);">
            <span>${escapeHtml(z.name)}</span>
            <strong class="font-mono text-cyan">${z.temperature_c}°C</strong>
          </div>
        `).join('');
      } else {
        thermalContainer.innerHTML = `<div class="text-muted" style="font-size: 0.8rem;">${thermal.status || 'Thermal sensors unavailable on this hardware.'}</div>`;
      }
    }

    // 4. System Platform Info
    document.getElementById('hw-sys-os').textContent = `${sys.system || 'Windows'} ${sys.release || ''} (Build ${sys.version || ''})`;
    document.getElementById('hw-sys-arch').textContent = sys.architecture || 'x86_64';
    document.getElementById('hw-sys-proc').textContent = sys.processor || 'Central Processor';
    document.getElementById('hw-sys-host').textContent = sys.hostname || 'localhost';

    const uptimeSec = hw.uptime_seconds || 0;
    const hours = Math.floor(uptimeSec / 3600);
    const mins = Math.floor((uptimeSec % 3600) / 60);
    document.getElementById('hw-sys-uptime').textContent = `${hours} hours, ${mins} minutes`;
  }
}

window.hardwarePage = new HardwarePage();
