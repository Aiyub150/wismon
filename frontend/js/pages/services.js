/**
 * Windows Services Page Controller.
 */

class ServicesPage {
  constructor() {
    this.services = [];
    this.svchostGroups = [];
    this.filterStatus = 'all';
    this.searchTerm = '';
  }

  init() {
    const searchInput = document.getElementById('services-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.toLowerCase().trim();
        this.renderServices();
      });
    }

    const filterBtns = document.querySelectorAll('.service-filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.filterStatus = btn.dataset.filter;
        this.renderServices();
      });
    });

    this.fetchServices();
  }

  async fetchServices() {
    try {
      const res = await fetch('/api/activity/services');
      if (res.ok) {
        const data = await res.json();
        this.services = data.services || [];
        this.svchostGroups = data.svchost_groups || [];

        document.getElementById('services-total-count').textContent = `${this.services.length} Total`;
        document.getElementById('services-running-count').textContent = `${data.running_count || 0} Running`;
        document.getElementById('services-stopped-count').textContent = `${data.stopped_count || 0} Stopped`;

        this.renderServices();
        this.renderSvchostTree();
      }
    } catch (e) {}
  }

  renderServices() {
    const tbody = document.getElementById('services-tbody');
    if (!tbody) return;

    let list = this.services;
    if (this.filterStatus !== 'all') {
      list = list.filter(s => s.status.toLowerCase() === this.filterStatus);
    }
    if (this.searchTerm) {
      list = list.filter(s =>
        s.name.toLowerCase().includes(this.searchTerm) ||
        (s.display_name && s.display_name.toLowerCase().includes(this.searchTerm))
      );
    }

    tbody.innerHTML = list.slice(0, 60).map(s => `
      <tr>
        <td><strong>${escapeHtml(s.name)}</strong></td>
        <td>${escapeHtml(s.display_name || s.name)}</td>
        <td class="font-mono text-muted">${s.pid || '—'}</td>
        <td><span class="badge ${s.status === 'running' ? 'badge-healthy' : 'badge-warning'}">${s.status}</span></td>
        <td class="text-secondary font-mono">${s.start_type}</td>
        <td class="text-muted font-mono" style="font-size: 0.7rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(s.binpath)}</td>
      </tr>
    `).join('') || '<tr><td colspan="6" class="text-muted text-center">No services found matching filter.</td></tr>';
  }

  renderSvchostTree() {
    const container = document.getElementById('svchost-tree-container');
    if (!container) return;

    container.innerHTML = this.svchostGroups.map(group => `
      <div class="card" style="padding: 0.85rem; margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1rem;">⚙️</span>
            <strong>svchost.exe</strong>
            <span class="font-mono text-secondary" style="font-size: 0.75rem;">PID: ${group.pid}</span>
          </div>
          <span class="badge badge-info">${group.service_count} Services Hosted</span>
        </div>
        <div style="padding-left: 1.5rem; display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem;">
          ${group.services.map(s => `
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <span class="text-muted">├──</span>
              <strong class="text-primary">${escapeHtml(s.name)}</strong>
              <span class="text-muted">(${escapeHtml(s.display_name)})</span>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('') || '<div class="text-muted">No shared svchost groups identified.</div>';
  }
}

window.servicesPage = new ServicesPage();
