/**
 * Process Explorer Page Controller.
 */

class ProcessesPage {
  constructor() {
    this.processes = [];
    this.filteredProcesses = [];
    this.searchTerm = '';
    this.sortBy = 'cpu_percent';
    this.sortAsc = false;
  }

  init() {
    const searchInput = document.getElementById('proc-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.toLowerCase().trim();
        this.applyFilterAndRender();
      });
    }

    const sortSelect = document.getElementById('proc-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.sortBy = e.target.value;
        this.applyFilterAndRender();
      });
    }

    this.fetchProcesses();
    setInterval(() => {
      if (window.app && window.app.currentPage === 'processes') {
        this.fetchProcesses();
      }
    }, 4000);
  }

  async fetchProcesses() {
    try {
      const res = await fetch('/api/activity/processes');
      if (res.ok) {
        const data = await res.json();
        this.processes = data.processes || [];
        const countEl = document.getElementById('proc-total-count');
        if (countEl) countEl.textContent = `${this.processes.length} Processes`;
        this.applyFilterAndRender();
      }
    } catch (e) {}
  }

  applyFilterAndRender() {
    let list = [...this.processes];

    if (this.searchTerm) {
      list = list.filter(p => 
        p.name.toLowerCase().includes(this.searchTerm) || 
        String(p.pid).includes(this.searchTerm) ||
        (p.path && p.path.toLowerCase().includes(this.searchTerm)) ||
        (p.description && p.description.toLowerCase().includes(this.searchTerm))
      );
    }

    list.sort((a, b) => {
      const valA = a[this.sortBy] || 0;
      const valB = b[this.sortBy] || 0;
      return this.sortAsc ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
    });

    this.filteredProcesses = list;
    this.renderTable();
  }

  renderTable() {
    const tbody = document.getElementById('processes-tbody');
    if (!tbody) return;

    tbody.innerHTML = this.filteredProcesses.slice(0, 60).map(p => {
      const isIdle = p.is_idle || p.pid === 0 || p.name.toLowerCase().includes('idle');
      const isProtected = p.pid === 0 || p.pid === 4 || ['smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe'].includes(p.name.toLowerCase());
      
      const cpuDisplay = isIdle 
        ? `${p.cpu_percent_normalized || (p.cpu_percent / 8).toFixed(1)}% <span class="text-muted" style="font-size: 0.65rem;">(Idle)</span>`
        : `${p.cpu_percent}%`;

      return `
        <tr>
          <td class="font-mono text-secondary">${p.pid}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 4px;">
              <strong>${escapeHtml(p.name)}</strong>
              ${isIdle ? '<span class="badge badge-neutral font-mono" style="font-size: 0.65rem;" title="Represents unallocated CPU capacity across all logical cores">Idle Thread</span>' : ''}
            </div>
            <div class="text-muted" style="font-size: 0.7rem; margin-top: 1px;">${escapeHtml(p.description || '')}</div>
          </td>
          <td class="font-mono ${isIdle ? 'text-secondary' : 'text-cyan'}">${cpuDisplay}</td>
          <td class="font-mono">${(p.memory_bytes / (1024 * 1024)).toFixed(1)} MB</td>
          <td class="font-mono">${p.threads}</td>
          <td class="font-mono text-muted">${p.handles}</td>
          <td class="font-mono text-muted">${p.username}</td>
          <td>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.72rem;" onclick="app.inspectProcess(${p.pid})">Inspect</button>
            ${isProtected 
              ? `<button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.72rem; margin-left: 4px; opacity: 0.5;" disabled title="Core system process is protected">Protected</button>`
              : `<button class="btn btn-danger" style="padding: 2px 8px; font-size: 0.72rem; margin-left: 4px;" onclick="app.confirmKillProcess(${p.pid}, '${escapeHtml(p.name)}')">End</button>`
            }
          </td>
        </tr>
      `;
    }).join('');
  }
}

window.processesPage = new ProcessesPage();
