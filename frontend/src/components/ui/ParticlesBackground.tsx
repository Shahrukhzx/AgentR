'use client';

import { useEffect, useRef } from 'react';

export function ParticlesBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const neuronCount = 100;

    const neurons: Array<{
      x: number;
      y: number;
      radius: number;
      vx: number;
      vy: number;
      opacity: number;
    }> = [];

    for (let i = 0; i < neuronCount; i++) {
      neurons.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: 1 + Math.random() * 4,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        opacity: 0.6 + Math.random() * 0.4,
      });
    }

    function drawConnection(n1: typeof neurons[0], n2: typeof neurons[0]) {
      const dx = n1.x - n2.x;
      const dy = n1.y - n2.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      const maxDist = 120;
      if (dist < maxDist) {
         if (!ctx) return;

        const alpha = 1 - dist / maxDist;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(0, 255, 200, ${alpha * 0.4})`;
        ctx.lineWidth = alpha * 1.5;
        ctx.moveTo(n1.x, n1.y);
        ctx.lineTo(n2.x, n2.y);
        ctx.stroke();
      }
    }

    function animate() {
      if (!canvas || !ctx) return; // Prevents errors if canvas/context are null
      ctx.fillStyle = 'rgba(10, 10, 20, 0.3)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      neurons.forEach((n1, i) => {
        n1.x += n1.vx;
        n1.y += n1.vy;

        // Wrap around edges
        if (n1.x < 0) n1.x = canvas.width;
        if (n1.x > canvas.width) n1.x = 0;
        if (n1.y < 0) n1.y = canvas.height;
        if (n1.y > canvas.height) n1.y = 0;

        // Draw neuron (glowing core)
        const gradient = ctx.createRadialGradient(
          n1.x,
          n1.y,
          0,
          n1.x,
          n1.y,
          n1.radius * 6
        );
        gradient.addColorStop(0, `rgba(0, 255, 200, ${n1.opacity})`);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.beginPath();
        ctx.fillStyle = gradient;
        ctx.arc(n1.x, n1.y, n1.radius, 0, Math.PI * 2);
        ctx.fill();

        // Connect to nearby neurons
        for (let j = i + 1; j < neurons.length; j++) {
          drawConnection(n1, neurons[j]);
        }
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 bg-black"
    />
  );
}
