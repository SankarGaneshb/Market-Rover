import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { Trophy, Play, User, LogOut, TrendingUp, Calendar, Target, HelpCircle, Menu, X } from 'lucide-react';
import OnboardingModal from './OnboardingModal';

export default function Navbar() {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (!hasSeenOnboarding) {
      // Auto-show for first time users
      setShowOnboarding(true);
      localStorage.setItem('hasSeenOnboarding', 'true');
    }
  }, []);

  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between sticky top-0 z-[150]">
      <div className="flex items-center gap-3 md:gap-8">
        {/* Mobile Menu Toggle */}
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="md:hidden p-2.5 -ml-2 text-slate-400 hover:text-white transition-colors"
          aria-label="Toggle Menu"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <Link to="/" className="flex items-center gap-2 text-indigo-400 font-bold text-xl transition-transform active:scale-95">
          <TrendingUp size={24} />
          <span>InvestBrand</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-6">
          <Link to="/play" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"><Play size={14} />Play</Link>
          <Link to="/leaderboard" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"><Trophy size={14} />Leaderboard</Link>
          <Link to="/vote" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"><Calendar size={14} />Vote</Link>
          {user && (
            <Link to="/missions" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"><Target size={14} />Missions</Link>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {/* Help Button */}
        <button 
          onClick={() => setShowOnboarding(true)}
          className="p-2.5 sm:p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-all group relative"
          title="How to Play & AI Agents"
        >
          <HelpCircle size={22} className="sm:hidden" />
          <HelpCircle size={20} className="hidden sm:block" />
          <span className="absolute -bottom-10 right-0 bg-slate-800 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Help & Agents</span>
        </button>

        {user ? (
          <div className="flex items-center gap-3 sm:gap-4 border-l border-slate-800 pl-3 sm:pl-4 ml-1">
            <Link to="/profile" className="flex items-center gap-2 text-slate-300 hover:text-white font-medium transition-transform active:scale-95">
              <div className="w-9 h-9 sm:w-8 sm:h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center overflow-hidden">
                {user.avatar ? <img src={user.avatar} alt="" className="w-full h-full object-cover" /> : <User size={18} className="sm:hidden" /> || <User size={16} className="hidden sm:block" />}
              </div>
              <span className="hidden sm:inline">{user.name}</span>
            </Link>
            <button 
              onClick={logout} 
              className="p-2.5 sm:p-2 text-slate-500 hover:text-red-400 transition-colors" 
              title="Logout"
            >
              <LogOut size={22} className="sm:hidden" />
              <LogOut size={18} className="hidden sm:block" />
            </button>
          </div>
        ) : (
          <div className="pt-0.5">
            <GoogleLogin
              onSuccess={async (r) => {
                try {
                  await login(r.credential);
                  navigate('/play');
                } catch (err) {
                  alert(`Login Failed: ${err.message}`);
                }
              }}
              onError={() => alert('Google Script Loading Failed')}
              shape="pill"
              text="signin"
              size="medium"
              theme="filled_blue"
            />
          </div>
        )}
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 top-[65px] bg-slate-950/95 backdrop-blur-md z-[200] md:hidden animate-in fade-in slide-in-from-top duration-300">
          <div className="p-6 flex flex-col gap-4">
            <Link 
              to="/play" 
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-xl text-slate-200 hover:text-white flex items-center gap-4 p-4 bg-slate-900/50 rounded-2xl transition-all active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-indigo-500/20 rounded-xl flex items-center justify-center text-indigo-400">
                <Play size={20} />
              </div>
              Play Brand Recall
            </Link>
            <Link 
              to="/leaderboard" 
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-xl text-slate-200 hover:text-white flex items-center gap-4 p-4 bg-slate-900/50 rounded-2xl transition-all active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-amber-500/20 rounded-xl flex items-center justify-center text-amber-400">
                <Trophy size={20} />
              </div>
              Leaderboard
            </Link>
            <Link 
              to="/vote" 
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-xl text-slate-200 hover:text-white flex items-center gap-4 p-4 bg-slate-900/50 rounded-2xl transition-all active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-400">
                <Calendar size={20} />
              </div>
              Vote Next Brand
            </Link>
            {user && (
              <Link 
                to="/missions" 
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-xl text-slate-200 hover:text-white flex items-center gap-4 p-4 bg-slate-900/50 rounded-2xl transition-all active:scale-[0.98]"
              >
                <div className="w-10 h-10 bg-pink-500/20 rounded-xl flex items-center justify-center text-pink-400">
                  <Target size={20} />
                </div>
                Active Missions
              </Link>
            )}
          </div>
          
          <div className="absolute bottom-10 left-0 right-0 px-10">
            <p className="text-slate-500 text-sm text-center font-medium">
              Empower your investing journey with <span className="text-indigo-400">InvestBrand</span>
            </p>
          </div>
        </div>
      )}

      <OnboardingModal isOpen={showOnboarding} onClose={() => setShowOnboarding(false)} />
    </nav>
  );
}
