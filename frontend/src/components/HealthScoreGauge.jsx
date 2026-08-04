import { useEffect, useRef } from 'react';

export default function HealthScoreGauge({ score = 50 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const size = 200;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2 + 10;
    const radius = 75;
    const lineWidth = 12;
    const startAngle = Math.PI * 0.75;
    const endAngle = Math.PI * 2.25;

    // Animate
    let currentScore = 0;
    const targetScore = Math.max(0, Math.min(100, score));
    const duration = 1500;
    const startTime = performance.now();

    const getColor = (s) => {
      if (s >= 75) return '#10b981';
      if (s >= 50) return '#f59e0b';
      if (s >= 25) return '#ef4444';
      return '#dc2626';
    };

    const draw = (timestamp) => {
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // Ease-out cubic
      currentScore = eased * targetScore;

      ctx.clearRect(0, 0, size, size);

      // Background arc
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Value arc
      const scoreAngle = startAngle + (endAngle - startAngle) * (currentScore / 100);
      const color = getColor(currentScore);

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, scoreAngle);
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.shadowColor = color;
      ctx.shadowBlur = 15;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Score text
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 36px Outfit, Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(Math.round(currentScore), centerX, centerY - 5);

      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '12px Inter, sans-serif';
      ctx.fillText('/ 100', centerX, centerY + 22);

      if (progress < 1) requestAnimationFrame(draw);
    };

    requestAnimationFrame(draw);
  }, [score]);

  const getLabel = (s) => {
    if (s >= 75) return { text: 'Healthy', cls: 'text-emerald-400' };
    if (s >= 50) return { text: 'Fair', cls: 'text-amber-400' };
    if (s >= 25) return { text: 'At Risk', cls: 'text-red-400' };
    return { text: 'Critical', cls: 'text-red-300' };
  };

  const label = getLabel(score);

  return (
    <div className="glass-card p-6 flex flex-col items-center">
      <h3 className="section-title mb-2">
        💚 Business Health Score
      </h3>
      <canvas ref={canvasRef} />
      <span className={`text-sm font-semibold mt-1 ${label.cls}`}>
        {label.text}
      </span>
    </div>
  );
}
