import React from 'react';

export default function AmbientBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#090a0d]">
      {/* Drifting Ambient Soft Blobs */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-amber-600/10 rounded-full blur-[140px] animate-blob-1 pointer-events-none" />
      <div className="absolute top-1/3 -right-40 w-[30rem] h-[30rem] bg-emerald-600/10 rounded-full blur-[160px] animate-blob-2 pointer-events-none" />
      <div className="absolute -bottom-40 left-1/4 w-[35rem] h-[35rem] bg-zinc-800/20 rounded-full blur-[180px] animate-blob-1 pointer-events-none" />

      {/* Subtle Noise / Grid Texture */}
      <div 
        className="absolute inset-0 opacity-[0.025] pointer-events-none" 
        style={{
          backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.4) 1px, transparent 1px)`,
          backgroundSize: '24px 24px'
        }}
      />
    </div>
  );
}
