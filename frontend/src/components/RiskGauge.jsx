import { useEffect, useRef } from 'react';

export default function RiskGauge({ riskScore, riskLevel, distressProbability, confidence }) {
  const canvasRef = useRef(null);

  const isAvailable = riskScore !== null && riskScore !== undefined;

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

    const targetScore = isAvailable ? Math.max(0, Math.min(100, riskScore)) : 0;
    const duration = isAvailable ? 1500 : 0;
    const startTime = performance.now();

    const getColor = (s) => {
      if (!isAvailable) return 'rgba(255,255,255,0.1)';
      if (s <= 25) return '#10b981';
      if (s <= 50) return '#f59e0b';
      if (s <= 75) return '#ef4444';
      return '#dc2626';
    };

    const draw = (timestamp) => {
      const elapsed = timestamp - startTime;
      const progress = duration > 0 ? Math.min(elapsed / duration, 1) : 1;
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
      const scoreAngle = startAngle + (endAngle - startAngle) * (isAvailable ? (currentScore / 100) : 1);
      const color = getColor(currentScore);

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, scoreAngle);
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.shadowColor = isAvailable ? color : 'transparent';
      ctx.shadowBlur = isAvailable ? 15 : 0;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Score text
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 36px Outfit, Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(isAvailable ? Math.round(currentScore) : '--', centerX, centerY - 5);

      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '12px Inter, sans-serif';
      ctx.fillText('/ 100', centerX, centerY + 22);

      if (progress < 1) requestAnimationFrame(draw);
    };

    requestAnimationFrame(draw);
  }, [riskScore, isAvailable]);

  const levelColor = isAvailable ? ({
    Low: 'risk-badge-low',
    Medium: 'risk-badge-medium',
    High: 'risk-badge-high',
    Critical: 'risk-badge-critical',
  }[riskLevel] || 'risk-badge-medium') : 'text-gray-400 bg-gray-800/50';

  const displayRiskLevel = isAvailable ? riskLevel : 'Unknown';

  return (
    <div className="glass-card p-6 flex flex-col items-center">
      <h3 className="section-title mb-2">
        ⚠️ Financial Distress Score
      </h3>
      <canvas ref={canvasRef} />
      <span className={`text-xs font-semibold px-3 py-1 rounded-full mt-1 ${levelColor}`}>
        {displayRiskLevel} Risk
      </span>
      <div className="flex gap-4 mt-3 text-xs text-gray-500">
        <span>Probability: {distressProbability !== undefined && distressProbability !== null ? (distressProbability * 100).toFixed(1) + '%' : '--'}</span>
        <span>Confidence: {confidence !== undefined && confidence !== null ? confidence + '%' : '--'}</span>
      </div>
    </div>
  );
}
