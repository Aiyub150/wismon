/**
 * Lightweight Real-Time HTML5 Canvas Time-Series Chart Engine.
 * Supports multi-series, gradient fills, gridlines, auto-scaling, smooth updates,
 * high-DPI crisp rendering without layout overflow, and interactive hover tooltips.
 */

class MiniChart {
  constructor(canvasId, options = {}) {
    this.canvasId = canvasId;
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.options = Object.assign({
      maxPoints: 60,
      minY: 0,
      maxY: 100,
      autoScaleY: false,
      color: '#3C50E0',
      gradientFill: true,
      unit: '%',
      label: 'Value'
    }, options);

    this.dataPoints = []; // Array of { val: number, timeStr: string, timestamp: number }
    this.hoverIndex = -1;
    this.width = 0;
    this.height = 0;

    // Canvas styling to prevent overflow
    this.canvas.style.display = 'block';
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';

    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Hover tooltip interactions
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.canvas.addEventListener('mouseleave', () => this.onMouseLeave());
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    if (!parent) return;

    const rect = parent.getBoundingClientRect();
    if (rect.width <= 0) return; // Parent is hidden (display: none)

    const dpr = window.devicePixelRatio || 1;
    const cssWidth = Math.floor(rect.width);
    const cssHeight = Math.floor(rect.height) || 180;

    this.canvas.width = cssWidth * dpr;
    this.canvas.height = cssHeight * dpr;
    this.canvas.style.width = cssWidth + 'px';
    this.canvas.style.height = cssHeight + 'px';

    this.ctx.resetTransform?.();
    this.ctx.scale(dpr, dpr);
    this.width = cssWidth;
    this.height = cssHeight;
    this.render();
  }

  push(value, customTime = null) {
    if (value === null || value === undefined || isNaN(value)) value = 0;

    const now = new Date();
    const timeStr = customTime || now.toLocaleTimeString('en-GB', { hour12: false });
    this.dataPoints.push({
      val: Number(value),
      timeStr: timeStr,
      timestamp: Date.now()
    });

    if (this.dataPoints.length > this.options.maxPoints) {
      this.dataPoints.shift();
    }

    // Auto-detect container visibility change
    if (this.width <= 0 && this.canvas && this.canvas.parentElement) {
      const w = this.canvas.parentElement.clientWidth;
      if (w > 0) this.resize();
    }

    this.render();
  }

  onMouseMove(e) {
    if (!this.width || this.dataPoints.length < 2) return;
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;

    const padTop = 15;
    const padBottom = 20;
    const w = this.width;
    const step = w / (this.options.maxPoints - 1);
    const startX = w - (this.dataPoints.length - 1) * step;

    // Find nearest point
    let closestIdx = -1;
    let minDiff = Infinity;
    for (let i = 0; i < this.dataPoints.length; i++) {
      const ptX = startX + i * step;
      const diff = Math.abs(mouseX - ptX);
      if (diff < minDiff && diff < (step * 1.5)) {
        minDiff = diff;
        closestIdx = i;
      }
    }

    if (closestIdx !== this.hoverIndex) {
      this.hoverIndex = closestIdx;
      this.render();
    }
  }

  onMouseLeave() {
    if (this.hoverIndex !== -1) {
      this.hoverIndex = -1;
      this.render();
    }
  }

  render() {
    if (!this.ctx || !this.width || !this.height) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const padTop = 16;
    const padBottom = 22;
    const chartHeight = h - padTop - padBottom;

    ctx.clearRect(0, 0, w, h);

    // Calculate Y limits
    let minY = this.options.minY;
    let maxY = this.options.maxY;
    if (this.options.autoScaleY && this.dataPoints.length > 0) {
      const maxVal = Math.max(...this.dataPoints.map(p => p.val));
      maxY = Math.max(maxVal * 1.25, 5);
    }

    // Dynamic gridlines based on theme
    const isDark = document.documentElement.classList.contains('dark');
    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.05)';
    ctx.lineWidth = 1;
    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const y = padTop + (chartHeight / gridSteps) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();

