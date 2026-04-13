import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Play, TrendingUp, Facebook, Linkedin, Github } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export default function Home() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const handleSocialLogin = async (provider, token = 'mock_token') => {
    try {
      // In production, these would trigger their respective OAuth flows
      // For now, we stub the flow while showing the beautiful UI
      if (provider === 'google') {
          await login(token, 'google');
      } else {
          alert(`${provider} integration is coming soon! Whitelist your production ID to enable.`);
      }
      navigate('/play');
    } catch (err) {
      alert(`Login Failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#030014] relative overflow-hidden flex items-center justify-center px-4">
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 opacity-40">
        <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/20 blur-[150px] animate-pulse" />
        <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-cyan-600/20 blur-[150px] animate-pulse delay-700" />
      </div>

      <div className="text-center max-w-2xl relative z-10">
        <div className="flex items-center justify-center gap-4 mb-4 animate-in fade-in slide-in-from-bottom-5 duration-1000">
          <div className="p-3 bg-indigo-600/20 rounded-2xl border border-indigo-500/30 shadow-2xl shadow-indigo-500/20">
            <TrendingUp size={48} className="text-indigo-400" />
          </div>
          <h1 className="text-6xl font-black text-white tracking-tighter">InvestBrand</h1>
        </div>

        <p className="text-2xl text-indigo-300 font-medium mb-2 opacity-90">Craft your wealth, one move at a time.</p>
        <p className="text-slate-400 text-lg mb-12 max-w-lg mx-auto leading-relaxed">The ultimate brand intelligence challenge. Solve puzzles, decode market signals, and master the art of identification.</p>

        <div className="flex flex-col items-center gap-6">
          <button
            onClick={() => user ? navigate('/play') : null}
            className={`${user ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-slate-800/50 cursor-not-allowed border border-white/5'} text-white text-xl font-black px-12 py-5 rounded-[2rem] transition-all shadow-2xl shadow-indigo-600/40 flex items-center gap-3 transform hover:scale-105 active:scale-95`}
          >
            {user ? "Continue Journey →" : <><Play size={24} fill="currentColor" /> Play Now</>}
          </button>

          {!user && (
            <div className="mt-8 bg-white/5 backdrop-blur-2xl border border-white/10 p-8 rounded-[2.5rem] shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full max-w-md animate-in zoom-in-95 duration-500">
              <h3 className="text-white font-bold text-lg mb-6 flex items-center justify-center gap-2">
                <span className="w-8 h-[1px] bg-gradient-to-r from-transparent to-white/20"></span>
                Social Identity Access
                <span className="w-8 h-[1px] bg-gradient-to-l from-transparent to-white/20"></span>
              </h3>

              <div className="flex flex-col gap-4">
                {/* Primary: Google One-Tap */}
                <div className="w-full flex justify-center transform transition-transform hover:scale-[1.02]">
                  <GoogleLogin
                    onSuccess={(r) => handleSocialLogin('google', r.credential)}
                    onError={() => alert('Access Configuration Error')}
                    theme="filled_blue"
                    shape="pill"
                    width="320"
                    text="continue_with"
                  />
                </div>

                {/* Secondary Providers Grid */}
                <div className="grid grid-cols-3 gap-3">
                   <button onClick={() => handleSocialLogin('facebook')} className="bg-[#1877F2]/10 hover:bg-[#1877F2]/20 border border-[#1877F2]/30 p-4 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-[#1877F2]" title="Sign in with Facebook">
                      <Facebook size={24} fill="currentColor" />
                   </button>
                   <button onClick={() => handleSocialLogin('linkedin')} className="bg-[#0A66C2]/10 hover:bg-[#0A66C2]/20 border border-[#0A66C2]/30 p-4 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-[#0A66C2]" title="Sign in with LinkedIn">
                      <Linkedin size={24} fill="currentColor" />
                   </button>
                   <button onClick={() => handleSocialLogin('github')} className="bg-white/5 hover:bg-white/10 border border-white/20 p-4 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 text-white" title="Sign in with GitHub">
                      <Github size={24} fill="currentColor" />
                   </button>
                </div>
              </div>

              <p className="mt-6 text-slate-500 text-xs font-medium uppercase tracking-widest">Global Authentication Enabled</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
