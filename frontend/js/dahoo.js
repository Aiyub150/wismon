/**
 * Dahoo Assistant UI Controller.
 * Features an interactive Wolf Mascot with dynamic facial expressions,
 * WhatsApp-style conversational chat bubbles, typing indicator, and transparent AI mode routing.
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
    this.cloudAvailable = false;
    this.currentEmotion = 'normal';

    this.renderWolfAvatar('normal');
    this.initEvents();
    this.updateState();
    setInterval(() => this.updateMetrics(), 15000);
  }

  renderWolfAvatar(emotion = 'normal') {
    if (!this.avatarBtn) return;
    this.currentEmotion = emotion;

    // Eye shape and expression paths based on emotion
    let eyeLeft = '<ellipse cx="15" cy="22" rx="2.5" ry="3.5" fill="#FFFFFF"/><circle cx="15.5" cy="21.5" r="1.5" fill="#1C2434"/>';
    let eyeRight = '<ellipse cx="29" cy="22" rx="2.5" ry="3.5" fill="#FFFFFF"/><circle cx="28.5" cy="21.5" r="1.5" fill="#1C2434"/>';
    let mouth = '<path d="M19 28 Q22 31 25 28" stroke="#1C2434" stroke-width="1.5" fill="none" stroke-linecap="round"/>';
    let extras = '';

    if (emotion === 'happy') {
      eyeLeft = '<path d="M12.5 22 Q15 19 17.5 22" stroke="#FFFFFF" stroke-width="2.5" fill="none" stroke-linecap="round"/>';
      eyeRight = '<path d="M26.5 22 Q29 19 31.5 22" stroke="#FFFFFF" stroke-width="2.5" fill="none" stroke-linecap="round"/>';
      mouth = '<path d="M18 27 Q22 33 26 27" stroke="#1C2434" stroke-width="1.8" fill="#F43F5E" stroke-linecap="round"/>';
    } else if (emotion === 'worried') {
      eyeLeft = '<ellipse cx="15" cy="23" rx="2" ry="3" fill="#FFFFFF"/><circle cx="15" cy="22.5" r="1.2" fill="#1C2434"/>';
      eyeRight = '<ellipse cx="29" cy="23" rx="2" ry="3" fill="#FFFFFF"/><circle cx="29" cy="22.5" r="1.2" fill="#1C2434"/>';
      mouth = '<path d="M19 30 Q22 27 25 30" stroke="#1C2434" stroke-width="1.5" fill="none" stroke-linecap="round"/>';
      // Sweat drop
      extras = '<path d="M34 14 C34 12 36 9 36 9 C36 9 38 12 38 14 C38 15.5 36.8 16.5 35.5 16.5 C34.5 16.5 34 15.5 34 14 Z" fill="#38BDF8"/>';
    } else if (emotion === 'alert') {
      eyeLeft = '<ellipse cx="15" cy="22" rx="3" ry="4" fill="#FEE2E2"/><circle cx="15.5" cy="22" r="2" fill="#DC2626"/>';
      eyeRight = '<ellipse cx="29" cy="22" rx="3" ry="4" fill="#FEE2E2"/><circle cx="28.5" cy="22" r="2" fill="#DC2626"/>';
      mouth = '<circle cx="22" cy="29" r="2.5" fill="#1C2434"/>';
      // Alert badge
      extras = '<circle cx="37" cy="9" r="6" fill="#EF4444" stroke="#FFFFFF" stroke-width="1.5"/><text x="37" y="13" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">!</text>';
    }

    const wolfSvg = `
      <svg viewBox="0 0 44 44" class="wolf-svg">
        <!-- Wolf Ears -->
        <polygon points="6,18 12,2 20,12" fill="#94A3B8"/>
        <polygon points="8,16 13,5 18,12" fill="#F472B6"/>
        <polygon points="38,18 32,2 24,12" fill="#94A3B8"/>
        <polygon points="36,16 31,5 26,12" fill="#F472B6"/>

        <!-- Wolf Head -->
        <path d="M10,14 Q22,9 34,14 Q41,25 36,36 Q22,43 8,36 Q3,25 10,14 Z" fill="#E2E8F0"/>
        
        <!-- Cheeks and Fur -->
        <polygon points="3,25 10,23 7,29" fill="#CBD5E1"/>
        <polygon points="41,25 34,23 37,29" fill="#CBD5E1"/>
        <path d="M14,18 Q22,23 30,18 Q34,32 22,36 Q10,32 14,18 Z" fill="#FFFFFF"/>

        <!-- Eyes -->
        ${eyeLeft}
        ${eyeRight}

        <!-- Snout and Nose -->
        <polygon points="20,24 24,24 22,27" fill="#1E293B"/>
        ${mouth}

        <!-- Extras (sweat drop, alert badge) -->
        ${extras}
      </svg>
    `;

    this.avatarBtn.innerHTML = wolfSvg;

    // Also update drawer header wolf avatar if present
    const drawerAvatar = document.querySelector('.drawer-avatar');
    if (drawerAvatar) {
      drawerAvatar.innerHTML = wolfSvg;
    }
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

    // Cloud toggle change event
    if (this.cloudToggle) {
      this.cloudToggle.addEventListener('change', () => {
        const isCloud = this.cloudToggle.checked;
        if (this.modelBadge) {
          this.modelBadge.textContent = isCloud ? '● Gemini Cloud' : '● Local AI (Offline)';
          this.modelBadge.className = isCloud ? 'badge badge-primary font-mono' : 'badge badge-neutral font-mono';
        }
      });
    }

    // Listen to real-time telemetry updates for reactive wolf emotions
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
    let emotion = 'normal';
    if (threatCount > 0 || score < 40) {
      emotion = 'alert';
    } else if (cpu > 85 || score < 65) {
      emotion = 'worried';
    } else if (score >= 85) {
      emotion = 'happy';
    }

    this.avatarBtn.className = `dahoo-avatar-btn ${emotion}`;
    if (emotion !== this.currentEmotion) {
      this.renderWolfAvatar(emotion);
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
        this.cloudAvailable = data.cloud_available || false;
        if (this.modelBadge) {
          this.modelBadge.textContent = this.cloudAvailable ? '● Cloud AI Ready' : '● Local AI (Offline)';
        }
        if (this.cloudToggle) {
          if (!this.cloudAvailable) {
            this.cloudToggle.disabled = true;
            this.cloudToggle.checked = false;
            this.cloudToggle.title = 'Configure GEMINI_API_KEY in .env to enable Cloud AI';
          } else {
            this.cloudToggle.disabled = false;
          }
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

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    msgDiv.appendChild(bubble);

    const metaSpan = document.createElement('span');
    metaSpan.className = 'chat-meta';
    if (role === 'user') {
      metaSpan.innerHTML = `<span>${timeStr}</span> <span style="color:#60A5FA;">✓✓</span>`;
    } else {
      metaSpan.innerHTML = `<span>${timeStr}</span> ${meta ? '• ' + meta : ''}`;
    }
    msgDiv.appendChild(metaSpan);

    this.chatBody.appendChild(msgDiv);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  showTypingIndicator() {
    if (!this.chatBody || document.getElementById('dahoo-typing-msg')) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg assistant';
    msgDiv.id = 'dahoo-typing-msg';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = `
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;
    msgDiv.appendChild(bubble);
    this.chatBody.appendChild(msgDiv);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  removeTypingIndicator() {
    const typing = document.getElementById('dahoo-typing-msg');
    if (typing) typing.remove();
  }

  async sendMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    this.chatInput.value = '';
    this.appendMessage('user', text);
    this.showTypingIndicator();

    if (this.avatarBtn) this.avatarBtn.classList.add('thinking');
    const useCloud = this.cloudToggle ? this.cloudToggle.checked : false;

    try {
      const res = await fetch('/api/dahoo/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, use_cloud: useCloud })
      });

      this.removeTypingIndicator();

      if (res.ok) {
        const data = await res.json();
        const metaText = data.engine === 'cloud' 
          ? `${data.model} (${data.input_tokens + data.output_tokens} tok)`
          : 'Local Rule Engine';
        this.appendMessage('assistant', data.reply, metaText);
        this.updateMetrics();
      } else {
        this.appendMessage('assistant', 'Aww, maaf terjadi kendala saat memproses permintaanmu. Coba tanyakan kembali.');
      }
    } catch (err) {
      this.removeTypingIndicator();
      this.appendMessage('assistant', `Aww, server offline: ${err.message}`);
    } finally {
      if (this.avatarBtn) this.avatarBtn.classList.remove('thinking');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.dahoo = new DahooController();
});
