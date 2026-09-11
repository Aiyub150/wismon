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
    setInterval(() => this.fetchProcesses(), 3000);
  }

  async fetchProcesses() {
    try {
      const res = await fetch('/api/activity/processes');
      if (res.ok) {
        const data = await res.json();
        this.processes = data.processes || [];
        document.getElementById('proc-total-count').textContent = `${this.processes.length} Processes`;
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
        (p.path && p.path.toLowerCase().includes(this.searchTerm))
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

    tbody.innerHTML = this.filteredProcesses.slice(0, 50).map(p => `
      <tr>
        <td class="font-mono text-secondary">${p.pid}</td>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td class="font-mono text-cyan">${p.cpu_percent}%</td>
        <td class="font-mono">${(p.memory_bytes / (1024 * 1024)).toFixed(1)} MB</td>
        <td class="font-mono">${p.threads}</td>
        <td class="font-mono text-muted">${p.handles}</td>
        <td class="font-mono text-muted">${p.username}</td>
        <td>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.72rem;" onclick="app.inspectProcess(${p.pid})">Inspect</button>
          <button class="btn btn-danger" style="padding: 2px 8px; font-size: 0.72rem; margin-left: 4px;" onclick="app.confirmKillProcess(${p.pid}, '${escapeHtml(p.name)}')">End</button>
        </td>
      </tr>
    `).join('');
  }
}

window.processesPage = new ProcessesPage();
