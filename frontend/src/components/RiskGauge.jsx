import { useEffect, useRef } from 'react';

export default function RiskGauge({ riskScore = 0, riskLevel = 'Unknown', distressProbability = 0, confidence = 0 }) {
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

    const targetScore = Math.max(0, Math.min(100, riskScore));
    const duration = 1500;
    const startTime = performance.now();

    const getColor = (s) => {
      if (s <= 25) return '#10b981';
      if (s <= 50) return '#f59e0b';
      if (s <= 75) return '#ef4444';
      return '#dc2626';
    };

    const draw = (timestamp) => {
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const currentScore = eased * targetScore;

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
  }, [riskScore]);

  const levelColor = {
    Low: 'risk-badge-low',
    Medium: 'risk-badge-medium',
    High: 'risk-badge-high',
    Critical: 'risk-badge-critical',
  }[riskLevel] || 'risk-badge-medium';

  return (
    <div className="glass-card p-6 flex flex-col items-center">
      <h3 className="section-title mb-2">
        ⚠️ Financial Distress Score
      </h3>
      <canvas ref={canvasRef} />
      <span className={`text-xs font-semibold px-3 py-1 rounded-full mt-1 ${levelColor}`}>
        {riskLevel} Risk
      </span>
      <div className="flex gap-4 mt-3 text-xs text-gray-500">
        <span>Probability: {(distressProbability * 100).toFixed(1)}%</span>
        <span>Confidence: {confidence}%</span>
      </div>
    </div>
  );
}
