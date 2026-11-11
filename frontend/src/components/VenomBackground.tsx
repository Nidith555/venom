import React, { useEffect, useRef } from 'react';

export const VenomBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);
    let frame = 0;

    interface Node {
      x: number;
      y: number;
      vx: number;
      vy: number;
      r: number;
      pulse: number;
    }

    let nodes: Node[] = [];

    const handleResize = () => {
      if (!canvas) return;
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
      initNodes();
    };

    const initNodes = () => {
      nodes = [];
      const count = Math.floor((W * H) / 22000);
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * W,
          y: Math.random() * H,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          r: Math.random() * 1.5 + 0.5,
          pulse: Math.random() * Math.PI * 2,
        });
      }
    };

    initNodes();
    window.addEventListener('resize', handleResize);

    const render = () => {
      ctx.clearRect(0, 0, W, H);
      frame++;

      // 1. Organic tendrils radiating from edges into center
      ctx.save();
      for (let i = 0; i < 5; i++) {
        const t = frame * 0.005 + (i * Math.PI * 2) / 5;
        const x = W / 2 + Math.cos(t) * W * 0.55;
        const y = H / 2 + Math.sin(t) * H * 0.55;
        const grad = ctx.createRadialGradient(
          W / 2,
          H / 2,
          0,
          W / 2,
          H / 2,
          Math.max(W, H) * 0.6
        );
        grad.addColorStop(0, 'rgba(244, 244, 246, 0)');
        grad.addColorStop(0.5, 'rgba(244, 244, 246, 0.015)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(W / 2, H / 2);
        ctx.quadraticCurveTo(
          W / 2 + Math.cos(t + 0.4) * W * 0.25,
          H / 2 + Math.sin(t + 0.4) * H * 0.25,
          x,
          y
        );
        ctx.stroke();
      }
      ctx.restore();

      // 2. Nodes update & drawing
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        n.pulse += 0.02;

        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;

        const alpha = (Math.sin(n.pulse) * 0.5 + 0.5) * 0.35 + 0.05;
        ctx.fillStyle = `rgba(244, 244, 246, ${alpha})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. Spider web interconnects
      const maxDist = 130;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < maxDist) {
            const alpha = (1 - d / maxDist) * 0.12;
            ctx.strokeStyle = `rgba(244, 244, 246, ${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ background: '#000000' }}
    />
  );
};
