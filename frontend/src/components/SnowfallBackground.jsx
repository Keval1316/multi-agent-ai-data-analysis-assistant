import React, { useEffect, useRef } from 'react';

/**
 * Beautiful, lightweight Canvas-based snowfall particle animation.
 * Medium quantity snowflakes drifting gracefully from top-left to bottom-right.
 * Theme color: #CEAB93 (warm beige/caramel tone).
 */
export default function SnowfallBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Medium quantity of snowflakes (~55 flakes for optimal balance of elegance and performance)
    const flakeCount = Math.floor(Math.min(Math.max(width / 24, 40), 75));
    const flakes = [];

    for (let i = 0; i < flakeCount; i++) {
      flakes.push({
        x: Math.random() * (width + 300) - 200,
        y: Math.random() * (height + 200) - 100,
        radius: Math.random() * 2.4 + 1.2, // Delicate small sizes (1.2px to 3.6px)
        opacity: Math.random() * 0.55 + 0.3, // Soft translucent opacities (0.3 to 0.85)
        speedY: Math.random() * 1.4 + 0.8, // Downward velocity
        speedX: Math.random() * 1.2 + 0.7, // Rightward drift (top-left -> bottom-right)
        swaySpeed: Math.random() * 0.02 + 0.008,
        swayOffset: Math.random() * Math.PI * 2,
        swayAmplitude: Math.random() * 0.8 + 0.3
      });
    }

    let time = 0;

    const render = () => {
      time += 1;
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < flakes.length; i++) {
        const flake = flakes[i];

        // Update position: diagonal drift from top-left to bottom-right with organic gentle sway
        flake.y += flake.speedY;
        flake.x += flake.speedX + Math.sin(time * flake.swaySpeed + flake.swayOffset) * flake.swayAmplitude;

        // Wrap around boundaries seamlessly
        if (flake.y > height + 20) {
          flake.y = -20;
          flake.x = Math.random() * (width + 200) - 200;
        }
        if (flake.x > width + 20) {
          flake.x = -20;
          flake.y = Math.random() * (height + 200) - 100;
        }

        // Draw delicate snowflake (#CEAB93 -> RGB: 206, 171, 147)
        ctx.beginPath();
        ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2, false);
        ctx.fillStyle = `rgba(206, 171, 147, ${flake.opacity})`;
        ctx.shadowColor = 'rgba(206, 171, 147, 0.4)';
        ctx.shadowBlur = flake.radius > 2.2 ? 3 : 1;
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none -z-10 w-full h-full"
      style={{ opacity: 0.9 }}
      aria-hidden="true"
    />
  );
}
