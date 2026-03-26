import React, { useState } from 'react';
import { X, ChevronRight, ChevronLeft, Brain, GraduationCap, ShieldCheck, LifeBuoy, Zap, Flame, Target } from 'lucide-react';


const AGENTS = [
  {
    name: "Adaptive Gamemaster",
    role: "Challenge Orchestrator",
    icon: <Zap className="text-yellow-400" size={32} />,
    description: "Watches your behavior and generates dynamic daily missions. If you only bet on one sector, expect a challenge to diversify!",
    tip: "Complete missions to earn massive XP multipliers."
  },
  {
    name: "Contextual Teacher",
    role: "Personal Educator",
    icon: <GraduationCap className="text-indigo-400" size={32} />,
    description: "Provides 'Did you know?' insights tailored specifically to your experience level after every puzzle solve.",
    tip: "Insights adapt to your history—beginner to advanced."
  },
  {
    name: "Quality Control",
    role: "System Auditor",
    icon: <ShieldCheck className="text-green-400" size={32} />,
    description: "An autonomous moderator that scans your feedback for blurry logos or errors and fixes the game assets overnight.",
    tip: "Use the report button; the QC agent is always listening."
  },
  {
    name: "Ops Support",
    role: "AI SRE",
    icon: <LifeBuoy className="text-red-400" size={32} />,
    description: "Our 'Guardian' agent that analyzes backend errors in real-time to prevent game crashes.",
    tip: "If something breaks, Ops is already working on the fix."
  }
];

export default function OnboardingModal({ isOpen, onClose }) {
  const [step, setStep] = useState(0);

  if (!isOpen) return null;

  const totalSteps = AGENTS.length + 2;


  const next = () => setStep(s => Math.min(s + 1, totalSteps - 1));
  const prev = () => setStep(s => Math.max(s - 0, 0));

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md" onClick={onClose}></div>
      
      <div className="relative bg-slate-900 border border-slate-700 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="p-6 pb-0 flex justify-between items-center">
          <div className="flex items-center gap-2 text-indigo-400 font-bold uppercase tracking-widest text-xs">
            <Brain size={16} />
            <span>AI Intelligence Mesh</span>
          </div>
          <button onClick={onClose} className="p-1 text-slate-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-8 flex-1 min-h-[340px] flex flex-col justify-center text-center">

          {step === 0 ? (
            <div className="animate-in slide-in-from-bottom-2 duration-500">
              <div className="w-20 h-20 bg-indigo-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-indigo-500/30">
                <Brain className="text-indigo-400" size={40} />
              </div>
              <h2 className="text-2xl font-black text-white mb-3">Welcome to InvestBrand</h2>
              <p className="text-slate-400 leading-relaxed mb-6">
                You're entering a gamified financial ecosystem driven by an <strong>Agentic AI Framework</strong>.
              </p>
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700 inline-block">
                <p className="text-xs text-slate-300 font-medium italic">Meet the 4 agents working in the background to evolve your gameplay experience.</p>
              </div>
            </div>
          ) : step === totalSteps - 1 ? (
             <div key="growth-engine" className="animate-in slide-in-from-right-4 duration-300">
                <div className="flex justify-center gap-4 mb-6">
                  <div className="w-14 h-14 bg-orange-500/20 rounded-2xl flex items-center justify-center border border-orange-500/30">
                    <Flame className="text-orange-400" size={28} />
                  </div>
                  <div className="w-14 h-14 bg-emerald-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/30">
                    <Target className="text-emerald-400" size={28} />
                  </div>
                </div>
                <h3 className="text-sm font-black text-cyan-400 uppercase tracking-widest mb-1">Growth Engine</h3>
                <h2 className="text-2xl font-bold text-white mb-4">Mastery vs. Missions</h2>
                <div className="text-slate-400 text-sm leading-relaxed mb-6 space-y-3 text-left bg-slate-800/30 p-4 rounded-2xl border border-slate-700/50">
                  <p>🔹 <strong>Mastery Path:</strong> Build consistency with <strong>Streaks</strong> to reach higher Virtuoso Ranks.</p>
                  <p>🔹 <strong>Mission Accomplishments:</strong> Complete <strong>Voting</strong> challenges to reveal hidden market insights and badges.</p>
                </div>
                <p className="text-xs text-slate-500 font-medium italic">Master both to become a financial elite.</p>
             </div>
          ) : (
            <div key={step} className="animate-in slide-in-from-right-4 duration-300">
              <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-slate-700">
                {AGENTS[step - 1].icon}
              </div>
              <h3 className="text-sm font-black text-indigo-400 uppercase tracking-widest mb-1">{AGENTS[step - 1].role}</h3>
              <h2 className="text-2xl font-bold text-white mb-4">{AGENTS[step - 1].name}</h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-6 px-4">
                {AGENTS[step - 1].description}
              </p>
              <div className="flex items-center gap-2 justify-center text-xs bg-indigo-500/10 text-indigo-300 py-2 px-3 rounded-full border border-indigo-500/20 mx-auto w-fit">
                <Zap size={12} />
                <span><strong>Pro Tip:</strong> {AGENTS[step - 1].tip}</span>
              </div>
            </div>
          )}
        </div>


        {/* Footer / Navigation */}
        <div className="p-6 bg-slate-950/50 border-t border-slate-800 flex items-center justify-between">
          <div className="flex gap-1.5">
            {[...Array(totalSteps)].map((_, i) => (
              <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === step ? 'w-6 bg-indigo-500' : 'w-1.5 bg-slate-700'}`} />
            ))}
          </div>

          <div className="flex gap-3">
            {step > 0 && (
              <button 
                onClick={() => setStep(s => s - 1)}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                aria-label="Previous"
              >
                <ChevronLeft size={24} />
              </button>
            )}
            
            {step < totalSteps - 1 ? (
              <button 
                onClick={next}
                className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 pr-4 rounded-xl flex items-center gap-1 font-bold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-indigo-500/20"
              >
                <ChevronRight size={24} />
                <span>Next</span>
              </button>
            ) : (
              <button 
                onClick={onClose}
                className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded-xl font-bold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-green-500/20"
              >
                Get Started
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
