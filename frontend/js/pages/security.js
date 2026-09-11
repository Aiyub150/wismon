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
    this.fetchEventHistory();
  }

  renderThreats() {
    const container = document.getElementById('security-threats-container');
    const badge = document.getElementById('security-threat-badge');
    if (badge) badge.textContent = `${this.threats.length} Active`;

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
                <span class="badge ${badgeClass}">${t.severity}</span>
                <strong style="font-size: 1rem;">${escapeHtml(t.category)}</strong>
              </div>
              <div class="text-muted font-mono" style="font-size: 0.75rem;">Target: <span class="text-primary">${escapeHtml(t.target)}</span> | Source: ${escapeHtml(t.source)}</div>
            </div>
            <span class="badge badge-info font-mono">${t.status}</span>
          </div>

          <p style="font-size: 0.85rem; margin-bottom: 0.6rem;">${escapeHtml(t.reason)}</p>

          <div class="card" style="background: rgba(0,0,0,0.3); padding: 0.6rem; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
            <strong>Evidence:</strong> ${escapeHtml(t.evidence)}
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
            <div style="font-size: 0.78rem; color: var(--accent-cyan);">
              💡 <strong>Recommendation:</strong> ${escapeHtml(t.recommended_action)}
            </div>
            <div style="display: flex; gap: 0.5rem;">
              ${t.pid ? `
                <button class="btn btn-danger" style="font-size: 0.75rem;" onclick="app.mitigateThreat('${t.id}', 'TERMINATE_PROCESS')">
                  Terminate Process
                </button>
              ` : ''}
              <button class="btn btn-secondary" style="font-size: 0.75rem;" onclick="app.mitigateThreat('${t.id}', 'RESOLVE')">
                Resolve
              </button>
              <button class="btn btn-secondary" style="font-size: 0.75rem;" onclick="app.mitigateThreat('${t.id}', 'FALSE_POSITIVE')">
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
              <td><span class="badge ${e.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning'}">${e.severity}</span></td>
              <td>${escapeHtml(e.target || '—')}</td>
              <td><span class="badge badge-healthy">${e.status}</span></td>
              <td class="text-secondary" style="font-size: 0.75rem;">${escapeHtml(e.action_taken || 'No action recorded')}</td>
            </tr>
          `).join('') || '<tr><td colspan="6" class="text-muted text-center">No historical threat events recorded in database yet.</td></tr>';
        }
      }
    } catch (err) {}
  }
}

window.securityPage = new SecurityPage();
