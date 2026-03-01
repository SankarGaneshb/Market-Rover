import React from 'react';

export default function GlitterBadge({ icon, name, levelConfig, size = 'large' }) {
    const isSilver = name.toLowerCase().includes('silver');
    const isSmall = size === 'small';

    return (
        <div className="relative group cursor-default">
            {/* 1. Dramatic Backlighting (Outer Aura) */}
            <div
                className="absolute inset-[-60%] rounded-full opacity-30 blur-[120px] animate-pulse pointer-events-none z-0 transition-opacity group-hover:opacity-50"
                style={{ backgroundColor: levelConfig.accent }}
            />

            <div className={`relative ${levelConfig.bg} ${isSmall ? 'px-4 py-4 rounded-2xl min-w-0 w-24 h-24' : 'px-10 py-14 rounded-[3.5rem] min-w-[300px]'} border-t-2 border-l-2 border-white/40 border-b-2 border-r-2 border-black/80 flex flex-col items-center justify-center gap-2 shadow-[20px_20px_50px_-10px_rgba(0,0,0,1),inset_0_2px_4px_rgba(255,255,255,0.3)] backdrop-blur-[100px] overflow-hidden transform transition-all duration-700 hover:shadow-[40px_40px_100px_-20px_rgba(0,0,0,1),inset_0_2px_4px_rgba(255,255,255,0.4)] ring-1 ${isSilver ? 'ring-white/50' : 'ring-white/20'}`}>

                {/* 2. Concentrated Spotlight (INNER GLOW BEHIND IMAGE) */}
                <div
                    className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 ${isSmall ? 'w-20 h-20' : 'w-56 h-56'} rounded-full blur-3xl mix-blend-screen pointer-events-none animate-pulse ${isSilver ? 'opacity-90' : 'opacity-70'}`}
                    style={{ background: `radial-gradient(circle, ${isSilver ? '#fff' : levelConfig.accent}, transparent 75%)` }}
                />

                {/* 3. High-Contrast Shimmer Sweep */}
                <div className="absolute inset-0 w-full h-full pointer-events-none z-40">
                    <div className="glitter-shimmer absolute top-0 left-[-100%] w-[120%] h-full skew-x-[-35deg] bg-gradient-to-r from-transparent via-white/80 to-transparent opacity-95" />
                    {isSilver && (
                        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent animate-silver-flow" />
                    )}
                </div>

                {/* 4. Hyper Sparkles */}
                <div className="absolute inset-0 z-50 pointer-events-none">
                    {[...Array(20)].map((_, i) => (
                        <div
                            key={i}
                            className={`absolute w-1.5 h-1.5 bg-white rounded-full animate-twinkle shadow-[0_0_20px_white] ${isSilver ? 'brightness-150' : ''}`}
                            style={{
                                top: `${Math.random() * 100}%`,
                                left: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 5}s`,
                                animationDuration: `${0.8 + Math.random() * 1.5}s`
                            }}
                        />
                    ))}
                </div>

                <div className={`relative ${isSmall ? 'w-16 h-16' : 'w-48 h-48'} flex items-center justify-center z-30 ${isSmall ? 'mb-0' : 'mb-2'}`}>
                    {levelConfig.image ? (
                        <img
                            src={levelConfig.image}
                            alt={name}
                            className={`w-full h-full object-contain relative z-10 drop-shadow-[0_15px_30px_rgba(0,0,0,0.8)] ${isSilver ? 'animate-silver-vibrate' : ''}`}
                            style={{
                                filter: `drop-shadow(0 0 ${isSmall ? '15px' : '40px'} ${isSilver ? '#fff' : levelConfig.accent}aa)`
                            }}
                        />
                    ) : (
                        <div className={`${isSmall ? 'w-10 h-10' : 'w-24 h-24'} ${levelConfig.color} relative z-10 drop-shadow-[0_20px_40px_rgba(0,0,0,0.7)]`}>
                            <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                                <path d={levelConfig.icon || "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"} />
                            </svg>
                        </div>
                    )}
                </div>

                {!isSmall && (
                    <div className="flex flex-col items-center text-center z-30 relative">
                        <span className="text-[14px] font-black uppercase tracking-[0.6em] text-white/50 mb-3 block">
                            {levelConfig.minDays === 0 ? 'LEGACY RANK' : 'VIRTUOSO ELITE'}
                        </span>
                        <span className={`text-6xl font-black italic tracking-tighter ${levelConfig.color} filter drop-shadow-[0_6px_10px_rgba(0,0,0,0.9)]`}>
                            {name.split(' ')[0]}
                        </span>
                        <div
                            className="h-2 w-32 rounded-full mt-6 shadow-[0_0_30px_rgba(255,255,255,0.4)] animate-pulse"
                            style={{ backgroundColor: isSilver ? '#fff' : levelConfig.accent }}
                        />
                    </div>
                )}

                <style dangerouslySetInnerHTML={{
                    __html: `
          .glitter-shimmer {
            animation: broad-sweep 3s infinite cubic-bezier(0.4, 0, 0.2, 1);
          }
          @keyframes broad-sweep {
            0% { left: -100%; opacity: 0; }
            10% { opacity: 0; }
            30% { opacity: 0.9; }
            70% { opacity: 0.9; }
            90% { opacity: 0; }
            100% { left: 200%; opacity: 0; }
          }
          @keyframes twinkle {
            0%, 100% { opacity: 0; transform: scale(0.3); }
            50% { opacity: 1; transform: scale(1.5) rotate(45deg); }
          }
          .animate-twinkle {
            animation: twinkle infinite ease-in-out;
          }
          @keyframes silver-vibrate {
            0%, 100% { transform: scale(1) translateY(0); }
            50% { transform: scale(1.05) translateY(-5px); }
          }
          .animate-silver-vibrate {
            animation: silver-vibrate 2s infinite ease-in-out;
          }
          @keyframes silver-flow {
            0% { transform: translateX(-100%) skewX(-30deg); }
            100% { transform: translateX(200%) skewX(-30deg); }
          }
          .animate-silver-flow {
            animation: silver-flow 1.5s infinite linear;
          }
        `}} />
            </div>
        </div>
    );
}
