import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Play, TrendingUp } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export default function Home() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const handleLoginSuccess = async (response) => {
    try {
      await login(response.credential);
      navigate('/play');
    } catch (err) {
      alert(`Login Failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center px-4">
      <div className="text-center max-w-2xl">
        <div className="flex items-center justify-center gap-3 mb-4">
          <TrendingUp size={44} className="text-indigo-400" />
          <h1 className="text-5xl font-black text-white px-2">InvestCraft</h1>
        </div>
        <p className="text-xl text-indigo-300 mb-2">Craft your wealth, one move at a time.</p>
        <p className="text-slate-400 mb-8 px-4">Solve Nifty 50 brand puzzles. Learn about stocks. Compete for streaks.</p>

        <div className="flex flex-col items-center gap-4">
          <button
            onClick={() => user ? navigate('/play') : null}
            className={`${user ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-slate-700/50 cursor-not-allowed opacity-80'} text-white text-lg font-bold px-10 py-4 rounded-2xl transition-all shadow-xl flex items-center gap-2`}
          >
            {user ? "Today's Puzzle →" : <><Play size={20} fill="currentColor" /> Play Now</>}
          </button>

          {!user && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-700 flex flex-col items-center gap-4">
              <div className="bg-white/5 border border-white/10 px-6 py-4 rounded-2xl backdrop-blur-sm flex flex-col items-center gap-3">
                <p className="text-indigo-200 text-sm font-medium">
                  Please <button onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })} className="text-indigo-400 font-bold hover:underline cursor-pointer bg-transparent border-none p-0">Sign In</button> to unlock the game!
                </p>
                <div className="scale-110">
                  <GoogleLogin
                    onSuccess={handleLoginSuccess}
                    onError={() => alert('Login Failed. Please try again.')}
                    theme="filled_blue"
                    shape="pill"
                    text="signin_with"
                    size="large"
                  />
                </div>
              </div>
              <p className="text-slate-500 text-xs">Login with Google to track your score & streak.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
