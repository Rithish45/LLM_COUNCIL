import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function SpatialGlassPanel({
  children,
  elevation = 'standard',
  interactive = true,
  glow = 'none',
  className = '',
  onClick
}) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const [tilt, setTilt] = useState({ rotateX: 0, rotateY: 0 });

  const handleMouseMove = (e) => {
    if (!interactive) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setMousePos({ x, y });

    // Subtle 3D tilt calculation (max 3 degrees)
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateY = ((x - centerX) / centerX) * 2.5;
    const rotateX = ((centerY - y) / centerY) * 2.5;
    setTilt({ rotateX, rotateY });
  };

  const handleMouseEnter = () => {
    if (!interactive) return;
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    if (!interactive) return;
    setIsHovered(false);
    setTilt({ rotateX: 0, rotateY: 0 });
  };

  // Base styles based on elevation
  let baseClass = "relative overflow-hidden rounded-2xl transition-colors duration-300 ";
  if (elevation === 'flat') {
    baseClass += "bg-zinc-900/40 backdrop-blur-md border border-white/5 ";
  } else if (elevation === 'elevated') {
    baseClass += "spatial-glass-elevated ";
  } else if (elevation === 'floating') {
    baseClass += "spatial-glass-elevated shadow-2xl border-white/20 ";
  } else {
    baseClass += "spatial-glass ";
  }

  // Optional glow accents
  let glowStyle = "";
  if (glow === 'amber') {
    glowStyle = "shadow-[0_0_25px_rgba(245,158,11,0.15)] border-amber-500/30 ";
  } else if (glow === 'emerald') {
    glowStyle = "shadow-[0_0_25px_rgba(16,185,129,0.15)] border-emerald-500/30 ";
  } else if (glow === 'rose') {
    glowStyle = "shadow-[0_0_25px_rgba(244,63,94,0.15)] border-rose-500/30 ";
  }

  return (
    <motion.div
      className={`${baseClass} ${glowStyle} ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ transformStyle: 'preserve-3d' }}
      animate={{
        rotateX: interactive && isHovered ? tilt.rotateX : 0,
        rotateY: interactive && isHovered ? tilt.rotateY : 0,
        scale: interactive && isHovered ? 1.008 : 1
      }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 22
      }}
    >
      {/* Specular Radial Cursor Highlight */}
      {interactive && isHovered && (
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300 opacity-100"
          style={{
            background: `radial-gradient(550px circle at ${mousePos.x}px ${mousePos.y}px, rgba(255, 255, 255, 0.08), transparent 45%)`
          }}
        />
      )}

      {/* Hairline subtle border shine on hover */}
      {interactive && isHovered && (
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl border border-white/20 transition-opacity duration-300"
        />
      )}

      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
