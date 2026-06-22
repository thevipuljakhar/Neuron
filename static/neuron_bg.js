/* ═══════════════════════════════════════════════════════════════════════════
   NEURON v22 — Deep-space neural field background
   Three depth planes: star-field (far) · neural net (mid) · feature nodes (near)
   Signal pulses travel along edges. Everything is kept dim and distant so the
   data panels float above it without competition.
   Theme-aware, parallax on mouse + scroll, pauses when hidden.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  const cv = document.getElementById("bg-canvas");
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext("2d", { alpha: true });
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DPR = Math.min(window.devicePixelRatio || 1, 2);

  let W = 0, H = 0, t = 0, raf = null;
  let mx = 0.5, my = 0.5, tmx = 0.5, tmy = 0.5, sNorm = 0;

  // Three planes
  let stars = [], mids = [], nears = [], pulses = [];

  function isDark() {
    return document.documentElement.dataset.theme !== "light";
  }

  function resize() {
    W = cv.width  = Math.floor(innerWidth  * DPR);
    H = cv.height = Math.floor(innerHeight * DPR);
    cv.style.width  = innerWidth  + "px";
    cv.style.height = innerHeight + "px";

    // Far plane — sparse star/constellation field
    const nStar = Math.min(180, Math.round((innerWidth * innerHeight) / 5500));
    stars = Array.from({ length: nStar }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: (0.25 + Math.random() * 0.6) * DPR,
      a: 0.06 + Math.random() * 0.14,
      ph: Math.random() * Math.PI * 2,
      sp: 0.15 + Math.random() * 0.4,
      dx: (Math.random() - 0.5) * 6,   // parallax offset multipliers
      dy: (Math.random() - 0.5) * 5,
    }));

    // Mid plane — neural net backbone
    const nMid = Math.max(40, Math.min(80, Math.round((innerWidth * innerHeight) / 16000)));
    mids = Array.from({ length: nMid }, () => ({
      bx: Math.random(), by: Math.random(),
      z: 0.25 + Math.random() * 0.55,
      r: (0.6 + Math.random() * 1.1) * DPR,
      warm: Math.random() < 0.18,
      amp: 0.004 + Math.random() * 0.009,
      ph: Math.random() * Math.PI * 2,
      sp: 0.25 + Math.random() * 0.65,
    }));

    // Near plane — 6–10 prominent feature nodes that glow and pulse
    nears = Array.from({ length: 7 }, () => ({
      bx: Math.random(), by: Math.random(),
      z: 0.75 + Math.random() * 0.25,
      r: (1.8 + Math.random() * 2.2) * DPR,
      warm: Math.random() < 0.55,
      amp: 0.002 + Math.random() * 0.005,
      ph: Math.random() * Math.PI * 2,
      sp: 0.1 + Math.random() * 0.25,
    }));

    pulses = [];
    if (reduce) { frame(); } else { if (!raf) start(); }
  }

  function maybeSpawnPulse(edges) {
    if (edges.length && Math.random() < 0.035 && pulses.length < 10) {
      const e = edges[Math.floor(Math.random() * edges.length)];
      pulses.push({ ...e, p: 0, sp: 0.006 + Math.random() * 0.012 });
    }
    pulses = pulses.filter(p => { p.p += p.sp; return p.p < 1.05; });
  }

  function frame() {
    t += 0.0028;
    mx += (tmx - mx) * 0.038;
    my += (tmy - my) * 0.038;
    ctx.clearRect(0, 0, W, H);

    const dark = isDark();
    const px = mx - 0.5, py = my - 0.5;

    // ── Far plane: twinkling star field ──
    const sc = dark ? [185, 205, 255] : [160, 130, 80];
    for (const s of stars) {
      const a = s.a * (0.55 + 0.45 * Math.sin(t * s.sp + s.ph));
      ctx.fillStyle = `rgba(${sc[0]},${sc[1]},${sc[2]},${a.toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(s.x + px * s.dx, s.y + py * s.dy, s.r, 0, 6.2832);
      ctx.fill();
    }

    // ── Mid plane: project node positions ──
    const allPts = [...mids, ...nears].map(p => {
      const drift = Math.sin(t * p.sp + p.ph) * p.amp;
      const x = (p.bx + drift + px * 0.055 * p.z) * W;
      let y = (p.by + sNorm * 0.07 * p.z + py * 0.038 * p.z) % 1.0;
      if (y < 0) y += 1;
      return { x, y: y * H, z: p.z, r: p.r, warm: p.warm, sp: p.sp, ph: p.ph };
    });
    const midPts  = allPts.slice(0, mids.length);
    const nearPts = allPts.slice(mids.length);

    // ── Mid plane: synapse links ──
    const maxd = 125 * DPR, maxd2 = maxd * maxd;
    const lc = dark ? [88, 112, 210] : [120, 90, 50];
    const edges = [];
    ctx.lineWidth = DPR * 0.42;
    for (let i = 0; i < midPts.length; i++) {
      for (let j = i + 1; j < midPts.length; j++) {
        const a = midPts[i], b = midPts[j];
        const dx = a.x - b.x, dy = a.y - b.y, d2 = dx*dx + dy*dy;
        if (d2 < maxd2) {
          const al = (1 - d2 / maxd2) * 0.24 * Math.min(a.z, b.z);
          ctx.strokeStyle = `rgba(${lc[0]},${lc[1]},${lc[2]},${al.toFixed(3)})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          if (al > 0.04) edges.push({ ax: a.x, ay: a.y, bx: b.x, by: b.y });
        }
      }
    }

    // ── Signal pulses traveling along edges ──
    maybeSpawnPulse(edges);
    const pc = dark ? [233, 185, 73] : [180, 100, 30];
    for (const p of pulses) {
      const x = p.ax + (p.bx - p.ax) * p.p;
      const y = p.ay + (p.by - p.ay) * p.p;
      const a = Math.sin(p.p * Math.PI) * 0.85;
      ctx.fillStyle = `rgba(${pc[0]},${pc[1]},${pc[2]},${a.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(x, y, 2.0 * DPR, 0, 6.2832); ctx.fill();
    }

    // ── Mid nodes ──
    const nc = dark ? [105, 125, 198] : [110, 85, 48];
    const wc = dark ? [233, 185, 73]  : [195, 135, 38];
    for (const p of midPts) {
      const c = p.warm ? wc : nc;
      const a = 0.14 + p.z * 0.28;
      ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.2832); ctx.fill();
    }

    // ── Near nodes — brighter, breathe, have glow rings ──
    for (const p of nearPts) {
      const c = p.warm ? wc : nc;
      const pulse_a = 0.28 + 0.18 * Math.sin(t * p.sp * 2.2 + p.ph);
      ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},${pulse_a.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.2832); ctx.fill();
      // outer glow ring
      ctx.strokeStyle = `rgba(${c[0]},${c[1]},${c[2]},${(pulse_a * 0.22).toFixed(3)})`;
      ctx.lineWidth = DPR * 0.8;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 2.8, 0, 6.2832); ctx.stroke();
    }

    if (!reduce) raf = requestAnimationFrame(frame);
  }

  function start() { if (!raf && !reduce) raf = requestAnimationFrame(frame); }
  function stop()  { if (raf) { cancelAnimationFrame(raf); raf = null; } }

  window.addEventListener("pointermove", e => {
    tmx = e.clientX / innerWidth; tmy = e.clientY / innerHeight;
  }, { passive: true });
  window.addEventListener("scroll", () => {
    sNorm = Math.min(1, (window.scrollY || 0) / Math.max(1, document.body.scrollHeight - innerHeight));
  }, { passive: true });
  window.addEventListener("resize", () => { resize(); });
  document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());

  window.NEURON_BG = { retheme: () => { if (reduce) frame(); } };

  resize();
  if (!reduce) start(); else frame();
})();
