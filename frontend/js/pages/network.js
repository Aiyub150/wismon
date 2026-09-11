/**
 * Network Page Controller.
 */

class NetworkPage {
  constructor() {
    this.tputChart = null;
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
    this.fetchSockets();
    setInterval(() => {
      if (window.app && window.app.currentPage === 'network') {
        this.fetchSockets();
      }
    }, 4000);
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
        const conns = data.connections || [];
        const countBadge = document.getElementById('sockets-count-badge');
        if (countBadge) {
          countBadge.textContent = `${conns.length} Sockets (${data.established_count || 0} Established)`;
        }

        const tbody = document.getElementById('network-sockets-tbody');
        if (tbody) {
          tbody.innerHTML = conns.slice(0, 35).map(c => `
            <tr>
              <td><span class="badge ${c.protocol === 'TCP' ? 'badge-neutral' : 'badge-warning'} font-mono">${c.protocol}</span></td>
              <td class="font-mono text-secondary">${escapeHtml(c.local_address)}</td>
              <td class="font-mono text-cyan">${escapeHtml(c.remote_address)}</td>
              <td><span class="font-mono text-primary">${escapeHtml(c.remote_host)}</span></td>
              <td><span class="badge ${c.state === 'ESTABLISHED' ? 'badge-healthy' : 'badge-neutral'} font-mono">${c.state}</span></td>
              <td class="font-mono">${c.pid}</td>
              <td><strong>${escapeHtml(c.process_name)}</strong></td>
            </tr>
          `).join('');
        }
      }
    } catch (e) {}
  }
}

window.networkPage = new NetworkPage();
