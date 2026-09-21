/**
 * Network Page Controller.
 * Features live throughput charts, network interface telemetry,
 * and Socket Explorer with external connection priority and domain filtering.
 */

class NetworkPage {
  constructor() {
    this.tputChart = null;
    this.allSockets = [];
    this.socketStats = { total: 0, established: 0 };
  }

  init() {
    this.tputChart = new MiniChart('network-tput-canvas', {
      color: '#3C50E0',
      unit: ' KB/s',
      label: 'Bandwidth',
      autoScaleY: true,
      maxPoints: 60
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));

    // Socket search and filter event listeners
    const searchInput = document.getElementById('socket-search-input');
    const filterSelect = document.getElementById('socket-filter-select');

    if (searchInput) {
      searchInput.addEventListener('input', () => this.renderSockets());
    }
    if (filterSelect) {
      filterSelect.addEventListener('change', () => this.renderSockets());
    }

    this.fetchSockets();
    setInterval(() => {
      if (window.app && window.app.currentPage === 'network') {
        this.fetchSockets();
      }
    }, 3000);
  }

  update(snap) {
    if (!snap || !snap.network) return;
    const net = snap.network;
    const ifaces = net.interfaces || [];
    const tput = net.throughput || {};

    // 1. Throughput speeds
    const dlKbs = (tput.bytes_recv_sec / 1024).toFixed(1);
    const ulKbs = (tput.bytes_sent_sec / 1024).toFixed(1);
    const totalKbs = (parseFloat(dlKbs) + parseFloat(ulKbs)).toFixed(1);

    const dlElem = document.getElementById('net-dl-speed');
    const ulElem = document.getElementById('net-ul-speed');
    const totalElem = document.getElementById('net-total-speed');

    if (dlElem) dlElem.textContent = `${dlKbs} KB/s`;
    if (ulElem) ulElem.textContent = `${ulKbs} KB/s`;
    if (totalElem) totalElem.textContent = `${totalKbs} KB/s`;

    if (this.tputChart) {
      const timeStr = snap.timestamp ? new Date(snap.timestamp * 1000).toLocaleTimeString('en-GB') : null;
      this.tputChart.push(parseFloat(totalKbs), timeStr);
    }

    // 2. Interfaces Grid
    const ifacesContainer = document.getElementById('network-interfaces-list');
    if (ifacesContainer) {
      ifacesContainer.innerHTML = ifaces.filter(i => i.is_up).map(i => `
        <div class="card" style="padding: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                ${i.type === 'Wi-Fi' 
                  ? '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'
                  : '<rect width="16" height="12" x="2" y="6" rx="2"/><path d="M12 18v4M8 22h8"/>'}
              </svg>
              <strong>${escapeHtml(i.name)}</strong>
            </div>
            <span class="badge ${i.is_up ? 'badge-healthy' : 'badge-warning'}">${i.status}</span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.4rem; font-size: 0.75rem;" class="text-secondary font-mono">
            <div><span class="text-muted">IPv4:</span> ${i.ipv4}</div>
            <div><span class="text-muted">Gateway:</span> ${i.gateway}</div>
            <div><span class="text-muted">MAC:</span> ${i.mac}</div>
            <div><span class="text-muted">Speed:</span> ${i.speed_mbps !== 'Unavailable' ? i.speed_mbps + ' Mbps' : 'Unavailable'}</div>
          </div>
        </div>
      `).join('') || '<div class="text-muted">No active network adapters found.</div>';
    }
  }

  async fetchSockets() {
    try {
      const res = await fetch('/api/activity/sockets');
      if (res.ok) {
        const data = await res.json();
        this.allSockets = data.connections || [];
        this.socketStats = {
          total: this.allSockets.length,
          established: data.established_count || 0
        };
        this.renderSockets();
      }
    } catch (e) {
      console.warn('Failed to fetch sockets:', e);
    }
  }

