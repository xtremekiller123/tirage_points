// Fond animé de particules mauves
window.addEventListener('DOMContentLoaded', function () {
  const canvas = document.createElement('canvas');
  canvas.id = 'bg-anim';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d');
  let w = window.innerWidth, h = window.innerHeight;
  function resize() {
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = w; canvas.height = h;
  }
  resize();
  window.addEventListener('resize', resize);
  // Particules
  const PARTICLE_COUNT = 40;
  const particles = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 8 + Math.random() * 18,
      dx: (Math.random() - 0.5) * 0.4,
      dy: (Math.random() - 0.5) * 0.25,
      alpha: 0.2 + Math.random() * 0.4
    });
  }
  function draw() {
    ctx.clearRect(0, 0, w, h);
    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
      ctx.fillStyle = `rgba(180,123,255,${p.alpha})`;
      ctx.shadowColor = '#b47bff';
      ctx.shadowBlur = 18;
      ctx.fill();
      ctx.shadowBlur = 0;
      p.x += p.dx; p.y += p.dy;
      if (p.x < -50) p.x = w + 50;
      if (p.x > w + 50) p.x = -50;
      if (p.y < -50) p.y = h + 50;
      if (p.y > h + 50) p.y = -50;
    }
    requestAnimationFrame(draw);
  }
  draw();
});

// Animation d'annonce de gagnant
window.showDrawAnnouncement = function (winner, percent, mise) {
  // Supprime l'encadré existant si déjà présent
  let old = document.getElementById('draw-announcement');
  if (old) old.remove();
  let box = document.createElement('div');
  box.id = 'draw-announcement';
  box.innerHTML = `🎉 <b>${winner}</b> a gagné le dernier tirage !<br><span style="font-size:0.97em;">Mise : <b>${mise}</b> | % de chance : <b>${percent}%</b></span>`;
  box.style.position = 'fixed';
  box.style.left = '50%';
  box.style.bottom = '18px';
  box.style.transform = 'translateX(-50%)';
  box.style.background = 'linear-gradient(90deg,#ffe066 0%,#b47bff 100%)';
  box.style.color = '#4e008e';
  box.style.padding = '1em 1.3em';
  box.style.borderRadius = '14px';
  box.style.fontSize = '1.08em';
  box.style.fontWeight = 'bold';
  box.style.boxShadow = '0 2px 12px #b47bff33';
  box.style.textAlign = 'center';
  box.style.zIndex = '9999';
  box.style.opacity = '1';
  box.style.maxWidth = '95vw';
  box.style.margin = '0 auto';
  document.body.appendChild(box);
};
