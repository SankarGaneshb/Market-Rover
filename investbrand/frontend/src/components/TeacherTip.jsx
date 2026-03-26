import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Lightbulb, Sparkles, X } from 'lucide-react';

export default function TeacherTip() {
  const [tip, setTip] = useState(null);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const fetchTip = async () => {
      try {
        const res = await axios.get('/api/education/tip');
        const data = res?.data ?? {};
        if (data.tip) {
          setTip(data.tip);
        }
      } catch (err) {
        console.error('Failed to fetch teacher tip:', err);
      }
    };
    fetchTip();
  }, []);

  if (!tip || !isVisible) return null;

  return (
    <div className="relative group mb-6 animate-in fade-in slide-in-from-top-4 duration-700">
      {/* Background with high contrast for both light/dark */}
      <div className="absolute inset-0 bg-slate-900/40 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="relative bg-slate-900 border border-white/10 rounded-2xl p-4 lg:p-5 flex items-start gap-4 shadow-2xl overflow-hidden group-hover:border-indigo-400/50 transition-all">
        {/* Animated accent line */}
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-400 to-cyan-400" />
        
        <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-lg flex-shrink-0 animate-pulse">
          <Lightbulb size={20} />
        </div>
        
        <div className="flex-1 min-w-0 pr-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400">Teacher Agent Insight</span>
            <Sparkles size={10} className="text-cyan-400 animate-spin-slow" />
          </div>
          <p className="text-sm font-semibold text-white leading-relaxed italic">
            "{tip}"
          </p>
        </div>

        <button 
          onClick={() => setIsVisible(false)}
          className="p-1 hover:bg-white/10 rounded-lg text-white/40 hover:text-white transition-colors absolute top-2 right-2"
        >
          <X size={16} />
        </button>
      </div>
      
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 8s linear infinite;
        }
      `}} />
    </div>
  );
}
