/**
 * Main Application Orchestrator for WISMON (Windows System Monitoring).
 * Handles client-side navigation, theme switching, global modals, and search palette.
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
    // 1. Theme setup (TailAdmin Dark/Light mode)
    this.initTheme();

    // 2. Navigation setup
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        const target = item.dataset.target;
        if (page) {
          this.navigate(page, target);
        }
      });
    });

    // Nav Dahoo trigger
    const navDahoo = document.getElementById('nav-dahoo-btn');
    if (navDahoo) {
      navDahoo.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.dahooAssistant) window.dahooAssistant.toggleDrawer(true);
      });
    }

    // 3. Global search shortcut (Ctrl+K)
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

    // Listen for threats to show notification badge
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

    console.log("WISMON — Windows System Monitoring UI initialized.");
  }

  initTheme() {
    const savedTheme = localStorage.getItem('wismon-theme') || 'dark';
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('wismon-theme', isDark ? 'dark' : 'light');
      });
    }
  }

  navigate(pageId, targetSection = null) {
    this.currentPage = pageId;

    // Update active nav-item
    document.querySelectorAll('.nav-item').forEach(el => {
      const match = el.dataset.page === pageId;
      el.classList.toggle('active', match);
    });

    // Update active view
    document.querySelectorAll('.page-view').forEach(el => {
      el.classList.toggle('active', el.id === `page-${pageId}`);
    });

    // Update breadcrumb/title
    const titleEl = document.getElementById('topbar-page-title');
    if (titleEl) {
      const pageNames = {
        'dashboard': 'Dashboard Overview',
        'cpu': 'CPU Telemetry & Diagnostics',
        'memory': 'Physical RAM & Kernel Memory',
        'storage': 'Storage & Disk I/O Analytics',
        'network': 'Network & Sockets Explorer',
        'processes': 'Process Explorer',
        'services': 'Windows Services',
        'security': 'Security Events & Threat Intelligence',
        'hardware': 'GPU & Hardware Sensors',
        'analysis': 'Performance & Historical Analysis'
      };
      titleEl.textContent = pageNames[pageId] || pageId.toUpperCase();
    }

    // Trigger canvas resize so newly visible charts calculate actual container widths
    setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 40);

    // Scroll viewport or target section
    const viewport = document.getElementById('content-viewport');
    if (viewport) {
      if (targetSection) {
        setTimeout(() => {
          const targetEl = document.getElementById(`section-${targetSection}`);
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          } else {
            viewport.scrollTop = 0;
          }
        }, 60);
      } else {
        viewport.scrollTop = 0;
      }
    }
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
    const actionLabel = action === 'TERMINATE_PROCESS' 
      ? 'Hentikan (Kill) proses yang memicu ancaman ini' 
      : (action === 'COOLDOWN_PROCESS' || action === 'THROTTLE_PROCESS')
      ? 'Tangguhkan (pause) proses selama 3.5 detik untuk mendinginkan CPU lalu lanjutkan kembali secara normal'
      : action === 'FALSE_POSITIVE' 
      ? 'Tandai ancaman sebagai False Positive (Aman)' 
      : 'Selesaikan anomali ini dan terapkan tindakan mitigasi sistem';

    if (!confirm(`Konfirmasi Tindakan Keamanan:\n${actionLabel}?\n\nTindakan nyata akan dieksekusi dan dicatat dalam audit log.`)) {
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
        this.showToast('success', data.message || 'Tindakan keamanan berhasil dieksekusi.');
        if (window.securityPage) window.securityPage.fetchEventHistory();
      } else {
        this.showToast('danger', data.detail || 'Tindakan gagal dijalankan.');
      }
    } catch (e) {
      this.showToast('danger', 'Error komunikasi: ' + e.message);
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
      { name: 'Dashboard Overview', page: 'dashboard', category: 'Overview' },
      { name: 'CPU Telemetry & Cores', page: 'cpu', category: 'System' },
      { name: 'Physical RAM & Kernel Pools', page: 'memory', category: 'System' },
      { name: 'GPU & Graphics Hardware', page: 'hardware', category: 'System', target: 'gpu' },
      { name: 'Storage Drives & I/O', page: 'storage', category: 'System' },
      { name: 'Network Interfaces & Speed', page: 'network', category: 'System' },
      { name: 'Process Explorer', page: 'processes', category: 'Activity' },
      { name: 'Windows Services & svchost', page: 'services', category: 'Activity' },
      { name: 'Connections & Sockets Explorer', page: 'network', category: 'Activity', target: 'sockets' },
      { name: 'Threat Center', page: 'security', category: 'Security' },
      { name: 'Security Events Log', page: 'security', category: 'Security', target: 'events' },
      { name: 'Storage Analyzer', page: 'storage', category: 'Analysis', target: 'analyzer' },
      { name: 'Statistical Telemetry Analysis', page: 'analysis', category: 'Analysis' }
    ];

    const matched = pages.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));

    resultsContainer.innerHTML = matched.map(p => `
      <div class="palette-item" onclick="app.navigate('${p.page}', '${p.target || ''}'); app.toggleSearchModal(false);" style="display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 0.85rem; border-radius: var(--radius-md); cursor: pointer; border-bottom: 1px solid var(--border-subtle);">
        <strong style="color: var(--text-primary); font-size: 0.875rem;">${p.name}</strong>
        <span class="badge badge-neutral" style="font-size: 0.7rem;">${p.category}</span>
      </div>
    `).join('') || '<div class="text-muted text-center" style="padding: 1rem;">No matching pages or items.</div>';
  }

  showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `badge badge-${type === 'success' ? 'healthy' : 'critical'}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '85px';
    toast.style.right = '24px';
    toast.style.zIndex = '999';
    toast.style.padding = '0.65rem 1.1rem';
    toast.style.fontSize = '0.8125rem';
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
