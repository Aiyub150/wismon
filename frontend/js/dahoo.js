/**
 * Dahoo Assistant UI Controller.
 * Handles interactive mascot, emotions, proactive alerts, chat drawer, and AI cost tracking.
 */

class DahooController {
  constructor() {
    this.avatarBtn = document.getElementById('dahoo-avatar');
    this.speechBubble = document.getElementById('dahoo-speech-bubble');
    this.drawer = document.getElementById('dahoo-drawer');
    this.closeBtn = document.getElementById('close-dahoo-btn');
    this.chatBody = document.getElementById('dahoo-chat-body');
    this.chatInput = document.getElementById('dahoo-input');
    this.sendBtn = document.getElementById('dahoo-send-btn');
    this.cloudToggle = document.getElementById('dahoo-cloud-toggle');
    this.modelBadge = document.getElementById('dahoo-model-badge');
    this.costBadge = document.getElementById('dahoo-cost-badge');
    this.tokenBadge = document.getElementById('dahoo-tokens-badge');

    this.initEvents();
    this.updateState();
    setInterval(() => this.updateMetrics(), 10000);
  }

  initEvents() {
    if (this.avatarBtn) {
      this.avatarBtn.addEventListener('click', () => this.toggleDrawer());
    }
    if (this.speechBubble) {
      this.speechBubble.addEventListener('click', () => this.toggleDrawer());
    }
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.toggleDrawer(false));
    }
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.sendMessage());
    }
    if (this.chatInput) {
      this.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }

    // Topbar Assistant Button
    const topbarDahoo = document.getElementById('topbar-dahoo-btn');
    if (topbarDahoo) {
      topbarDahoo.addEventListener('click', () => this.toggleDrawer(true));
    }

    // Suggestion pills
    document.querySelectorAll('.suggestion-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        if (this.chatInput) {
          this.chatInput.value = pill.textContent.trim();
          this.sendMessage();
        }
      });
    });

    // Listen to real-time telemetry updates for reactive emotions
    window.addEventListener('telemetry-update', (e) => {
      const snap = e.detail;
      const score = snap.health ? snap.health.score : 100;
      const threatCount = snap.threats ? snap.threats.length : 0;
      const cpu = snap.cpu ? snap.cpu.total_percent : 0;
      this.setEmotion(score, threatCount, cpu);
    });
  }

  toggleDrawer(open) {
    if (!this.drawer) return;
    const shouldOpen = open !== undefined ? open : !this.drawer.classList.contains('open');
    if (shouldOpen) {
      this.drawer.classList.add('open');
      if (this.speechBubble) this.speechBubble.style.display = 'none';
      if (this.chatInput) this.chatInput.focus();
      this.updateMetrics();
    } else {
      this.drawer.classList.remove('open');
    }
  }

  setEmotion(score, threatCount, cpu) {
    if (!this.avatarBtn) return;
    this.avatarBtn.className = 'dahoo-avatar-btn';
    if (threatCount > 0 || score < 40) {
      this.avatarBtn.classList.add('alert');
    } else if (cpu > 85 || score < 65) {
      this.avatarBtn.classList.add('worried');
    } else if (score >= 85) {
      this.avatarBtn.classList.add('happy');
    } else {
      this.avatarBtn.classList.add('normal');
    }
  }

  async updateState() {
    try {
      const res = await fetch('/api/dahoo/state');
      if (res.ok) {
        const data = await res.json();
        if (this.speechBubble && data.proactive_speech) {
          this.speechBubble.textContent = data.proactive_speech;
        }
        if (this.modelBadge) {
          this.modelBadge.textContent = data.cloud_model;
        }
        if (this.cloudToggle && !data.cloud_available) {
          this.cloudToggle.disabled = true;
          this.cloudToggle.title = "Configure GEMINI_API_KEY in .env to enable Cloud AI";
        }
      }
    } catch (e) {}
  }

  async updateMetrics() {
    try {
      const res = await fetch('/api/dahoo/metrics');
      if (res.ok) {
        const stats = await res.json();
        if (this.costBadge) this.costBadge.textContent = `$${stats.total_cost.toFixed(5)}`;
        if (this.tokenBadge) this.tokenBadge.textContent = stats.total_tokens.toLocaleString();
      }
    } catch (e) {}
  }

  appendMessage(role, text, meta = '') {
    if (!this.chatBody) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    msgDiv.appendChild(bubble);

    if (meta) {
      const metaSpan = document.createElement('span');
      metaSpan.className = 'chat-meta';
      metaSpan.textContent = meta;
      msgDiv.appendChild(metaSpan);
    }

    this.chatBody.appendChild(msgDiv);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  async sendMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    this.chatInput.value = '';
    this.appendMessage('user', text);

    // Thinking state
    if (this.avatarBtn) this.avatarBtn.classList.add('thinking');
    const useCloud = this.cloudToggle ? this.cloudToggle.checked : false;

    try {
      const res = await fetch('/api/dahoo/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, use_cloud: useCloud })
      });

      if (res.ok) {
        const data = await res.json();
        const metaText = `${data.model} • ${data.input_tokens + data.output_tokens} tokens ($${data.estimated_cost})`;
        this.appendMessage('assistant', data.reply, metaText);
        this.updateMetrics();
      } else {
        this.appendMessage('assistant', 'Aww, maaf terjadi kesalahan komunikasi dengan server.');
      }
    } catch (err) {
      this.appendMessage('assistant', `Aww, server error: ${err.message}`);
    } finally {
      if (this.avatarBtn) this.avatarBtn.classList.remove('thinking');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.dahoo = new DahooController();
});
