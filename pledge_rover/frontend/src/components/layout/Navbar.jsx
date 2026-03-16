import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, ShieldAlert, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function Navbar() {
  const location = useLocation();

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: <Activity className="w-4 h-4 mr-2" /> },
    { name: 'Contagion Feed', path: '/feed', icon: <ShieldAlert className="w-4 h-4 mr-2" /> },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full glass-card border-x-0 border-t-0 rounded-none px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-8">
        <Link to="/" className="flex items-center group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-navy-700 to-navy-900 border border-electric-cyan/30 shadow-glow group-hover:shadow-glow-lg transition-all duration-300">
            <Zap className="text-electric-cyan w-5 h-5 absolute z-10" />
            <ShieldAlert className="text-trust-blue w-6 h-6 opacity-30 group-hover:opacity-50 transition-opacity" />
          </div>
          <span className="ml-3 text-xl font-display font-bold text-white tracking-wide">
            Pledge<span className="text-electric-cyan">Rover</span>
          </span>
        </Link>
        
        <div className="hidden md:flex space-x-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={cn(
                  "flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-navy-700/50 text-electric-cyan border border-electric-cyan/20" 
                    : "text-trust-silver hover:bg-navy-700/30 hover:text-white"
                )}
              >
                {link.icon}
                {link.name}
              </Link>
            );
          })}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 bg-navy-800/80 px-4 py-1.5 rounded-full border border-trust-silver/10 cursor-help" title="Mock API Connected">
           <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_#4ade80] animate-pulse"></div>
           <span className="text-xs font-medium text-trust-silver">Council Online</span>
        </div>
        <button className="btn-accent hidden sm:block text-sm py-1.5">
          Trigger Scan
        </button>
      </div>
    </nav>
  );
}
