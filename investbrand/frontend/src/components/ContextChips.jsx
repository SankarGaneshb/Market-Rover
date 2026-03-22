import React from 'react';

const ContextChips = ({ chips }) => {
  if (!chips || chips.length === 0) return null;

  const getColorClass = (type) => {
    switch(type) {
      case 'positive': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'risk': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'info':
      default: return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  return (
    <div className="flex flex-wrap gap-2 mt-3 animate-in fade-in duration-300">
      {chips.map((chip, idx) => (
        <div 
          key={idx} 
          className={`px-3 py-1.5 rounded-md text-[11px] font-semibold border shadow-sm ${getColorClass(chip.type)}`}
        >
          {chip.text}
        </div>
      ))}
    </div>
  );
};

export default ContextChips;