  renderSockets() {
    const filterSelect = document.getElementById('socket-filter-select');
    const searchInput = document.getElementById('socket-search-input');
    const filterMode = filterSelect ? filterSelect.value : 'external';
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    let filtered = this.allSockets;

    // Filter by mode
    if (filterMode === 'external') {
      filtered = filtered.filter(c => c.is_external === true);
    } else if (filterMode === 'established') {
      filtered = filtered.filter(c => c.state === 'ESTABLISHED');
    } else if (filterMode === 'listening') {
      filtered = filtered.filter(c => c.state === 'LISTEN' || c.state === 'LISTENING');
    }

    // Filter by search query
    if (query) {
      filtered = filtered.filter(c => {
        const host = (c.remote_host || '').toLowerCase();
        const rAddr = (c.remote_address || '').toLowerCase();
        const lAddr = (c.local_address || '').toLowerCase();
        const proc = (c.process_name || '').toLowerCase();
        const pid = String(c.pid || '');
        return host.includes(query) || rAddr.includes(query) || lAddr.includes(query) || proc.includes(query) || pid.includes(query);
      });
    }

    const countBadge = document.getElementById('sockets-count-badge');
    if (countBadge) {
      countBadge.textContent = `${filtered.length} of ${this.socketStats.total} Sockets (${this.socketStats.established} Established)`;
    }

    const tbody = document.getElementById('network-sockets-tbody');
    if (!tbody) return;

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-muted" style="padding: 2rem;">
            ${query 
              ? `Tidak ditemukan koneksi yang cocok dengan "${escapeHtml(query)}"` 
              : (filterMode === 'external' 
                  ? 'Tidak ada koneksi internet eksternal aktif saat ini. Coba pilih "Semua Koneksi".' 
                  : 'Tidak ada data soket.')}
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = filtered.slice(0, 60).map(c => {
      const isExt = c.is_external;
      const isEst = c.state === 'ESTABLISHED';
      const rowStyle = isExt ? 'background: rgba(60, 80, 224, 0.04);' : '';
      const domainLabel = c.domain_label && c.domain_label !== '—' ? c.domain_label : '';
      const resolvedDomain = c.resolved_domain && c.resolved_domain !== '—' ? c.resolved_domain : '';
      const procSafe = escapeHtml(c.process_name || 'Process');
      const remoteSafe = escapeHtml(c.remote_address || '-');
      const hostSafe = escapeHtml(c.remote_host || '-');

      return `
        <tr style="${rowStyle}">
          <td>
            <div style="display: flex; align-items: center; gap: 0.35rem;">
              <span class="badge ${c.protocol === 'TCP' ? 'badge-neutral' : 'badge-warning'} font-mono" style="font-size: 0.7rem;">${c.protocol}</span>
              ${isExt ? '<span title="External Internet Connection" style="font-size: 0.8rem;">🌐</span>' : ''}
            </div>
          </td>
          <td class="font-mono text-secondary" style="font-size: 0.75rem;">${escapeHtml(c.local_address)}</td>
          <td class="font-mono text-cyan" style="font-size: 0.75rem; font-weight: ${isExt ? '600' : 'normal'};">
            ${remoteSafe}
          </td>
          <td>
            <div style="display: flex; flex-direction: column; gap: 2px;">
              <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                ${domainLabel ? `<span class="badge badge-primary font-mono" style="font-size: 0.68rem; padding: 1px 6px;">${escapeHtml(domainLabel)}</span>` : ''}
                ${resolvedDomain && resolvedDomain !== domainLabel ? `<span class="text-xs font-mono font-semibold text-primary">${escapeHtml(resolvedDomain)}</span>` : ''}
              </div>
              <span class="font-mono ${isExt ? 'text-secondary font-semibold' : 'text-muted'}" style="font-size: 0.74rem;">
                ${hostSafe}
              </span>
            </div>
          </td>
          <td>
            <span class="badge ${isEst ? 'badge-healthy' : 'badge-neutral'} font-mono" style="font-size: 0.7rem;">
              ${c.state}
            </span>
          </td>
          <td class="font-mono" style="font-size: 0.75rem;">${c.pid}</td>
          <td>
            <strong style="font-size: 0.82rem;">${procSafe}</strong>
          </td>
          <td style="text-align: right;">
            <button class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 4px;" onclick="window.networkPage.askDahooAboutSocket('${encodeURIComponent(JSON.stringify({ proc: c.process_name, pid: c.pid, remote: c.remote_address, host: c.remote_host, domain: domainLabel, resolved: resolvedDomain }))}')" title="Tanyakan keamanan & fungsi koneksi ini ke Dahoo AI">
              <span>💬</span> <span>Tanya</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  askDahooAboutSocket(encodedData) {
    try {
      const data = JSON.parse(decodeURIComponent(encodedData));
      const targetName = data.resolved || data.domain || data.host || data.remote;
      const prompt = `Tolong analisis koneksi internet ini: Proses "${data.proc}" (PID: ${data.pid}) sedang tersambung ke ${data.remote} (${targetName}). Apakah koneksi ini aman, wajar, dan apa fungsinya?`;
      if (window.dahoo) {
        window.dahoo.askContextual(prompt);
      }
    } catch (e) {
      console.error('Failed to ask Dahoo about socket:', e);
    }
  }
}

window.networkPage = new NetworkPage();

