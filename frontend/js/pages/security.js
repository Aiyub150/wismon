/**
 * Threat Center & Security Page Controller.
 */

class SecurityPage {
  constructor() {
    this.threats = [];
  }

  init() {
    window.addEventListener('telemetry-update', (e) => {
      this.threats = e.detail?.threats || [];
      this.renderThreats();
    });
    window.addEventListener('threat-resolved', () => {
      this.fetchEventHistory();
    });
    this.fetchEventHistory();
  }

  async mitigateAllThreats() {
    const btn = document.getElementById('security-mitigate-all-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '⚡ Menjalankan Mitigasi Massal...';
    }
    if (window.showToast) {
      window.showToast('info', 'Mengeksekusi mitigasi untuk semua ancaman sistem...', 'Batch Mitigation', 3000);
    }
    try {
      const res = await fetch('/api/security/mitigate-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true })
      });
      const data = await res.json();
      if (data.success) {
        if (window.showToast) {
          window.showToast('success', data.message || 'Semua anomali berhasil dimitigasi.', 'Mitigasi Massal Selesai');
        }
        this.fetchEventHistory();
        window.dispatchEvent(new CustomEvent('threat-resolved', { detail: data }));
      } else {
        if (window.showToast) {
          window.showToast('danger', data.message || 'Gagal memitigasi anomali.', 'Mitigasi Gagal');
        }
      }
    } catch (e) {
      if (window.showToast) {
        window.showToast('danger', 'Error: ' + e.message, 'Koneksi Terputus');
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '⚡ Tindak Semua (Mitigate All)';
      }
    }
  }

  renderThreats() {
    const container = document.getElementById('security-threats-container');
    const badge = document.getElementById('security-threat-badge');
    const mitigateAllBtn = document.getElementById('security-mitigate-all-btn');
    if (mitigateAllBtn) {
      mitigateAllBtn.style.display = this.threats.length > 0 ? 'inline-flex' : 'none';
    }
    if (badge) {
      badge.textContent = `${this.threats.length} Active`;
      badge.className = this.threats.length > 0 ? 'badge badge-critical font-mono' : 'badge badge-healthy font-mono';
    }

    if (!container) return;

    if (this.threats.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 2.5rem 1rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛡️</div>
          <h3 style="font-family: var(--font-display); margin-bottom: 0.25rem;">Threat Center Clean</h3>
          <p class="text-secondary" style="font-size: 0.85rem;">No suspicious anomalies or security deviations currently detected across system telemetry.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.threats.map(t => {
      const badgeClass = t.severity === 'CRITICAL' ? 'badge-critical' : t.severity === 'HIGH' ? 'badge-critical' : t.severity === 'WARNING' ? 'badge-warning' : 'badge-info';
      return `
        <div class="card" style="border-left: 4px solid var(--accent-rose); margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span class="badge ${badgeClass} font-mono">${t.severity}</span>
                <strong style="font-size: 1rem;">${escapeHtml(t.category)}</strong>
              </div>
              <div class="text-muted font-mono" style="font-size: 0.75rem;">Target: <span class="text-primary">${escapeHtml(t.target)}</span> | Source: ${escapeHtml(t.source)}</div>
            </div>
            <span class="badge badge-info font-mono">${t.status}</span>
          </div>

          <p style="font-size: 0.85rem; margin-bottom: 0.6rem;">${escapeHtml(t.reason)}</p>

          <div class="card" style="background: var(--bg-body); padding: 0.6rem; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
            <strong>Evidence:</strong> ${escapeHtml(t.evidence)}
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.78rem; color: var(--color-primary);">
              💡 <strong>Recommendation:</strong> ${escapeHtml(t.recommended_action)}
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              ${t.pid ? `
                <button class="btn btn-primary btn-sm" onclick="app.mitigateThreat('${t.id}', 'COOLDOWN_PROCESS')" title="Tangguhkan proses 3.5s untuk mendinginkan CPU lalu lanjutkan normal">
                  ⏱️ Resolve & Cooldown (3.5s)
                </button>
                <button class="btn btn-danger btn-sm" onclick="app.mitigateThreat('${t.id}', 'TERMINATE_PROCESS')">
                  Terminate Process
                </button>
              ` : `
                <button class="btn btn-primary btn-sm" onclick="app.mitigateThreat('${t.id}', 'RESOLVE')">
                  🛠️ Resolve & Mitigate
                </button>
              `}
              <button class="btn btn-secondary btn-sm" onclick="app.mitigateThreat('${t.id}', 'FALSE_POSITIVE')">
                False Positive
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  async fetchEventHistory() {
    try {
      const res = await fetch('/api/security/events');
      if (res.ok) {
        const events = await res.json();
        const tbody = document.getElementById('security-history-tbody');
        if (tbody) {
          tbody.innerHTML = events.map(e => `
            <tr>
              <td class="font-mono text-muted">${new Date(e.timestamp * 1000).toLocaleTimeString()}</td>
              <td><strong>${escapeHtml(e.category)}</strong></td>
              <td><span class="badge ${e.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning'} font-mono">${e.severity}</span></td>
              <td>${escapeHtml(e.target || '—')}</td>
              <td><span class="badge badge-healthy font-mono">${e.status}</span></td>
              <td class="text-secondary" style="font-size: 0.75rem;">${escapeHtml(e.action_taken || 'Status acknowledged by administrator')}</td>
            </tr>
          `).join('') || '<tr><td colspan="6" class="text-muted text-center">No historical threat events recorded in database yet.</td></tr>';
        }
      }
    } catch (err) {}
  }
  showFallbackOptions(threatId, failureData) {
    const existing = document.getElementById('wismon-fallback-modal');
    if (existing) existing.remove();

    const backdrop = document.createElement('div');
    backdrop.id = 'wismon-fallback-modal';
    backdrop.className = 'wismon-confirm-backdrop';

    const actions = failureData.suggested_actions || [
      { label: 'Paksa Hentikan (Kill)', action: 'TERMINATE_PROCESS' },
      { label: 'Tandai False Positive (Aman)', action: 'FALSE_POSITIVE' }
    ];

    const actionButtons = actions.map(a => `
      <button class="btn btn-primary btn-sm" onclick="app.mitigateThreat('${threatId}', '${a.action}'); document.getElementById('wismon-fallback-modal')?.remove();">
        ${escapeHtml(a.label)}
      </button>
    `).join('');

    backdrop.innerHTML = `
      <div class="wismon-confirm-modal">
        <div class="wismon-confirm-header">
          <div class="wismon-confirm-icon icon-warning">⚠️</div>
          <div class="wismon-confirm-title">Opsi Alternatif Mitigasi</div>
        </div>
        <div class="wismon-confirm-desc">
          <strong>Penyebab Kendala:</strong>
          <p style="margin-top: 0.35rem; color: var(--status-critical); font-size: 0.8rem;">
            ${escapeHtml(failureData.message || 'Tindakan awal tidak dapat dieksekusi.')}
          </p>
          <p style="margin-top: 0.5rem; font-size: 0.775rem; color: var(--text-secondary);">
            Silakan pilih opsi penanganan alternatif di bawah ini atau jalankan WISMON dengan hak Administrator:
          </p>
        </div>
        <div class="wismon-confirm-actions" style="margin-top: 0.75rem;">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('wismon-fallback-modal')?.remove();">Tutup</button>
          ${actionButtons}
        </div>
      </div>
    `;

    document.body.appendChild(backdrop);
  }
}

window.securityPage = new SecurityPage();
