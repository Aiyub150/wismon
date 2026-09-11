/**
 * Hardware, Multi-GPU, Battery & Platform Page Controller.
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

    // 1. Dynamic Multi-GPU Rendering (Intel, AMD, NVIDIA)
    const gpuContainer = document.getElementById('hw-gpus-container') || document.getElementById('hw-gpu-card');
    const gpusList = gpu.gpus || [];

    if (gpuContainer) {
      if (gpusList.length > 0) {
        gpuContainer.innerHTML = gpusList.map(g => {
          const vramTotalMb = g.vram_total_bytes ? (g.vram_total_bytes / (1024**2)).toFixed(0) : '—';
          const vramUsedMb = g.vram_used_bytes ? (g.vram_used_bytes / (1024**2)).toFixed(0) : '—';
          const utilVal = g.usage_percent !== null && g.usage_percent !== undefined ? g.usage_percent : 0;
          const tempVal = g.temperature_c !== null && g.temperature_c !== undefined ? `${g.temperature_c}°C` : 'Sensor unavailable';

          const vendorBadge = g.vendor === 'NVIDIA' ? 'badge-healthy' : g.vendor === 'Intel' ? 'badge-info' : 'badge-primary';

          return `
            <div class="card" style="margin-bottom: 1rem;">
              <div class="card-header" style="margin-bottom: 0.8rem; padding-bottom: 0.6rem;">
                <div class="card-title">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                    <rect width="20" height="14" x="2" y="3" rx="2"/>
                    <line x1="8" x2="16" y1="21" y2="21"/>
                    <line x1="12" x2="12" y1="17" y2="21"/>
                  </svg>
                  <span>${escapeHtml(g.name)}</span>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                  <span class="badge ${vendorBadge} font-mono">${g.vendor}</span>
                  <span class="badge badge-neutral font-mono">${g.is_discrete ? 'Discrete' : 'Integrated'}</span>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                <div>
                  <div class="text-muted" style="font-size: 0.75rem;">Engine Utilization (3D)</div>
                  <div style="font-size: 1.5rem; font-weight: 700; font-family: var(--font-display); color: var(--color-primary);">${utilVal}%</div>
                  <div class="progress-container" style="height: 6px; margin-top: 0.4rem;">
                    <div class="progress-bar ${utilVal > 80 ? 'critical' : utilVal > 50 ? 'warning' : ''}" style="width: ${Math.min(100, utilVal)}%;"></div>
                  </div>
                </div>

                <div>
                  <div class="text-muted" style="font-size: 0.75rem;">Graphics Memory (VRAM)</div>
                  <div style="font-size: 1.15rem; font-weight: 600; font-family: var(--font-mono);">${vramUsedMb} / ${vramTotalMb} MB</div>
                  <div class="text-muted font-mono" style="font-size: 0.7rem; margin-top: 0.2rem;">${escapeHtml(g.vram_type || 'DirectX Shared / Dedicated')}</div>
                </div>

                <div>
                  <div class="text-muted" style="font-size: 0.75rem;">Temperature & Thermals</div>
                  <div style="font-size: 1.15rem; font-weight: 600; font-family: var(--font-mono); color: var(--text-primary);">${tempVal}</div>
                  <div class="text-muted" style="font-size: 0.7rem; margin-top: 0.2rem;">Driver: ${escapeHtml(g.driver_version || 'WDDM Driver')}</div>
                </div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        gpuContainer.innerHTML = `
          <div class="card">
            <div class="text-muted text-center" style="padding: 1.5rem;">No graphics processing units detected.</div>
          </div>
        `;
      }
    }

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
    const osEl = document.getElementById('hw-sys-os');
    const archEl = document.getElementById('hw-sys-arch');
    const procEl = document.getElementById('hw-sys-proc');
    const hostEl = document.getElementById('hw-sys-host');
    const uptimeEl = document.getElementById('hw-sys-uptime');

    if (osEl) osEl.textContent = `${sys.system || 'Windows'} ${sys.release || ''} (Build ${sys.version || ''})`;
    if (archEl) archEl.textContent = sys.architecture || 'x86_64';
    if (procEl) procEl.textContent = sys.processor || 'Central Processor';
    if (hostEl) hostEl.textContent = sys.hostname || 'localhost';

    const uptimeSec = hw.uptime_seconds || 0;
    const hours = Math.floor(uptimeSec / 3600);
    const mins = Math.floor((uptimeSec % 3600) / 60);
    if (uptimeEl) uptimeEl.textContent = `${hours} hours, ${mins} minutes`;
  }
}

window.hardwarePage = new HardwarePage();
