/**
 * Real-Time SSE (Server-Sent Events) Client with auto-reconnection.
 */

class TelemetryStream {
  constructor(endpoint = '/api/stream/realtime') {
    this.endpoint = endpoint;
    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.listeners = [];
  }

  connect() {
    this.updateStatus('connecting', 'Connecting...');
    try {
      this.eventSource = new EventSource(this.endpoint);

      this.eventSource.onopen = () => {
        this.reconnectAttempts = 0;
        this.updateStatus('online', 'Online (SSE)');
      };

      this.eventSource.onmessage = (event) => {
        try {
          const snapshot = JSON.parse(event.data);
          // Dispatch custom event
          window.dispatchEvent(new CustomEvent('telemetry-update', { detail: snapshot }));
          this.listeners.forEach(cb => cb(snapshot));
        } catch (err) {
          console.error('Error parsing SSE snapshot:', err);
        }
      };

      this.eventSource.onerror = () => {
        this.updateStatus('offline', 'Reconnecting...');
        this.eventSource.close();
        const timeout = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000);
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), timeout);
      };
    } catch (e) {
      this.updateStatus('offline', 'Error');
    }
  }

  subscribe(callback) {
    this.listeners.push(callback);
  }

  updateStatus(state, label) {
    const pill = document.getElementById('topbar-status-pill');
    const text = document.getElementById('topbar-status-text');
    if (!pill || !text) return;

    pill.className = `status-pill ${state}`;
    text.textContent = label;
  }
}

window.telemetryStream = new TelemetryStream();
