/**
 * Network Page Controller.
 */

class NetworkPage {
  constructor() {
    this.tputChart = null;
  }

  init() {
    this.tputChart = new MiniChart('network-tput-canvas', {
      color: '#06b6d4',
      unit: 'KB/s',
      autoScaleY: true,
      maxPoints: 60
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));
    this.fetchSockets();
    setInterval(() => {
      if (window.app && window.app.currentPage === 'network') {
        this.fetchSockets();
      }
    }, 5000);
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

    document.getElementById('net-dl-speed').textContent = `${dlKbs} KB/s`;
    document.getElementById('net-ul-speed').textContent = `${ulKbs} KB/s`;
    document.getElementById('net-total-speed').textContent = `${totalKbs} KB/s`;

    if (this.tputChart) this.tputChart.push(parseFloat(totalKbs));

    // 2. Interfaces Grid
    const ifacesContainer = document.getElementById('network-interfaces-list');
    if (ifacesContainer) {
      ifacesContainer.innerHTML = ifaces.filter(i => i.is_up).map(i => `
        <div class="card" style="padding: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 1.1rem;">${i.type === 'Wi-Fi' ? '📶' : '🌐'}</span>
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
        document.getElementById('sockets-count-badge').textContent = `${conns.length} Sockets (${data.established_count || 0} Established)`;

        const tbody = document.getElementById('network-sockets-tbody');
        if (tbody) {
          // Show top 30 active connections
          tbody.innerHTML = conns.slice(0, 30).map(c => `
            <tr>
              <td><span class="badge ${c.protocol === 'TCP' ? 'badge-info' : 'badge-warning'}">${c.protocol}</span></td>
              <td class="font-mono text-secondary">${escapeHtml(c.local_address)}</td>
              <td class="font-mono text-cyan">${escapeHtml(c.remote_address)}</td>
              <td><span class="font-mono text-primary">${escapeHtml(c.remote_host)}</span></td>
              <td><span class="badge ${c.state === 'ESTABLISHED' ? 'badge-healthy' : 'badge-info'}">${c.state}</span></td>
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
