import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, Shield, Zap, Lock, ChevronRight, GraduationCap } from 'lucide-react';

const ICON_MAP = { BookOpen, Shield, Zap };

export default function LearningLocker() {
  const [guides, setGuides] = useState([]);
  const [selectedGuide, setSelectedGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLocker = async () => {
      try {
        const res = await axios.get('/api/education/locker');
        setGuides((res?.data ?? {}).locker || []);
      } catch (err) {
        console.error('Failed to fetch locker:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLocker();
  }, []);

  if (loading) return <div className="animate-pulse h-32 bg-white/5 rounded-2xl" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <GraduationCap className="text-indigo-400" size={24} />
        <h3 className="text-xl font-bold text-white tracking-tight italic">Learning Locker</h3>
      </div>

      {guides.length === 0 ? (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
          <Lock className="mx-auto text-white/20 mb-3" size={32} />
          <p className="text-slate-400 text-sm font-medium">Your locker is empty. Complete missions to unlock premium financial guides!</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {guides.map((guide) => {
            const Icon = ICON_MAP[guide.icon] || BookOpen;
            return (
              <div 
                key={guide.id}
                onClick={() => setSelectedGuide(guide)}
                className="group relative bg-[#1a1c2e] border border-white/10 rounded-2xl p-4 cursor-pointer hover:border-indigo-500/50 transition-all hover:translate-y-[-2px] overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Icon size={48} />
                </div>
                
                <div className="flex items-start gap-4 relative z-10">
                  <div className="p-3 rounded-xl bg-indigo-500/20 text-indigo-400">
                    <Icon size={20} />
                  </div>
                  <div className="flex-1">
                    <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400/80">{guide.category}</span>
                    <h4 className="text-white font-bold mb-1">{guide.title}</h4>
                    <p className="text-slate-400 text-xs line-clamp-2">{guide.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Guide Detail Modal (Simple Overlay) */}
      {selectedGuide && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-4 lg:p-12">
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-xl" onClick={() => setSelectedGuide(null)} />
          
          <div className="relative bg-[#0d0f1a] border border-white/10 rounded-[2rem] w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="sticky top-0 bg-[#0d0f1a] border-b border-white/10 p-6 flex justify-between items-start">
              <div>
                <span className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-1 block">{selectedGuide.category}</span>
                <h2 className="text-3xl font-black text-white">{selectedGuide.title}</h2>
              </div>
              <button 
                onClick={() => setSelectedGuide(null)}
                className="p-2 hover:bg-white/5 rounded-full text-slate-500 hover:text-white transition-colors"
              >
                <ChevronRight size={24} className="rotate-90" />
              </button>
            </div>
            
            <div className="p-8 prose prose-invert max-w-none">
              <div className="text-slate-300 leading-relaxed space-y-4" dangerouslySetInnerHTML={{ __html: selectedGuide.content.replace(/\n/g, '<br/>') }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
