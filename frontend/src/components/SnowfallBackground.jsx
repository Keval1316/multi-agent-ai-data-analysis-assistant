import React, { useEffect, useRef } from 'react';

/**
 * Beautiful, high-performance Canvas-based snowfall particle animation.
 * Features delicate #CEAB93 snowflakes drifting smoothly from top-left to bottom-right.
 * Optimized with high-DPI scaling, organic sway, and micro-crystal shimmer.
 */
export default function SnowfallBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width = window.innerWidth;
    let height = window.innerHeight;

    const setCanvasSize = () => {
      if (!canvas) return;
      const dpr = window.devicePixelRatio || 1;
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    setCanvasSize();
    window.addEventListener('resize', setCanvasSize);

    // Subtle, light quantity of snowflakes (~25-45 flakes for clean minimalism)
    const flakeCount = Math.floor(Math.min(Math.max(width / 40, 25), 45));
    const flakes = [];

    // Curated color palette anchored on #CEAB93
    const colors = [
      'rgba(206, 171, 147, ', // #CEAB93 Primary warm caramel
      'rgba(206, 171, 147, ', // #CEAB93 Primary warm caramel
      'rgba(173, 139, 115, ', // #AD8B73 Accent medium caramel
      'rgba(227, 202, 165, ', // #E3CAA5 Light cream
    ];

    for (let i = 0; i < flakeCount; i++) {
      flakes.push({
        x: Math.random() * (width + 400) - 200,
        y: Math.random() * (height + 300) - 150,
        radius: Math.random() * 2.2 + 1.2, // Small delicate size (1.2px to 3.4px)
        opacity: Math.random() * 0.45 + 0.45, // Crisp visible opacity (0.45 to 0.90)
        speedY: Math.random() * 1.3 + 0.75, // Downward velocity
        speedX: Math.random() * 1.1 + 0.65, // Rightward drift (top-left -> bottom-right)
        swaySpeed: Math.random() * 0.018 + 0.006,
        swayOffset: Math.random() * Math.PI * 2,
        swayAmplitude: Math.random() * 0.8 + 0.25,
        colorBase: colors[i % colors.length],
        isCrystal: i % 6 === 0 // 16% micro sparkle crystals
      });
    }

    let time = 0;

    const render = () => {
      time += 1;
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < flakes.length; i++) {
        const flake = flakes[i];

        // Move diagonally from top-left to bottom-right with organic lateral swaying
        flake.y += flake.speedY;
        flake.x += flake.speedX + Math.sin(time * flake.swaySpeed + flake.swayOffset) * flake.swayAmplitude;

        // Wrap around boundaries
        if (flake.y > height + 25) {
          flake.y = -25;
          flake.x = Math.random() * (width + 250) - 250;
        }
        if (flake.x > width + 25) {
          flake.x = -25;
          flake.y = Math.random() * (height + 250) - 150;
        }

        ctx.save();
        ctx.fillStyle = `${flake.colorBase}${flake.opacity})`;
        ctx.shadowColor = 'rgba(206, 171, 147, 0.65)';
        ctx.shadowBlur = flake.radius > 2.2 ? 4 : 2;

        if (flake.isCrystal && flake.radius > 1.8) {
          // Draw delicate 4-pointed sparkle snowflake
          const r = flake.radius * 1.4;
          ctx.beginPath();
          ctx.arc(flake.x, flake.y, flake.radius * 0.6, 0, Math.PI * 2);
          ctx.fill();

          ctx.strokeStyle = `${flake.colorBase}${flake.opacity * 0.95})`;
          ctx.lineWidth = 0.9;
          ctx.beginPath();
          ctx.moveTo(flake.x - r, flake.y);
          ctx.lineTo(flake.x + r, flake.y);
          ctx.moveTo(flake.x, flake.y - r);
          ctx.lineTo(flake.x, flake.y + r);
          ctx.stroke();
        } else {
          // Draw delicate round snowflake dot
          ctx.beginPath();
          ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2, false);
          ctx.fill();
        }
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', setCanvasSize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none w-full h-full"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 1
      }}
      aria-hidden="true"
    />
  );
}
