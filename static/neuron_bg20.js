/* ═══════════════════════════════════════════════════════════════════════════
   NEURON v20 — Premium 3D neural observatory background
   Developed by Vipul Jakhar.
   Advanced 3D perspective projection, dynamic camera rotation, mouse parallax,
   depth sorting, synapse pulses with decay tails, and theme-adaptive colors.
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  const cv = document.getElementById("bg-canvas");
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext("2d", { alpha: true });
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DPR = Math.min(window.devicePixelRatio || 1, 2);

  let W = 0, H = 0, t = 0, raf = null;
  let mx = 0, my = 0, tmx = 0, tmy = 0; // Mouse offsets
  let scrollPct = 0;

  // 3D parameters
  const FOV = 400; // Perspective FOV
  let nodes = [];
  let stars = [];
  let pulses = [];

  function isDark() {
    return document.documentElement.dataset.theme !== "light";
  }

  // 3D rotation utilities
  function rotateY(x, y, z, angle) {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    return {
      x: x * cos - z * sin,
      y: y,
      z: x * sin + z * cos
    };
  }

  function rotateX(x, y, z, angle) {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    return {
      x: x,
      y: y * cos - z * sin,
      z: y * sin + z * cos
    };
  }

  function resize() {
    W = cv.width  = Math.floor(innerWidth  * DPR);
    H = cv.height = Math.floor(innerHeight * DPR);
    cv.style.width  = innerWidth  + "px";
    cv.style.height = innerHeight + "px";

    const countMultiplier = Math.min(1.5, (innerWidth * innerHeight) / (1280 * 800));

    // Initialize 3D Stars (distant background plane)
    const nStar = Math.min(250, Math.round(150 * countMultiplier));
    stars = Array.from({ length: nStar }, () => ({
      x: (Math.random() - 0.5) * 1.5,
      y: (Math.random() - 0.5) * 1.5,
      z: 0.8 + Math.random() * 0.4,
      r: (0.3 + Math.random() * 0.5) * DPR,
      a: 0.08 + Math.random() * 0.18,
      ph: Math.random() * Math.PI * 2,
      sp: 0.2 + Math.random() * 0.4
    }));

    // Initialize 3D Neural Nodes (mid and near combined for depth sorting)
    // Coords normalized in [-0.5, 0.5]
    const nNodes = Math.max(50, Math.min(110, Math.round(75 * countMultiplier)));
    nodes = Array.from({ length: nNodes }, (v, i) => {
      const isNear = i < 8; // First 8 are near prominent nodes
      return {
        x: (Math.random() - 0.5) * 0.9,
        y: (Math.random() - 0.5) * 0.9,
        z: (Math.random() - 0.5) * 0.9,
        isNear: isNear,
        r: (isNear ? (2.0 + Math.random() * 1.5) : (0.6 + Math.random() * 0.8)) * DPR,
        warm: Math.random() < (isNear ? 0.6 : 0.15),
        ph: Math.random() * Math.PI * 2,
        sp: 0.15 + Math.random() * 0.35,
        amp: 0.03 + Math.random() * 0.05
      };
    });

    pulses = [];
    if (reduce) { frame(); } else { if (!raf) start(); }
  }

  function maybeSpawnPulse(edges) {
    if (edges.length && Math.random() < 0.045 && pulses.length < 15) {
      const e = edges[Math.floor(Math.random() * edges.length)];
      pulses.push({
        ax: e.ax, ay: e.ay, az: e.az,
        bx: e.bx, by: e.by, bz: e.bz,
        p: 0,
        sp: 0.008 + Math.random() * 0.015
      });
    }
    pulses = pulses.filter(p => {
      p.p += p.sp;
      return p.p < 1.0;
    });
  }

  function frame() {
    t += 0.0036;
    // Mouse ease transition
    mx += (tmx - mx) * 0.045;
    my += (tmy - my) * 0.045;

    ctx.clearRect(0, 0, W, H);

    const dark = isDark();
    const centerX = W / 2;
    const centerY = H / 2;

    // Determine camera rotations based on time, mouse coordinates, and scroll progress
    const rotYAngle = t * 0.08 + mx * 0.28;
    const rotXAngle = Math.sin(t * 0.05) * 0.06 - my * 0.18 + (scrollPct - 0.5) * 0.15;

    // ── Distant 3D Twinkling Star Field ──
    const starColor = dark ? [180, 200, 255] : [160, 130, 90];
    for (const s of stars) {
      // Small rotation for parallax
      let rPt = rotateY(s.x, s.y, s.z, rotYAngle * 0.12);
      rPt = rotateX(rPt.x, rPt.y, rPt.z, rotXAngle * 0.12);

      const fovScale = FOV / (rPt.z + 1.2);
      const px = centerX + rPt.x * W * fovScale * 0.6;
      const py = centerY + rPt.y * H * fovScale * 0.6;

      if (px >= 0 && px <= W && py >= 0 && py <= H) {
        const starTwinkle = s.a * (0.5 + 0.5 * Math.sin(t * s.sp + s.ph));
        ctx.fillStyle = `rgba(${starColor[0]},${starColor[1]},${starColor[2]},${starTwinkle.toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(px, py, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // ── Project and Rotate Neural Network Nodes ──
    const projNodes = nodes.map(n => {
      // Add subtle internal drift physics
      const driftAngle = t * n.sp + n.ph;
      const dx = Math.cos(driftAngle) * n.amp;
      const dy = Math.sin(driftAngle) * n.amp;
      const dz = Math.sin(driftAngle * 1.5) * n.amp;

      let rPt = rotateY(n.x + dx, n.y + dy, n.z + dz, rotYAngle);
      rPt = rotateX(rPt.x, rPt.y, rPt.z, rotXAngle);

      // Perspective projection
      const fovScale = FOV / (rPt.z + 1.5);
      const sx = centerX + rPt.x * W * fovScale * 0.45;
      const sy = centerY + rPt.y * H * fovScale * 0.45;

      return {
        sx, sy,
        sz: rPt.z, // Rotated Z coordinate for depth sorting
        rawX: rPt.x, rawY: rPt.y, rawZ: rPt.z,
        r: n.r * (fovScale * 0.5),
        isNear: n.isNear,
        warm: n.warm,
        ph: n.ph,
        sp: n.sp
      };
    });

    // ── Generate Synapse Edges ──
    const edges = [];
    const maxDist = 0.22; // Normalized threshold
    const maxDistSq = maxDist * maxDist;

    for (let i = 0; i < projNodes.length; i++) {
      for (let j = i + 1; j < projNodes.length; j++) {
        const a = projNodes[i];
        const b = projNodes[j];

        // Euclidean distance in 3D space
        const dx = a.rawX - b.rawX;
        const dy = a.rawY - b.rawY;
        const dz = a.rawZ - b.rawZ;
        const dsq = dx * dx + dy * dy + dz * dz;

        if (dsq < maxDistSq) {
          const alpha = (1 - dsq / maxDistSq) * 0.25 * (1 - (a.sz + b.sz) / 4);
          if (alpha > 0.01) {
            edges.push({
              ax: a.sx, ay: a.sy, az: a.sz,
              bx: b.sx, by: b.sy, bz: b.sz,
              alpha: alpha,
              z: (a.sz + b.sz) / 2
            });
          }
        }
      }
    }

    // ── Spawn and Update Signal Pulses ──
    maybeSpawnPulse(edges);

    // ── Depth Sorting (Important for authentic 3D overlaps) ──
    // Gather all renderable elements (edges, pulses, nodes)
    const renderQueue = [];

    // Edges
    const edgeColor = dark ? [90, 115, 215] : [130, 100, 60];
    edges.forEach(e => {
      renderQueue.push({
        z: e.z,
        type: 'edge',
        draw: () => {
          ctx.strokeStyle = `rgba(${edgeColor[0]},${edgeColor[1]},${edgeColor[2]},${e.alpha.toFixed(3)})`;
          ctx.lineWidth = DPR * 0.45;
          ctx.beginPath();
          ctx.moveTo(e.ax, e.ay);
          ctx.lineTo(e.bx, e.by);
          ctx.stroke();
        }
      });
    });

    // Pulses
    const pulseColor = dark ? [235, 185, 75] : [195, 120, 40];
    pulses.forEach(p => {
      // Interpolate 3D position
      const x = p.ax + (p.bx - p.ax) * p.p;
      const y = p.ay + (p.by - p.ay) * p.p;
      const z = p.az + (p.bz - p.az) * p.p;
      const alpha = Math.sin(p.p * Math.PI) * 0.85;

      renderQueue.push({
        z: z,
        type: 'pulse',
        draw: () => {
          ctx.fillStyle = `rgba(${pulseColor[0]},${pulseColor[1]},${pulseColor[2]},${alpha.toFixed(3)})`;
          ctx.beginPath();
          ctx.arc(x, y, 2.2 * DPR, 0, Math.PI * 2);
          ctx.fill();
        }
      });
    });

    // Nodes
    const nodeColor = dark ? [105, 130, 205] : [110, 88, 52];
    const warmColor = dark ? [235, 185, 75] : [195, 135, 38];

    projNodes.forEach(n => {
      const baseColor = n.warm ? warmColor : nodeColor;
      const nodeAlpha = 0.22 + (1.5 - n.sz) * 0.35; // depth-based opacity

      if (n.isNear) {
        // High-end glowing breathing nodes
        renderQueue.push({
          z: n.sz,
          type: 'near-node',
          draw: () => {
            const breathing = nodeAlpha * (0.6 + 0.4 * Math.sin(t * n.sp * 2.5 + n.ph));
            // Core
            ctx.fillStyle = `rgba(${baseColor[0]},${baseColor[1]},${baseColor[2]},${breathing.toFixed(3)})`;
            ctx.beginPath();
            ctx.arc(n.sx, n.sy, n.r, 0, Math.PI * 2);
            ctx.fill();
            // Outer glow ring
            ctx.strokeStyle = `rgba(${baseColor[0]},${baseColor[1]},${baseColor[2]},${(breathing * 0.25).toFixed(3)})`;
            ctx.lineWidth = DPR * 0.75;
            ctx.beginPath();
            ctx.arc(n.sx, n.sy, n.r * 2.8, 0, Math.PI * 2);
            ctx.stroke();
          }
        });
      } else {
        // Standard background node
        renderQueue.push({
          z: n.sz,
          type: 'node',
          draw: () => {
            ctx.fillStyle = `rgba(${baseColor[0]},${baseColor[1]},${baseColor[2]},${nodeAlpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.arc(n.sx, n.sy, n.r, 0, Math.PI * 2);
            ctx.fill();
          }
        });
      }
    });

    // Sort render items descending by rotated Z coordinate (painter's algorithm)
    // Z is back-to-front (larger Z is farther, smaller Z is closer)
    renderQueue.sort((a, b) => b.z - a.z);

    // Draw everything in order
    renderQueue.forEach(item => item.draw());

    if (!reduce) raf = requestAnimationFrame(frame);
  }

  function start() {
    if (!raf && !reduce) raf = requestAnimationFrame(frame);
  }

  function stop() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = null;
    }
  }

  window.addEventListener("pointermove", e => {
    // Center mouse coordinates around 0 [-0.5, 0.5]
    tmx = (e.clientX / innerWidth) - 0.5;
    tmy = (e.clientY / innerHeight) - 0.5;
  }, { passive: true });

  window.addEventListener("scroll", () => {
    scrollPct = Math.min(1, (window.scrollY || 0) / Math.max(1, document.body.scrollHeight - innerHeight));
  }, { passive: true });

  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());

  // RETHEME API called on manual theme shifts
  window.NEURON_BG = {
    retheme: () => {
      if (reduce) frame();
    }
  };

  resize();
  if (!reduce) start(); else frame();
})();
