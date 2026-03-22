import React from 'react';
import { X, ExternalLink, BookOpen } from 'lucide-react';

export default function ExplainerModal({ isOpen, onClose, data }) {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 font-sans">
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose}></div>
      
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col animate-in zoom-in-95 duration-200">
        
        <div className="flex items-center justify-between p-5 border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-3 text-indigo-600">
            <BookOpen size={24} />
            <h2 className="text-xl font-black text-slate-800">{data.title}</h2>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors focus:outline-none">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 md:p-8 overflow-y-auto">
          <h3 className="text-lg font-bold text-slate-800 mb-6 leading-snug">{data.headline}</h3>

          <div className="mb-6">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-slate-400 mb-3">Why it matters</h4>
            <ul className="space-y-3">
              {data.whyItMatters?.map((point, i) => (
                <li key={i} className="flex items-start gap-2.5 text-slate-600 text-sm">
                  <span className="text-indigo-400 font-bold mt-0.5">•</span>
                  <span className="leading-relaxed">{point}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mb-7 p-5 bg-slate-50 rounded-xl border border-slate-100 shadow-inner">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-slate-400 mb-3">Real-world example</h4>
            <p className="text-sm text-slate-700 leading-relaxed">{data.example}</p>
          </div>

          <div className="mb-6">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-slate-400 mb-3">Action takeaway</h4>
            <div className="border-l-4 border-indigo-500 pl-4 py-1.5 bg-indigo-50/30 rounded-r-lg">
              <p className="text-sm font-medium text-slate-800 italic leading-relaxed">{data.takeaway}</p>
            </div>
          </div>

          {data.resources && data.resources.length > 0 && (
            <div className="pt-5 mt-2 border-t border-slate-100">
              <h4 className="text-xs font-extrabold uppercase tracking-widest text-slate-400 mb-4">External resources</h4>
              <div className="flex flex-col gap-3">
                {data.resources.map((res, i) => (
                  <a key={i} href={res.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 w-fit group transition-colors">
                    <ExternalLink size={14} className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    {res.label}
                  </a>
                ))}
              </div>
            </div>
          )}
          
          <p className="text-[10px] text-slate-400 mt-8 uppercase tracking-widest text-center border-t border-slate-100 pt-4">
            Educational material - Not investment advice
          </p>
        </div>
      </div>
    </div>
  );
}
