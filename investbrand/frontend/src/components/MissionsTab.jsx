import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Target, Award, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ExplainerModal from './ExplainerModal';
import { EXPLAINERS } from '../data/explainers';

const MISSION_DEFS = {
  first_steps: {
    title: 'First Steps',
    desc: 'Complete your first 5 votes (any combination)',
    target: 5,
    reward: 'Introduction to investment basics guide'
  },
  sector_explorer: {
    title: 'Sector Explorer',
    desc: 'Vote across 3 different sectors',
    target: 3,
    reward: 'Sector comparison chart and defensively characteristics'
  }
};

export default function MissionsTab() {
  const { user } = useAuth();
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalData, setModalData] = useState(null);

  useEffect(() => {
    const fetchMissions = async () => {
      try {
        const res = await axios.get('/api/missions');
        setMissions(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (user) {
      fetchMissions();
    } else {
      setLoading(false);
    }
  }, [user]);

  const getMissionProgress = (missionId) => {
    const m = missions.find(x => x.mission_id === missionId);
    return m ? { progress: m.progress, isCompleted: m.is_completed } : { progress: 0, isCompleted: false };
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading missions...</div>;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#f8fafc] w-full">
      <div className="max-w-5xl mx-auto p-6 md:p-10 font-sans">
        <div className="mb-8 text-center md:text-left">
          <h1 className="text-3xl font-black text-slate-800 flex items-center justify-center md:justify-start gap-3">
            <Target className="text-indigo-600" size={32} />
            Financial Literacy Missions
          </h1>
          <p className="text-slate-500 mt-2 font-medium">Complete missions through your daily voting to earn badges and unlock exclusive investing knowledge.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {(() => {
            const displayMissions = [];
            
            // 1. Static Base Missions
            Object.entries(MISSION_DEFS).forEach(([id, def]) => {
              const dbEntry = missions.find(m => m.mission_id === id);
              displayMissions.push({
                id,
                title: def.title,
                desc: def.desc,
                target: def.target,
                reward: def.reward,
                progress: dbEntry ? dbEntry.progress : 0,
                isCompleted: dbEntry ? dbEntry.is_completed : false,
                isDynamic: false
              });
            });

            // 2. Dynamic Gamemaster Missions
            missions.forEach(m => {
              if (!MISSION_DEFS[m.mission_id] && m.mission_def) {
                displayMissions.push({
                  id: m.mission_id,
                  title: m.mission_def.title || 'Special Mission',
                  desc: m.mission_def.description || m.mission_def.desc,
                  target: m.mission_def.target,
                  reward: m.mission_def.reward,
                  progress: m.progress,
                  isCompleted: m.is_completed,
                  isDynamic: true
                });
              }
            });

            return displayMissions.map((def) => {
              const { id, progress, isCompleted, percent = Math.min(100, Math.round((progress / def.target) * 100)) } = def;

              return (
              <div key={id} className={`p-6 rounded-2xl border transition-all shadow-sm ${isCompleted ? 'bg-indigo-50 border-indigo-200' : 'bg-white border-slate-200'}`}>
                <div className="flex justify-between items-start mb-5">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl flex items-center justify-center shadow-sm ${isCompleted ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-400'}`}>
                      <Award size={28} />
                    </div>
                    <div>
                      <h3 className={`font-black text-xl leading-tight ${isCompleted ? 'text-indigo-900' : 'text-slate-800'}`}>{def.title}</h3>
                      <p className="text-sm font-medium text-slate-500 mt-1">{def.desc}</p>
                    </div>
                  </div>
                  {isCompleted && <CheckCircle className="text-indigo-500 shrink-0" size={28} />}
                </div>

                <div className="mb-5">
                  <div className="flex justify-between text-xs font-bold mb-2 uppercase tracking-widest">
                    <span className="text-slate-400">Progress</span>
                    <span className={isCompleted ? 'text-indigo-600' : 'text-slate-600'}>{progress} / {def.target}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
                    <div 
                      className={`h-full rounded-full transition-all duration-700 ease-out ${isCompleted ? 'bg-indigo-500' : 'bg-blue-400'}`}
                      style={{ width: `${percent}%` }}
                    ></div>
                  </div>
                </div>

                {isCompleted ? (
                   <div className="mt-4 pt-4 border-t border-indigo-200/50">
                     <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Reward Unlocked</span>
                     <p 
                       onClick={() => def.isDynamic ? null : setModalData(EXPLAINERS[id])} 
                       className={`text-sm font-semibold text-indigo-800 mt-1 flex items-center gap-1 ${def.isDynamic ? 'cursor-default' : 'cursor-pointer hover:underline'}`}
                     >
                       {def.reward} {!def.isDynamic && <span>&rarr;</span>}
                     </p>
                   </div>
                ) : (
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Reward Preview</span>
                    <p className="text-[13px] font-medium text-slate-400 mt-1 flex items-center gap-1">
                      {def.reward}
                    </p>
                  </div>
                )}
              </div>
            );
           });
          })()}
        </div>
      </div>
      <ExplainerModal isOpen={!!modalData} onClose={() => setModalData(null)} data={modalData} />
    </div>
  );
}
