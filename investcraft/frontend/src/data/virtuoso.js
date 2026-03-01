export const VIRTUOSO_LEVELS = [
    {
        name: 'Junior Virtuoso',
        minDays: 0,
        image: '/badges/junior.png',
        icon: 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z',
        color: 'text-indigo-200',
        accent: '#818cf8', // indigo-400
        glow: 'shadow-indigo-500/40',
        bg: 'bg-gradient-to-br from-[#0c0e1a] via-[#1e293b] to-[#0c0e1a]'
    },
    {
        name: 'Copper Virtuoso',
        minDays: 3,
        image: '/badges/copper.png',
        icon: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
        color: 'text-[#ff7043]',
        accent: '#ff7043', // Vibrant Copper
        glow: 'shadow-orange-600/50',
        bg: 'bg-gradient-to-br from-[#1a0f0c] via-[#452721] to-[#1a0f0c]'
    },
    {
        name: 'Bronze Virtuoso',
        minDays: 7,
        image: '/badges/bronze.png',
        icon: 'M12 15l-2 5h4l-2-5zm0-13C7.03 2 3 6.03 3 11c0 2.22.81 4.25 2.16 5.81L12 22l6.84-5.19c1.35-1.56 2.16-3.59 2.16-5.81 0-4.97-4.03-9-9-9z',
        color: 'text-[#cd7f32]',
        accent: '#cd7f32', // Metallic Bronze
        glow: 'shadow-amber-700/50',
        bg: 'bg-gradient-to-br from-[#1a140c] via-[#3a2a16] to-[#1a140c]'
    },
    {
        name: 'Silver Virtuoso',
        minDays: 14,
        image: '/badges/silver.png',
        icon: 'M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z',
        color: 'text-slate-50',
        accent: '#ffffff', // Pure Metallic Shine
        glow: 'shadow-slate-200/60',
        bg: 'bg-gradient-to-br from-[#0c161a] via-[#475569] to-[#0c161a]'
    },
    {
        name: 'Gold Virtuoso',
        minDays: 30,
        image: '/badges/gold.png',
        icon: 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z',
        color: 'text-[#ffd700]',
        accent: '#ffd700', // Bright Gold
        glow: 'shadow-yellow-500/50',
        bg: 'bg-gradient-to-br from-[#1e1b0c] via-[#715911] to-[#1e1b0c]'
    },
    {
        name: 'Platinum Virtuoso',
        minDays: 60,
        image: '/badges/platinum.png',
        icon: 'M12 21l-8.22-4.93C3.3 15.77 3 15.17 3 14.53V5.47c0-.64.3-1.24.78-1.54L12 3l8.22 4.93c.48.3.78.9.78 1.54v9.06c0 .64-.3 1.24-.78 1.54L12 21z',
        color: 'text-[#00ff9f]',
        accent: '#00ff9f', // Electric Platinum/Green
        glow: 'shadow-emerald-400/50',
        bg: 'bg-gradient-to-br from-[#0c1a14] via-[#103d2b] to-[#0c1a14]'
    },
    {
        name: 'Diamond Virtuoso',
        minDays: 100,
        image: '/badges/diamond.png',
        icon: 'M12 2l10 10-10 10L2 12z',
        color: 'text-[#00d4ff]',
        accent: '#00d4ff', // Cyan Diamond
        glow: 'shadow-blue-500/60',
        bg: 'bg-gradient-to-br from-[#0c161a] via-[#11384a] to-[#0c161a]'
    }
];

export const getVirtuosoLevel = (streak) => {
    return [...VIRTUOSO_LEVELS].reverse().find(l => streak >= l.minDays);
};

export const getNextVirtuosoLevel = (streak) => {
    return VIRTUOSO_LEVELS.find(l => streak < l.minDays);
};
