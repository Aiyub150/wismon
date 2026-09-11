/**
 * Main Application Orchestrator for Windows System Monitoring.
 * Handles client-side navigation, global modals, search palette, and notifications.
 */

class App {
  constructor() {
    this.currentPage = 'dashboard';
    this.inspectModal = document.getElementById('process-inspect-modal');
    this.killModal = document.getElementById('process-kill-modal');
    this.searchModal = document.getElementById('search-palette-modal');
    this.pendingKillPid = null;
    this.pendingThreatMitigation = null;
  }

  init() {
    // 1. Navigation setup
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        if (page) this.navigate(page);
      });
    });

    // 2. Global search shortcut (Ctrl+K)
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        this.toggleSearchModal(true);
      }
      if (e.key === 'Escape') {
        this.closeAllModals();
      }
    });

    const searchBox = document.getElementById('topbar-search-box');
    if (searchBox) {
      searchBox.addEventListener('click', () => this.toggleSearchModal(true));
    }

    const searchInput = document.getElementById('palette-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.handlePaletteSearch(e.target.value));
    }

    // Modal close buttons
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
      btn.addEventListener('click', () => this.closeAllModals());
    });

    // Confirm kill button
    const confirmKillBtn = document.getElementById('confirm-kill-btn');
    if (confirmKillBtn) {
      confirmKillBtn.addEventListener('click', () => this.executeKillProcess());
    }

    // Initialize subpages
    if (window.dashboardPage) window.dashboardPage.init();
    if (window.cpuPage) window.cpuPage.init();
    if (window.memoryPage) window.memoryPage.init();
    if (window.storagePage) window.storagePage.init();
    if (window.networkPage) window.networkPage.init();
    if (window.processesPage) window.processesPage.init();
    if (window.servicesPage) window.servicesPage.init();
    if (window.securityPage) window.securityPage.init();
    if (window.hardwarePage) window.hardwarePage.init();
    if (window.analysisPage) window.analysisPage.init();

    // Start SSE stream
    if (window.telemetryStream) window.telemetryStream.connect();

    // Listen for threats to show notification toasts
    window.addEventListener('telemetry-update', (e) => {
      const snap = e.detail;
      const threats = snap.threats || [];
      const badge = document.getElementById('nav-threat-count-badge');
      if (badge) {
        if (threats.length > 0) {
          badge.textContent = threats.length;
          badge.style.display = 'inline-block';
        } else {
          badge.style.display = 'none';
        }
      }
    });

    console.log("Windows System Monitoring UI initialized.");
  }

  navigate(pageId) {
    this.currentPage = pageId;

    // Update active nav-item
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.page === pageId);
    });

    // Update active view
    document.querySelectorAll('.page-view').forEach(el => {
      el.classList.toggle('active', el.id === `page-${pageId}`);
    });

    // Update breadcrumb/title
    const titleEl = document.getElementById('topbar-page-title');
    if (titleEl) {
      const pageNames = {
        'dashboard': 'System Overview',
        'cpu': 'CPU Monitoring',
        'memory': 'Memory Architecture',
        'storage': 'Storage & I/O Analytics',
        'network': 'Network & Sockets',
        'processes': 'Process Explorer',
        'services': 'Windows Services',
        'security': 'Security & Threat Center',
        'hardware': 'Hardware & Sensors',
        'analysis': 'Telemetry Analysis'
      };
      titleEl.textContent = pageNames[pageId] || pageId.toUpperCase();
    }

    // Scroll viewport to top
    const viewport = document.getElementById('content-viewport');
    if (viewport) viewport.scrollTop = 0;
  }

  // --- Modal Operations ---

  closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    this.pendingKillPid = null;
  }

  async inspectProcess(pid) {
    try {
      const res = await fetch(`/api/activity/process/${pid}`);
      if (res.ok) {
        const p = await res.json();
        document.getElementById('inspect-proc-name').textContent = p.name;
        document.getElementById('inspect-proc-pid').textContent = p.pid;
        document.getElementById('inspect-proc-path').textContent = p.path;
        document.getElementById('inspect-proc-user').textContent = p.username;
        document.getElementById('inspect-proc-cpu').textContent = `${p.cpu_percent}%`;
        document.getElementById('inspect-proc-mem').textContent = `${(p.memory_bytes / (1024**2)).toFixed(1)} MB`;
        document.getElementById('inspect-proc-threads').textContent = p.threads;
        document.getElementById('inspect-proc-handles').textContent = p.handles;
        document.getElementById('inspect-proc-io').textContent = `R: ${(p.io_read_bytes/(1024**2)).toFixed(1)} MB | W: ${(p.io_write_bytes/(1024**2)).toFixed(1)} MB`;
        document.getElementById('inspect-proc-time').textContent = new Date(p.created_at * 1000).toLocaleString();

        const killBtn = document.getElementById('inspect-kill-btn');
        if (killBtn) {
          killBtn.onclick = () => {
            this.closeAllModals();
            this.confirmKillProcess(p.pid, p.name);
          };
        }

        if (this.inspectModal) this.inspectModal.classList.add('active');
      }
    } catch (e) {
      alert('Error fetching process details: ' + e.message);
    }
  }

  confirmKillProcess(pid, name) {
    this.pendingKillPid = pid;
    document.getElementById('kill-proc-name').textContent = name;
    document.getElementById('kill-proc-pid').textContent = pid;
    if (this.killModal) this.killModal.classList.add('active');
  }

  async executeKillProcess() {
    if (!this.pendingKillPid) return;
    try {
      const res = await fetch('/api/activity/process/terminate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pid: this.pendingKillPid, confirm: true })
      });
      const data = await res.json();
      if (res.ok) {
        this.showToast('success', data.message || 'Process terminated.');
        this.closeAllModals();
        if (window.processesPage) window.processesPage.fetchProcesses();
      } else {
        this.showToast('danger', data.detail || 'Termination failed.');
      }
    } catch (e) {
      this.showToast('danger', 'Communication error: ' + e.message);
    }
  }

  async mitigateThreat(threatId, action) {
    if (!confirm(`Are you sure you want to perform action '${action}' on this threat event?`)) {
      return;
    }
    try {
      const res = await fetch('/api/security/mitigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threat_id: threatId, action: action, confirm: true })
      });
      const data = await res.json();
      if (res.ok) {
        this.showToast('success', data.message);
        if (window.securityPage) window.securityPage.fetchEventHistory();
      } else {
        this.showToast('danger', data.detail || 'Mitigation failed.');
      }
    } catch (e) {
      this.showToast('danger', 'Error: ' + e.message);
    }
  }

  toggleSearchModal(open) {
    if (!this.searchModal) return;
    if (open) {
      this.searchModal.classList.add('active');
      const input = document.getElementById('palette-input');
      if (input) {
        input.value = '';
        input.focus();
        this.handlePaletteSearch('');
      }
    } else {
      this.searchModal.classList.remove('active');
    }
  }

  handlePaletteSearch(query) {
    const q = query.toLowerCase().trim();
    const resultsContainer = document.getElementById('palette-results');
    if (!resultsContainer) return;

    const pages = [
      { name: 'Dashboard Overview', page: 'dashboard', icon: '📊' },
      { name: 'CPU Monitoring', page: 'cpu', icon: '⚡' },
      { name: 'Memory & Pools', page: 'memory', icon: '🧠' },
      { name: 'Storage & I/O Analytics', page: 'storage', icon: '💾' },
      { name: 'Network & Sockets', page: 'network', icon: '🌐' },
      { name: 'Process Explorer', page: 'processes', icon: '⚙️' },
      { name: 'Windows Services', page: 'services', icon: '🔧' },
      { name: 'Threat Center', page: 'security', icon: '🛡️' },
      { name: 'Hardware & GPU', page: 'hardware', icon: '🖥️' },
      { name: 'Telemetry Analysis & History', page: 'analysis', icon: '📈' },
    ];

    const matchedPages = pages.filter(p => p.name.toLowerCase().includes(q));

    resultsContainer.innerHTML = matchedPages.map(p => `
      <div class="palette-item" onclick="app.navigate('${p.page}'); app.toggleSearchModal(false);" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.85rem; border-radius: 8px; cursor: pointer; transition: background 0.15s;">
        <span style="font-size: 1.1rem;">${p.icon}</span>
        <strong>${p.name}</strong>
        <span class="text-muted" style="margin-left: auto; font-size: 0.7rem; font-family: monospace;">Page</span>
      </div>
    `).join('') || '<div class="text-muted text-center" style="padding: 1rem;">No matching pages or items.</div>';
  }

  showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `badge badge-${type === 'success' ? 'healthy' : 'critical'}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '90px';
    toast.style.right = '24px';
    toast.style.zIndex = '999';
    toast.style.padding = '0.75rem 1.25rem';
    toast.style.fontSize = '0.85rem';
    toast.style.boxShadow = 'var(--shadow-lg)';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
  window.app.init();
});
