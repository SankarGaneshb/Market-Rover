import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Trophy, Zap, Share2, Calendar, Clock, Move, RotateCcw, Eye, X, Award, TrendingUp, Lightbulb } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NIFTY50_BRANDS } from '../data/brands';
import { getVirtuosoLevel, getNextVirtuosoLevel } from '../data/virtuoso';
import GlitterBadge from '../components/GlitterBadge';

export default function PuzzleGame() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [gameState, setGameState] = useState('loading'); // loading, menu, playing, completed
  const [difficulty, setDifficulty] = useState(null);
  const [currentBrand, setCurrentBrand] = useState(null);
  const [dbPuzzleId, setDbPuzzleId] = useState(null);
  const [completedToday, setCompletedToday] = useState(false);

  const [pieces, setPieces] = useState([]);
  const [solvedPositions, setSolvedPositions] = useState({});
  const [draggedPiece, setDraggedPiece] = useState(null);
  const [timer, setTimer] = useState(0);
  const [boardSize, setBoardSize] = useState(300);
  const boardContainerRef = useRef(null);

  const [moves, setMoves] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [streak, setStreak] = useState(0);
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);

  const timerRef = useRef(null);

  const difficultyLevels = {
    easy: { grid: 3, pieces: 9, label: 'Easy' },
    medium: { grid: 4, pieces: 16, label: 'Medium' },
    hard: { grid: 5, pieces: 25, label: 'Hard' }
  };

  // Resize listener to perfectly bound the puzzle board into the screen without scrollbars
  useEffect(() => {
    const updateSize = () => {
      if (boardContainerRef.current) {
        const { width, height } = boardContainerRef.current.getBoundingClientRect();
        const size = Math.min(width - 16, height - 16, 600);
        setBoardSize(size);
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [gameState, showHint]);

  useEffect(() => {
    fetchDailyPuzzle();
  }, []);

  useEffect(() => {
    if (gameState === 'playing') {
      timerRef.current = setInterval(() => {
        setTimer(t => t + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [gameState]);

  const getBrandColors = (brand) => {
    const sectorColors = {
      'IT': { light: '#0ea5e9', dark: '#0369a1' },
      'Financials': { light: '#64748b', dark: '#1e293b' },
      'Energy': { light: '#f59e0b', dark: '#92400e' },
      'FMCG': { light: '#10b981', dark: '#064e3b' },
      'Telecom': { light: '#f43f5e', dark: '#881337' },
      'Automobile': { light: '#6366f1', dark: '#312e81' },
      'Healthcare': { light: '#14b8a6', dark: '#0f766e' },
      'Consumer': { light: '#8b5cf6', dark: '#4c1d95' },
      'Infrastructure': { light: '#f97316', dark: '#9a3412' },
      'Metals': { light: '#94a3b8', dark: '#334155' },
      'default': { light: '#3b82f6', dark: '#1d4ed8' }
    };
    return sectorColors[brand?.sector] || sectorColors.default;
  };

  const fetchDailyPuzzle = async () => {
    try {
      const { data } = await axios.get('/api/puzzles/daily');
      let matchedBrand = null;
      if (data) {
        matchedBrand = NIFTY50_BRANDS.find(b => b.ticker === data.ticker);
        setDbPuzzleId(data.id);
      }
      if (matchedBrand) {
        setCurrentBrand(matchedBrand);
      } else {
        const todayIndex = Math.floor(Date.now() / 86400000) % NIFTY50_BRANDS.length;
        setCurrentBrand(NIFTY50_BRANDS[todayIndex]);
        setDbPuzzleId(data ? data.id : null);
      }

      if (user) {
        setStreak(user.streak || 0);
        setScore(user.score || 0);
        setBestScore(user.bestScore || 0);
        if (data && data.id) {
          try {
            const sessions = await axios.get('/api/users/me/sessions');
            const done = sessions.data.some(s => s.puzzle_id === data.id && s.completed);
            setCompletedToday(done);
          } catch (e) {
            console.error('Failed to check session status', e);
          }
        }
      }
      setGameState('menu');
    } catch (err) {
      console.error('Failed to fetch daily puzzle', err);
      const todayIndex = Math.floor(Date.now() / 86400000) % NIFTY50_BRANDS.length;
      setCurrentBrand(NIFTY50_BRANDS[todayIndex]);
      setGameState('menu');
    }
  };

  const saveGameData = async (gameScore, movesUsed, timeTaken) => {
    if (!dbPuzzleId) return;
    try {
      const response = await axios.post(`/api/puzzles/${dbPuzzleId}/complete`, {
        score: gameScore,
        movesUsed: movesUsed,
        timeTaken: timeTaken
      });
      if (response.data.success) {
        setStreak(response.data.streak);
        if (response.data.realTotal !== undefined) {
          setScore(response.data.realTotal);
        } else {
          setScore(prev => prev + gameScore);
        }
        if (gameScore > bestScore) {
          setBestScore(gameScore);
        }
      }
    } catch (error) {
      console.error('Failed to save puzzle result', error);
    }
  };

  const startGame = (diff) => {
    setDifficulty(diff);
    setTimer(0);
    setMoves(0);
    setSolvedPositions({});
    setShowHint(false);

    const gridSize = difficultyLevels[diff].grid;
    const puzzlePieces = [];
    for (let i = 0; i < gridSize * gridSize; i++) {
      puzzlePieces.push({
        id: i,
        correctPosition: i,
        currentPosition: i
      });
    }
    for (let i = puzzlePieces.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const temp = puzzlePieces[i].currentPosition;
      puzzlePieces[i].currentPosition = puzzlePieces[j].currentPosition;
      puzzlePieces[j].currentPosition = temp;
    }
    setPieces(puzzlePieces);
    setGameState('playing');
  };

  const handleDragStart = (e, piece) => {
    e.dataTransfer.effectAllowed = 'move';
    setDraggedPiece(piece);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetPosition) => {
    e.preventDefault();
    if (!draggedPiece) return;
    const newPieces = [...pieces];
    const draggedPieceObj = newPieces.find(p => p.id === draggedPiece.id);
    const targetPieceObj = newPieces.find(p => p.currentPosition === targetPosition);

    if (draggedPieceObj && targetPieceObj && draggedPieceObj.id !== targetPieceObj.id) {
      const tempPosition = draggedPieceObj.currentPosition;
      draggedPieceObj.currentPosition = targetPieceObj.currentPosition;
      targetPieceObj.currentPosition = tempPosition;
      setPieces(newPieces);
      const newMoves = moves + 1;
      setMoves(newMoves);

      const newSolved = {};
      newPieces.forEach(piece => {
        if (piece.correctPosition === piece.currentPosition) {
          newSolved[piece.id] = true;
        }
      });
      setSolvedPositions(newSolved);

      if (Object.keys(newSolved).length === newPieces.length) {
        setTimeout(() => completeGame(newMoves), 500);
      }
    }
    setDraggedPiece(null);
  };

  const completeGame = async (finalMoves) => {
    if (timerRef.current) clearInterval(timerRef.current);
    const gameScore = calculateScore(finalMoves);
    setGameState('completed');
    setCompletedToday(true);
    await saveGameData(gameScore, finalMoves, timer);
  };

  const calculateScore = (finalMoves = moves) => {
    if (!difficulty) return 0;
    const baseScore = difficultyLevels[difficulty].pieces * 100;
    const timeBonus = Math.max(0, 300 - timer);
    const moveBonus = Math.max(0, 200 - finalMoves * 2);
    return baseScore + timeBonus + moveBonus;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const shareScore = () => {
    const url = `${window.location.origin}?promoter=${user?.id || ''}&ref=score`;
    const baseMessage = `🎯 Brand to Stock!\nLearn to invest through brands you use daily.`;
    let text = gameState === 'completed'
      ? `${baseMessage}\n\n🔥 Streak: ${streak} days\n⏱️ ${formatTime(timer)}\n🎮 ${moves} moves\n🏆 ${calculateScore()} points\n\nSolved ${currentBrand.brand}!\n\nJoin me at: ${url}`
      : `${baseMessage}\n\nJoin me at: ${url}`;

    if (navigator.share) {
      navigator.share({ title: 'InvestBrand - Brand to Stock', text: text, url: url });
    } else {
      navigator.clipboard.writeText(text);
      alert('Invite link copied to clipboard!');
    }
  };

  const shareLeaderboard = () => {
    const url = `${window.location.origin}/leaderboard?promoter=${user?.id || ''}&ref=leaderboard`;
    const text = `🎯 Brand to Stock!\nCheck out the Nifty stocks leaderboard. I'm on a ${streak} day streak!\n\nSee it here: ${url}`;
    if (navigator.share) {
      navigator.share({ title: 'InvestBrand Leaderboard', text: text, url: url });
    } else {
      navigator.clipboard.writeText(text);
      alert('Leaderboard link copied!');
    }
  };

  if (gameState === 'loading') {
    return <div className="flex items-center justify-center min-h-[500px] text-white font-bold">Loading challenge...</div>;
  }

  if (gameState === 'menu') {
    return (
      <div className="fixed inset-0 top-[64px] bg-[#030014] p-2 sm:p-4 flex items-center justify-center overflow-hidden" style={{ height: "calc(100vh - 64px)" }}>
        {/* Animated Ultra-Vibrant Mesh Background */}
        <div className="absolute inset-0 z-0 opacity-40 pointer-events-none transform scale-110">
          <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/20 blur-[150px] mix-blend-screen animate-blob" />
          <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-cyan-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
        </div>

        <div className="max-w-4xl w-full relative z-10">
          <div className="text-center mb-4 sm:mb-6">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 sm:mb-4">Brand to Stock</h1>
            <p className="text-xl text-white/90 mb-6">Learn investing through brands you use daily!</p>
            <div className="flex items-center justify-center gap-6 text-white/80 mb-8">
              <div className="flex items-center gap-2">
                <Zap className="text-yellow-300" size={20} />
                <span className="font-bold">{streak} Day Streak</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="text-green-300" size={20} />
                <span className="font-bold">{score} Total Score</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl p-4 sm:p-8 mb-6 relative overflow-hidden">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Calendar className="text-blue-600" />
                Today's Challenge
              </span>
              {completedToday && <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full font-bold">Completed</span>}
            </h2>

            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 mb-8 border border-blue-100">
              <div className="flex items-center gap-5">
                <div className="w-20 h-20 bg-white rounded-xl shadow-sm flex items-center justify-center p-3 border border-blue-50">
                  <TrendingUp className="text-blue-600" size={40} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold text-blue-500 uppercase tracking-wider mb-1">Nifty 50 Spotlight</div>
                  <div className="text-3xl font-black text-slate-800">{currentBrand?.brand}</div>
                  <div className="text-sm text-slate-500 font-medium">{currentBrand?.company}</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(difficultyLevels).map(([key, value]) => (
                <button
                  key={key}
                  onClick={() => startGame(key)}
                  className="group bg-slate-50 hover:bg-indigo-600 text-slate-800 hover:text-white p-6 rounded-2xl font-bold transition-all border border-slate-100 hover:border-indigo-500 hover:shadow-xl relative overflow-hidden"
                >
                  <div className="relative z-10">
                    <div className="text-2xl mb-1">{value.label}</div>
                    <div className="text-xs font-medium opacity-60 group-hover:opacity-100">{value.pieces} pieces</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: <Trophy className="text-yellow-500" />, label: 'Leaderboard', path: '/leaderboard' },
              { icon: <Calendar className="text-indigo-500" />, label: 'Vote Next', path: '/vote' },
              { icon: <Trophy className="text-amber-500" />, label: 'Share Stats', action: shareLeaderboard },
              { icon: <Share2 className="text-blue-500" />, label: 'Invite Friends', action: shareScore }
            ].map((btn, i) => (
              <button
                key={i}
                onClick={btn.action || (() => navigate(btn.path))}
                className="bg-white/10 backdrop-blur-md text-white py-3 px-2 rounded-xl font-bold hover:bg-white/20 transition-all border border-white/10 flex flex-col items-center gap-1 shadow-lg"
              >
                {btn.icon}
                <span className="text-xs">{btn.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (gameState === 'completed') {
    return (
      <div className="fixed inset-0 top-[64px] bg-[#030014] p-2 sm:p-4 flex items-center justify-center overflow-hidden" style={{ height: "calc(100vh - 64px)" }}>
        {/* Animated Ultra-Vibrant Mesh Background */}
        <div className="absolute inset-0 z-0 opacity-40 pointer-events-none transform scale-110">
          <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-emerald-600/20 blur-[150px] mix-blend-screen animate-blob" />
          <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-teal-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
        </div>

        <div className="max-w-5xl w-full h-full flex flex-col items-center justify-center p-2 lg:p-4 relative z-10">
          <div className="bg-white rounded-[2.5rem] shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] p-5 lg:p-8 text-center w-full max-h-[95vh] flex flex-col min-h-0 border border-white/20">

            <div className="flex-shrink-0 mb-4 lg:mb-6">
              <div className="text-4xl lg:text-5xl mb-1">🎉</div>
              <h2 className="text-3xl lg:text-4xl font-black text-slate-800 tracking-tight leading-none mb-1">Puzzle Solved!</h2>
              <p className="text-sm lg:text-base text-slate-500 font-bold uppercase tracking-widest">You discovered a Nifty investment</p>
            </div>

            <div className="flex-1 min-h-0 flex flex-col md:flex-row gap-4 lg:gap-6 mb-4 lg:mb-6">

              {/* Left Column: Brand Reveal */}
              <div className="flex-[1.2] bg-gradient-to-br from-blue-50 to-indigo-50/30 rounded-[2rem] p-5 lg:p-6 border border-indigo-100 flex flex-col items-center justify-center relative shadow-inner">
                <div className="w-20 h-20 lg:w-28 lg:h-28 mb-4 bg-white rounded-2xl shadow-lg p-3 lg:p-4 flex items-center justify-center flex-shrink-0 z-10 transition-transform hover:scale-105 duration-500">
                  {currentBrand?.logoSvg ? (
                    <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }} />
                  ) : (
                    <img src={currentBrand?.logoUrl} alt={currentBrand?.brand} className="max-w-full max-h-full object-contain" />
                  )}
                </div>
                <h3 className="text-2xl lg:text-3xl font-black text-slate-800 mb-1 leading-tight text-center">{currentBrand?.brand}</h3>
                <div className="inline-block bg-indigo-600 text-white px-3 py-1 rounded-full text-[10px] lg:text-xs font-bold mb-4 shadow-sm">{currentBrand?.ticker}</div>

                <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl border border-white text-left shadow-[0_8px_30px_rgb(0,0,0,0.04)] w-full flex-1">
                  <div className="flex items-center gap-2 mb-2 text-indigo-600 font-black text-[10px] lg:text-xs uppercase tracking-widest">
                    <Lightbulb size={14} className="animate-pulse" /> Brand Insight
                  </div>
                  <p className="text-[11px] lg:text-xs text-slate-600 font-medium leading-relaxed">{currentBrand?.insight}</p>
                </div>
              </div>

              {/* Right Column: Mastery & Stats */}
              <div className="flex-1 flex flex-col gap-4 lg:gap-6">

                {/* Mastery Status Card */}
                <div className="bg-slate-50 rounded-[2rem] p-4 lg:p-5 border border-slate-100 flex items-center gap-4 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out pointer-events-none" />
                  <div className="flex-shrink-0 transform scale-[1.3] lg:scale-[1.5] origin-left ml-2">
                    {(() => {
                      const level = getVirtuosoLevel(streak);
                      return <GlitterBadge size="small" icon={level.icon} name={level.name} levelConfig={level} />;
                    })()}
                  </div>
                  <div className="flex-1 text-left min-w-0 z-10">
                    <div className="text-[9px] lg:text-[10px] font-black text-slate-400 uppercase tracking-widest mb-0.5">Current Mastery</div>
                    <div className="text-lg lg:text-xl font-black text-slate-800 uppercase tracking-tighter truncate leading-none mb-2">
                      {getVirtuosoLevel(streak).name.split(' ')[0]}
                    </div>
                    {(() => {
                      const nextLevel = getNextVirtuosoLevel(streak);
                      if (!nextLevel) return null;
                      return (
                        <div className="w-full">
                          <div className="flex justify-between text-[9px] lg:text-[10px] font-bold text-slate-500 mb-1.5 px-0.5">
                            <span className="text-indigo-600">Next: {nextLevel.name.split(' ')[0]}</span>
                            <span>{nextLevel.minDays - streak}d left</span>
                          </div>
                          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden shadow-inner">
                            <div
                              className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)] transition-all duration-1000 ease-out"
                              style={{ width: `${Math.min(100, (streak / nextLevel.minDays) * 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3 lg:gap-4 flex-1">
                  {[
                    { label: 'Time', value: formatTime(timer), icon: <Clock size={18} />, bg: 'bg-blue-50', text: 'text-blue-600', labelColor: 'text-blue-400' },
                    { label: 'Moves', value: moves, icon: <Move size={18} />, bg: 'bg-purple-50', text: 'text-purple-600', labelColor: 'text-purple-400' },
                    { label: 'Score', value: calculateScore(), icon: <Trophy size={18} />, bg: 'bg-green-50', text: 'text-green-600', labelColor: 'text-green-400' },
                    { label: 'Streak', value: `${streak}d`, icon: <Zap size={18} />, bg: 'bg-orange-50', text: 'text-orange-600', labelColor: 'text-orange-400' }
                  ].map((stat, i) => (
                    <div key={i} className={`${stat.bg} rounded-2xl lg:rounded-[1.5rem] p-3 lg:p-4 flex flex-col justify-center`}>
                      <div className={`text-[9px] lg:text-[10px] font-black uppercase ${stat.labelColor} tracking-widest mb-1`}>{stat.label}</div>
                      <div className={`text-xl lg:text-2xl font-black ${stat.text} flex items-center gap-2 leading-none`}>
                        {stat.icon} {stat.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom Actions Row */}
            <div className="flex-shrink-0 grid grid-cols-2 sm:grid-cols-4 gap-2 lg:gap-3">
              <button onClick={() => navigate('/vote')} className="bg-slate-100 text-slate-600 py-3 lg:py-3.5 rounded-xl lg:rounded-2xl font-black text-xs lg:text-sm hover:bg-slate-200 transition-colors flex items-center justify-center gap-2">
                <Calendar size={16} /> Vote Next
              </button>
              <button onClick={shareLeaderboard} className="bg-slate-100 text-slate-600 py-3 lg:py-3.5 rounded-xl lg:rounded-2xl font-black text-xs lg:text-sm hover:bg-slate-200 transition-colors flex items-center justify-center gap-2">
                <Trophy size={16} /> Leaderboard
              </button>
              <button onClick={shareScore} className="bg-indigo-50 text-indigo-600 py-3 lg:py-3.5 rounded-xl lg:rounded-2xl font-black text-xs lg:text-sm hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2">
                <Share2 size={16} /> Share Record
              </button>
              <button onClick={() => setGameState('menu')} className="bg-indigo-600 text-white py-3 lg:py-3.5 rounded-xl lg:rounded-2xl font-black text-xs lg:text-sm hover:bg-indigo-700 shadow-lg shadow-indigo-600/30 transition-all active:scale-95">
                Play Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const gridSize = difficultyLevels[difficulty]?.grid || 3;

  return (
    <div className="fixed inset-0 top-[64px] bg-[#030014] font-sans overflow-hidden" style={{ height: "calc(100vh - 64px)" }}>
      {/* Animated Ultra-Vibrant Mesh Background */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none transform scale-110">
        <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-blue-600/20 blur-[150px] mix-blend-screen animate-blob" />
        <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-indigo-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 p-2 sm:p-4 w-full max-w-4xl mx-auto h-full flex flex-col min-h-0">
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-2 mb-2 text-white flex items-center justify-between gap-2 shadow-sm shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-black tracking-tight flex items-center gap-2">
              <Trophy size={18} className="text-yellow-400" /> Solve It!
            </h2>
            <div className="flex items-center gap-3 text-xs font-bold bg-white/10 px-3 py-1 rounded-lg">
              <span className="flex items-center gap-1"><Clock size={14} /> {formatTime(timer)}</span>
              <span className="flex items-center gap-1"><Move size={14} /> {moves}</span>
              <span className="flex items-center gap-1"><Zap size={14} className="text-orange-400" /> {streak}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowHint(!showHint)} className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg flex items-center gap-2 transition font-bold text-xs">
              <Eye size={14} /> Hint
            </button>
            <button onClick={() => setGameState('menu')} className="p-1.5 bg-red-500/80 hover:bg-red-500 rounded-lg transition">
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-3 shadow-2xl flex-1 flex flex-col min-h-0 relative">
          {showHint && (
            <div className="absolute inset-0 z-50 bg-white/95 backdrop-blur-sm flex items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
              <button onClick={() => setShowHint(false)} className="absolute top-4 right-4 p-2 bg-slate-100 rounded-full hover:bg-slate-200 transition">
                <X size={20} className="text-slate-600" />
              </button>
              <div className="w-full max-w-xs aspect-square p-8 bg-white rounded-3xl shadow-xl border border-slate-100 flex items-center justify-center relative">
                {currentBrand?.logoSvg ? (
                  <div className="w-full h-full opacity-40 grayscale" dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }} />
                ) : (
                  <img src={currentBrand?.logoUrl} alt="Hint" className="max-w-full max-h-full object-contain opacity-40 grayscale" />
                )}
                <div className="absolute inset-0 border-2 border-indigo-500/20 border-dashed rounded-3xl pointer-events-none" />
              </div>
            </div>
          )}

          <div className="mb-2 text-center">
            <div className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
              Progress: {Object.keys(solvedPositions).length} / {pieces.length}
            </div>
          </div>

          <div ref={boardContainerRef} className="flex-1 w-full min-h-0 relative flex items-center justify-center">
            <div
              className="grid shadow-inner bg-slate-50 rounded-xl"
              style={{
                gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                width: boardSize,
                height: boardSize,
                padding: '4px'
              }}
            >
              {Array.from({ length: gridSize * gridSize }).map((_, position) => {
                const piece = pieces.find(p => p.currentPosition === position);
                if (!piece) return null;

                const row = Math.floor(piece.correctPosition / gridSize);
                const col = piece.correctPosition % gridSize;
                const isSolved = solvedPositions[piece.id];

                return (
                  <div
                    key={position}
                    className={`relative overflow-hidden cursor-grab active:cursor-grabbing transition-all duration-300 border border-slate-100/30 ${isSolved ? 'shadow-inner' : 'hover:scale-[1.02] hover:z-50 hover:shadow-2xl'}`}
                    style={{ aspectRatio: '1', touchAction: 'none' }}
                    draggable
                    onDragStart={(e) => handleDragStart(e, piece)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, position)}
                  >
                    <div className="absolute inset-0 bg-white">
                      {(() => {
                        let imageUrl = '';
                        if (currentBrand?.logoSvg) {
                          const encodedSvg = encodeURIComponent(currentBrand.logoSvg)
                            .replace(/'/g, "%27")
                            .replace(/"/g, "%22");
                          imageUrl = `url("data:image/svg+xml;charset=utf-8,${encodedSvg}")`;
                        } else {
                          imageUrl = `url("${currentBrand?.logoUrl}")`;
                        }

                        return (
                          <div
                            className={`absolute inset-0 ${isSolved ? 'opacity-100' : 'opacity-90'}`}
                            style={{
                              backgroundImage: imageUrl,
                              // Force the background to be the size of the ENTIRE board.
                              // e.g. for a 3x3 grid, the background is 300% width and 300% height
                              // of the individual piece.
                              backgroundSize: `${gridSize * 100}% ${gridSize * 100}%`,
                              // Position the background so the correct "slice" is shown.
                              // If col=0, x=0%. If col=1 (in 3x3), x=50%. If col=2, x=100%.
                              backgroundPosition: `${gridSize > 1 ? (col / (gridSize - 1)) * 100 : 0}% ${gridSize > 1 ? (row / (gridSize - 1)) * 100 : 0}%`,
                              backgroundRepeat: 'no-repeat',
                              pointerEvents: "none"
                            }}
                          />
                        );
                      })()}
                    </div>
                    {isSolved && (
                      <div className="absolute top-1 right-1 bg-green-500 text-white rounded-full p-0.5 shadow-sm animate-in zoom-in">
                        <Award size={10} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-3 text-center text-slate-400 text-xs font-bold uppercase tracking-widest shrink-0">
            Drag pieces to solve
          </div>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{
        __html: `
          /* GUARANTEED ZERO SCROLLBAR: Force layout strictly visually */
          * { -ms-overflow-style: none; scrollbar-width: none; }
          *::-webkit-scrollbar { display: none !important; }
          body, html { overflow: hidden !important; height: 100vh !important; margin: 0; padding: 0; }
          
          /* Utility hide scroll for inner flex containers */
          .hide-scroll {
            -ms-overflow-style: none; 
            scrollbar-width: none; 
          }
          .hide-scroll::-webkit-scrollbar { 
            display: none !important; 
          }
          
          /* Animated Mesh Gradient Blobs */
          @keyframes blob {
            0% { transform: translate(0px, 0px) scale(1); }
            33% { transform: translate(30px, -50px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
            100% { transform: translate(0px, 0px) scale(1); }
          }
          .animate-blob {
            animation: blob 15s infinite alternate ease-in-out;
          }
          .animation-delay-2000 { animation-delay: 2s; }
          .animation-delay-4000 { animation-delay: 4s; }
        `}} />
    </div>
  );
}