      // Axis label
      const val = Math.round(maxY - ((maxY - minY) / gridSteps) * i);
      ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(100, 116, 139, 0.75)';
      ctx.font = '10px monospace';
      ctx.fillText(`${val}${this.options.unit}`, 6, y - 3);
    }

    if (this.dataPoints.length < 2) return;

    // Calculate point coordinates
    const step = w / (this.options.maxPoints - 1);
    const startX = w - (this.dataPoints.length - 1) * step;

    const points = this.dataPoints.map((item, idx) => {
      const norm = Math.max(0, Math.min(1, (item.val - minY) / (maxY - minY || 1)));
      const x = startX + idx * step;
      const y = padTop + chartHeight * (1 - norm);
      return { x, y, ...item };
    });

    // Draw Area Fill
    if (this.options.gradientFill) {
      const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
      grad.addColorStop(0, this.hexToRgba(this.options.color, 0.3));
      grad.addColorStop(1, this.hexToRgba(this.options.color, 0.0));

      ctx.beginPath();
      ctx.moveTo(points[0].x, h - padBottom);
      ctx.lineTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const xc = (points[i - 1].x + points[i].x) / 2;
        const yc = (points[i - 1].y + points[i].y) / 2;
        ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
      }
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
      ctx.lineTo(points[points.length - 1].x, h - padBottom);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
    }

    // Draw Stroke Curve
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      const xc = (points[i - 1].x + points[i].x) / 2;
      const yc = (points[i - 1].y + points[i].y) / 2;
      ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    ctx.strokeStyle = this.options.color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Pulse dot at latest point
    const last = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = this.options.color;
    ctx.shadowColor = this.options.color;
    ctx.shadowBlur = 6;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Render Hover Tooltip if active
    if (this.hoverIndex >= 0 && this.hoverIndex < points.length) {
      const hp = points[this.hoverIndex];

      // Vertical guide dashed line
      ctx.save();
      ctx.setLineDash([3, 3]);
      ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.45)' : 'rgba(0, 0, 0, 0.35)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(hp.x, padTop);
      ctx.lineTo(hp.x, h - padBottom);
      ctx.stroke();
      ctx.restore();

      // Highlight target point
      ctx.beginPath();
      ctx.arc(hp.x, hp.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.strokeStyle = this.options.color;
      ctx.lineWidth = 3;
      ctx.fill();
      ctx.stroke();

      // Tooltip Card
      const tooltipVal = `${hp.val}${this.options.unit}`;
      const tooltipTime = hp.timeStr || 'now';
      const line1 = `${this.options.label || 'Load'}: ${tooltipVal}`;
      const line2 = `Time: ${tooltipTime}`;

      ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
      const m1 = ctx.measureText(line1);
      ctx.font = '10px system-ui, -apple-system, sans-serif';
      const m2 = ctx.measureText(line2);
      const boxW = Math.max(m1.width, m2.width) + 20;
      const boxH = 40;

      let boxX = hp.x - boxW / 2;
      if (boxX < 10) boxX = 10;
      if (boxX + boxW > w - 10) boxX = w - boxW - 10;

      let boxY = hp.y - boxH - 10;
      if (boxY < padTop) boxY = hp.y + 12;

      // Tooltip background
      ctx.fillStyle = isDark ? '#1C2434' : '#FFFFFF';
      ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.15)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 6);
      ctx.fill();
      ctx.stroke();

      // Tooltip Text
      ctx.fillStyle = this.options.color;
      ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
      ctx.fillText(line1, boxX + 10, boxY + 16);

      ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
      ctx.font = '10px system-ui, -apple-system, sans-serif';
      ctx.fillText(line2, boxX + 10, boxY + 31);
    }
  }

  hexToRgba(hex, alpha) {
    let c;
    if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
      c = hex.substring(1).split('');
      if (c.length === 3) c = [c[0], c[0], c[1], c[1], c[2], c[2]];
      c = '0x' + c.join('');
      return `rgba(${(c >> 16) & 255}, ${(c >> 8) & 255}, ${c & 255}, ${alpha})`;
    }
    return hex;
  }
}

window.MiniChart = MiniChart;
