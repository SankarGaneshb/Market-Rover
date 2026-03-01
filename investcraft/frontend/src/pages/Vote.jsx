import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { CheckCircle, BarChart3, Navigation, Building2, Store } from 'lucide-react';
import { NIFTY50_BRANDS } from '../data/brands';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export default function Vote() {
    const { user } = useAuth();

    // 4-Tier State Hierarchy
    const [activeIndex, setActiveIndex] = useState(null);
    const [activeSector, setActiveSector] = useState(null);
    const [activeCompany, setActiveCompany] = useState(null);

    const [selectedVote, setSelectedVote] = useState(null);
    const [voteStatus, setVoteStatus] = useState(null);

    // Derived 4-Tier Data Sets
    const indices = useMemo(() => Array.from(new Set(NIFTY50_BRANDS.map(b => b.index))).sort(), []);

    // Automatically select the first Index if none is selected
    if (!activeIndex && indices.length > 0) {
        setActiveIndex(indices[0]);
    }

    const availableSectors = useMemo(() => {
        if (!activeIndex) return [];
        return Array.from(new Set(NIFTY50_BRANDS.filter(b => b.index === activeIndex).map(b => b.sector))).sort();
    }, [activeIndex]);

    const availableCompanies = useMemo(() => {
        if (!activeIndex || !activeSector) return [];
        return Array.from(new Set(NIFTY50_BRANDS.filter(b => b.index === activeIndex && b.sector === activeSector).map(b => b.company))).sort();
    }, [activeIndex, activeSector]);

    const availableBrands = useMemo(() => {
        if (!activeIndex || !activeSector || !activeCompany) return [];
        return NIFTY50_BRANDS.filter(b => b.index === activeIndex && b.sector === activeSector && b.company === activeCompany)
            .sort((a, b) => a.brand.localeCompare(b.brand));
    }, [activeIndex, activeSector, activeCompany]);

    if (!user) {
        return <Navigate to="/" />;
    }

    const handleVoteSubmit = async (ticker) => {
        if (!ticker) return;
        setVoteStatus('submitting');
        try {
            await axios.post('/api/puzzles/vote', { ticker: ticker });
            setVoteStatus('success');
        } catch (err) {
            console.error('Failed to submit vote', err);
            setVoteStatus('error');
        }
    };

    // Resets cascading tiers upon higher-level selections
    const handleIndexClick = (index) => {
        if (activeIndex !== index) {
            setActiveIndex(index);
            setActiveSector(null);
            setActiveCompany(null);
            setSelectedVote(null);
        }
    };

    const handleSectorClick = (sector) => {
        if (activeSector !== sector) {
            setActiveSector(sector);
            setActiveCompany(null);
            setSelectedVote(null);
        }
    };

    const handleCompanyClick = (company) => {
        if (activeCompany !== company) {
            setActiveCompany(company);
            setSelectedVote(null);
        }
    };

    const getDynamicDescription = () => {
        let indexType = "megacaps";
        if (activeIndex === "Nifty Next 50") indexType = "Future megacaps";
        if (activeIndex === "Nifty Midcap") indexType = "midcaps";

        if (activeCompany && activeSector) {
            return `Select an active Indian ${indexType} brand from ${activeCompany} (${activeSector}) for tomorrow's puzzle challenge.`;
        } else if (activeSector) {
            return `Select an active Indian ${indexType} brand from the ${activeSector} sector for tomorrow's puzzle challenge.`;
        } else {
            return `Select an active Indian ${indexType} brand for tomorrow's puzzle challenge.`;
        }
    };

    return (
        <div className="h-[calc(100vh-64px)] w-full bg-[#f8fafc] flex flex-col py-6 px-4 md:px-8 overflow-y-auto font-sans">
            <div className="flex-1 w-full max-w-7xl mx-auto flex flex-col min-h-0">

                <div className="mb-4 shrink-0 text-center">
                    <h1 className="text-3xl font-black text-slate-800 flex items-center justify-center gap-2">
                        <BarChart3 className="text-indigo-600" size={32} />
                        Market Rover <span className="text-indigo-600">Brand Profiler</span>
                    </h1>
                    <p className="text-sm text-slate-500 mt-2 font-medium">
                        {getDynamicDescription()}
                    </p>
                </div>

                <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0 items-start justify-center">

                    {/* Main Interaction Area */}
                    <div className="flex-[3] flex flex-col min-h-0 w-full bg-white rounded-xl shadow-sm border border-slate-200 p-6">

                        {/* 4-Tier Selection System */}
                        <div className="flex flex-col gap-5 border-b border-slate-100 pb-5">

                            {/* Tier 1: Index (Chips wrap, NO SCROLLBAR) */}
                            <div className="flex flex-col gap-2">
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">1. Market Index</div>
                                <div className="flex flex-wrap gap-2">
                                    {indices.map(idx => (
                                        <button
                                            key={idx}
                                            onClick={() => handleIndexClick(idx)}
                                            className={`px-4 py-2 text-sm font-semibold rounded-full transition-all border
                                                    ${activeIndex === idx
                                                    ? 'bg-slate-800 text-white border-slate-800 shadow-md'
                                                    : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:bg-slate-50'
                                                }
                                                `}
                                        >
                                            {idx}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Tier 2: Sector (Chips wrap, NO SCROLLBAR) */}
                            {availableSectors.length > 0 && (
                                <div className="flex flex-col gap-2 mt-2 animate-in fade-in duration-300">
                                    <div className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">2. Target Sector</div>
                                    <div className="flex flex-wrap gap-2">
                                        {availableSectors.map(sector => (
                                            <button
                                                key={sector}
                                                onClick={() => handleSectorClick(sector)}
                                                className={`px-3.5 py-1.5 text-sm font-semibold rounded-md transition-all border
                                                        ${activeSector === sector
                                                        ? 'bg-indigo-50 text-indigo-700 border-indigo-200 shadow-sm'
                                                        : 'bg-white text-slate-500 border-transparent hover:bg-slate-50 hover:text-slate-700'
                                                    }
                                                    `}
                                            >
                                                {sector}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Tier 3: Company (Chips wrap, NO SCROLLBAR) */}
                            {availableCompanies.length > 0 && (
                                <div className="flex flex-col gap-2 mt-2 animate-in fade-in duration-300">
                                    <div className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1 flex items-center gap-1"><Building2 size={14} /> 3. Parent Company</div>
                                    <div className="flex flex-wrap gap-2">
                                        {availableCompanies.map(comp => (
                                            <button
                                                key={comp}
                                                onClick={() => handleCompanyClick(comp)}
                                                className={`px-3.5 py-2 text-sm font-medium rounded-lg transition-all border
                                                        ${activeCompany === comp
                                                        ? 'bg-blue-600 text-white border-blue-600 shadow-md'
                                                        : 'bg-white text-slate-600 border-slate-200 hover:border-blue-400 hover:text-blue-600 hover:shadow-sm'
                                                    }
                                                    `}
                                            >
                                                {comp}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Tier 4: Brand Grid (Responsive Cards) */}
                        <div className="flex-1 mt-5 min-h-[300px]">
                            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1 flex items-center gap-1 mb-3"><Store size={14} /> 4. Core Brands</div>

                            {availableBrands.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                    {availableBrands.map(b => {
                                        const isSelected = selectedVote?.id === b.id;
                                        return (
                                            <button
                                                key={b.id}
                                                onClick={() => setSelectedVote(b)}
                                                className={`
                                                        flex items-center p-2.5 bg-white rounded-xl border text-left transition-all group
                                                        ${isSelected
                                                        ? 'border-indigo-500 ring-2 ring-indigo-100 shadow-md scale-[1.02] z-10'
                                                        : 'border-slate-200 hover:border-indigo-300 hover:shadow-sm'
                                                    }
                                                    `}
                                            >
                                                {/* Uniform Scale Authentic Logo */}
                                                <div className="w-[45px] h-[45px] shrink-0 bg-white border border-slate-100 rounded-lg p-1.5 shadow-sm mr-3 flex flex-col items-center justify-center">
                                                    <img
                                                        src={b.logoUrl}
                                                        alt={b.brand}
                                                        className="w-full h-full object-contain"
                                                        onError={(e) => { e.target.src = '/placeholder-logo.png'; }}
                                                    />
                                                </div>

                                                {/* Text Data Stack */}
                                                <div className="flex flex-col overflow-hidden leading-tight flex-1">
                                                    <div className="font-bold text-[14px] text-slate-800 truncate pr-2 group-hover:text-indigo-700 transition-colors">
                                                        {b.brand}
                                                    </div>
                                                    <div className="text-[11px] text-slate-500 truncate mt-0.5">
                                                        Ticker: {b.ticker}
                                                    </div>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center text-slate-400 h-full border-2 border-dashed border-slate-100 rounded-xl">
                                    <Navigation size={32} className="text-slate-200 mb-2" />
                                    <span className="font-medium">Please select an Index, Sector, and Company above.</span>
                                </div>
                            )}
                        </div>

                    </div>

                    {/* Sidebar */}
                    <div className="lg:w-[340px] flex-shrink-0 flex flex-col h-full bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                        <h3 className="text-[13px] font-black text-slate-400 mb-6 uppercase tracking-widest w-full border-b border-slate-100 pb-3 text-center">Selected Prospect</h3>

                        {voteStatus === 'success' && (
                            <div className="mb-6 w-full p-4 bg-emerald-50 border border-emerald-100 rounded-xl animate-in zoom-in duration-300">
                                <div className="flex items-center gap-3 text-emerald-700">
                                    <CheckCircle className="text-emerald-500 shrink-0" size={20} />
                                    <div>
                                        <div className="font-bold text-sm">Vote Logged!</div>
                                        <div className="text-[11px] opacity-80 leading-tight">Your selected brand will be tracked for tomorrow's challenge.</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="flex-1 flex flex-col items-center justify-center w-full min-h-[300px]">
                            {selectedVote ? (
                                <div className="flex flex-col items-center animate-in zoom-in duration-300 w-full">

                                    <div className="w-32 h-32 rounded-2xl shadow-lg border border-slate-100 overflow-hidden mb-5 bg-white flex items-center justify-center p-3">
                                        <img src={selectedVote.logoUrl} alt={selectedVote.brand} className="w-full h-full object-contain drop-shadow-sm" />
                                    </div>

                                    <div className="text-slate-800 font-black text-2xl text-center leading-tight mb-1">{selectedVote.brand}</div>
                                    <div className="text-slate-500 text-sm font-medium mb-6 text-center">{selectedVote.company}</div>

                                    <div className="w-full flex justify-between items-center text-xs text-slate-600 border-t border-b border-slate-100 py-3 mb-2">
                                        <span className="font-bold uppercase tracking-wider text-slate-400">Index</span>
                                        <span className="bg-slate-100 px-3 py-1 rounded-full font-bold">{selectedVote.index}</span>
                                    </div>

                                    <div className="w-full flex justify-between items-center text-xs text-slate-600 pb-3 mb-4 border-b border-slate-100">
                                        <span className="font-bold uppercase tracking-wider text-slate-400">Sector</span>
                                        <span className="bg-slate-100 px-3 py-1 rounded-full font-bold">{selectedVote.sector}</span>
                                    </div>

                                    <div className="w-full flex justify-between items-center text-xs text-slate-500 pb-3 mb-2">
                                        <span className="font-bold uppercase tracking-wider text-slate-400">Ticker ID</span>
                                        <span className="bg-indigo-50 text-indigo-700 border border-indigo-100 px-3 py-1 rounded-full font-black text-sm">{selectedVote.ticker}</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center text-slate-400 p-6 border-2 border-dashed border-slate-200 bg-slate-50 rounded-xl text-center w-full h-full">
                                    <div className="w-16 h-16 rounded-xl bg-white shadow-sm flex items-center justify-center mb-4">
                                        <Navigation size={24} className="text-slate-300" />
                                    </div>
                                    <span className="font-bold text-slate-400">Waiting for selection</span>
                                    <span className="text-[11px] text-slate-400 mt-2">Walk through the 4 steps</span>
                                </div>
                            )}
                        </div>

                        <div className="w-full mt-auto pt-4 border-t border-slate-100">
                            <button
                                onClick={() => handleVoteSubmit(selectedVote?.ticker)}
                                disabled={!selectedVote || voteStatus === 'submitting'}
                                className={`w-full py-3.5 rounded-xl font-bold text-[15px] transition-all focus:outline-none mb-4
                                        ${selectedVote && voteStatus !== 'submitting'
                                        ? 'bg-indigo-600 text-white shadow-md hover:bg-indigo-700 active:scale-[0.98] flex items-center justify-center gap-2'
                                        : 'bg-slate-100 text-slate-400 cursor-not-allowed flex items-center justify-center'
                                    }
                                    `}
                            >
                                {voteStatus === 'submitting' ? 'Submitting...' : 'Confirm Vote'}
                            </button>

                            {voteStatus === 'error' && (
                                <div className="mb-3 w-full p-3 bg-red-50 text-red-600 rounded-lg text-[13px] font-bold text-center border border-red-100">
                                    Failed to submit your vote. Please try again.
                                </div>
                            )}

                            <p className="text-[10px] text-slate-400 text-center uppercase tracking-wide leading-tight px-2 font-semibold">
                                Disclaimer: All product names, logos, and brands are property of their respective owners. Used here for identification and educational gaming purposes only. No endorsement or affiliation is implied.
                            </p>
                        </div>
                    </div>

                </div>
                )}
            </div>
        </div>
    );
}
