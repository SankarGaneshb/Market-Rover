import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Trophy, Zap, Share2, Calendar, Clock, Move, RotateCcw, Eye, X, Award, TrendingUp, Lightbulb } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NIFTY50_BRANDS } from '../data/brands';

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

  // Resize listener to perfectly bound the puzzle board into the screen without scrollbars
  useEffect(() => {
    const updateSize = () => {
      if (boardContainerRef.current) {
        const { width, height } = boardContainerRef.current.getBoundingClientRect();
        // The grid should be perfectly square and fit within whichever is smaller (width or height), max 600px.
        const size = Math.min(width - 16, height - 16, 600);
        setBoardSize(size);
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [gameState, showHint]); // Recompute if layout changes
  const [score, setScore] = useState(0);
  const [selectedVote, setSelectedVote] = useState('');
  const [voteStatus, setVoteStatus] = useState(null); // 'submitting', 'success', 'error'

  const timerRef = useRef(null);

  const difficultyLevels = {
    easy: { grid: 3, pieces: 9, label: 'Easy' },
    medium: { grid: 4, pieces: 16, label: 'Medium' },
    hard: { grid: 5, pieces: 25, label: 'Hard' }
  };

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
        // Fallback to local daily deterministic pick if backend puzzle can't be matched
        const todayIndex = Math.floor(Date.now() / 86400000) % NIFTY50_BRANDS.length;
        setCurrentBrand(NIFTY50_BRANDS[todayIndex]);
        setDbPuzzleId(data ? data.id : null); // Still track DB id if we want to save
      }

      // Also get user stats if we have endpoints, or default to context info
      if (user) {
        setStreak(user.streak || 0);
        setScore(user.total_score || 0);

        // Check if today's puzzle is already completed by this user
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
      // Fallback
      if (NIFTY50_BRANDS && NIFTY50_BRANDS.length > 0) {
        const todayIndex = Math.floor(Date.now() / 86400000) % NIFTY50_BRANDS.length;
        setCurrentBrand(NIFTY50_BRANDS[todayIndex]);
      }
      setGameState('menu');
    }
  };

  const saveGameData = async (gameScore, movesUsed, timeTaken) => {
    if (!dbPuzzleId) return; // Cannot save without backend puzzle ID
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

    const gridSize = difficultyLevels[diff].grid;
    const puzzlePieces = [];

    for (let i = 0; i < gridSize * gridSize; i++) {
      puzzlePieces.push({
        id: i,
        correctPosition: i,
        currentPosition: i
      });
    }

    // Shuffle pieces
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
    e.stopPropagation();

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

      const totalPieces = newPieces.length;
      const solvedCount = Object.keys(newSolved).length;

      if (solvedCount === totalPieces) {
        setTimeout(() => {
          completeGame(newMoves);
        }, 500);
      }
    }

    setDraggedPiece(null);
  };

  const completeGame = async (finalMoves) => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

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
    const text = `🎯 Brand to Stock!\n🔥 Streak: ${streak} days\n⏱️ ${formatTime(timer)}\n🎮 ${moves} moves\n🏆 ${calculateScore()} points\n\nSolved ${currentBrand.brand}!`;

    if (navigator.share) {
      navigator.share({ title: 'Brand to Stock', text: text });
    } else {
      navigator.clipboard.writeText(text);
      alert('Score copied to clipboard!');
    }
  };

  if (gameState === 'loading') {
    return <div className='flex items-center justify-center min-h-[500px] text-white'>Loading daily challenge...</div>;
  }

  if (gameState === 'menu') {
    return (
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-4 flex items-center justify-center">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">Brand to Stock</h1>
            <p className="text-xl text-white/90 mb-2">Learn investing through brands you use daily!</p>
            <div className="flex items-center justify-center gap-6 text-white/80">
              <div className="flex items-center gap-2">
                <Zap className="text-yellow-300" size={20} />
                <span>{streak} Day Streak</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="text-green-300" size={20} />
                <span>{score} Points</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl p-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Calendar className="text-blue-600" />
                Today's Challenge
              </span>
              {completedToday && (
                <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full font-bold flex items-center gap-1">
                  <Award size={14} /> Completed
                </span>
              )}
            </h2>

            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-white rounded-lg shadow-md flex items-center justify-center">
                  <TrendingUp className="text-blue-600" size={40} />
                </div>
                <div className="flex-1">
                  <div className="text-sm text-gray-600">Nifty 50 Company</div>
                  <div className="text-2xl font-bold text-gray-800">{currentBrand?.brand}</div>
                  <div className="text-sm text-gray-600">{currentBrand?.company}</div>
                </div>
              </div>
            </div>

            <h3 className="text-lg font-semibold text-gray-700 mb-4">Choose Difficulty:</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(difficultyLevels).map(([key, value]) => (
                <button
                  key={key}
                  onClick={() => startGame(key)}
                  className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-6 rounded-xl font-bold text-xl hover:scale-105 transition-transform shadow-lg"
                >
                  <div className="mb-2">{value.label}</div>
                  <div className="text-sm font-normal opacity-90">{value.pieces} pieces</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => navigate('/leaderboard')}
              className="bg-white text-gray-800 py-4 px-6 rounded-xl font-semibold hover:bg-gray-50 transition shadow-lg flex items-center justify-center gap-2"
            >
              <Trophy className="text-yellow-500" />
              Leaderboard
            </button>
            <button
              onClick={shareScore}
              className="bg-white text-gray-800 py-4 px-6 rounded-xl font-semibold hover:bg-gray-50 transition shadow-lg flex items-center justify-center gap-2"
            >
              <Share2 className="text-blue-500" />
              Invite Friends
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (gameState === 'completed') {
    return (
      <div className="h-[calc(100vh-64px)] bg-gradient-to-br from-green-600 via-emerald-600 to-teal-600 p-2 sm:p-4 flex items-center justify-center overflow-hidden">
        <div className="max-w-4xl w-full h-full flex flex-col items-center justify-center">
          <div className="bg-white rounded-3xl shadow-2xl p-4 sm:p-6 text-center w-full max-h-full flex flex-col overflow-hidden">
            <div className="shrink-0">
              <div className="text-4xl sm:text-5xl mb-2">🎉</div>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-1">Puzzle Solved!</h2>
              <p className="text-sm sm:text-base text-gray-600 mb-4">You discovered a Nifty investment!</p>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide px-2">
              <div className="flex flex-col lg:flex-row gap-4 mb-4">
                {/* Brand Info Card */}
                <div className="flex-1 bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-4 flex flex-col items-center justify-center border border-indigo-100">
                  <div className="w-24 h-24 mb-3 rounded-xl shadow-md bg-white p-2 flex items-center justify-center shrink-0">
                    {currentBrand?.logoSvg ? (
                      <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }} />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded text-gray-400 font-bold text-lg text-center p-1">
                        {currentBrand?.brand}
                      </div>
                    )}
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mb-0.5">{currentBrand?.brand}</h3>
                  <div className="text-sm text-gray-600 mb-1">{currentBrand?.company}</div>
                  <div className="inline-block bg-blue-600 text-white px-3 py-0.5 rounded-full text-xs font-semibold">{currentBrand?.ticker}</div>
                  <div className="flex items-start gap-2 bg-white/80 backdrop-blur-sm rounded-lg p-3 mt-3 text-left border border-white/50">
                    <Lightbulb className="text-yellow-500 shrink-0 mt-0.5" size={16} />
                    <p className="text-xs text-gray-700 leading-relaxed font-medium">{currentBrand?.insight}</p>
                  </div>
                </div>

                {/* Score Stats Grid */}
                <div className="flex-1 grid grid-cols-2 gap-2 sm:gap-3 h-full">
                  <div className="bg-blue-50/50 rounded-xl p-3 flex flex-col items-center justify-center border border-blue-100">
                    <div className="text-[10px] uppercase font-bold text-blue-400 mb-1">Time</div>
                    <div className="text-xl font-black text-blue-600 flex items-center gap-1.5 line-clamp-1">
                      <Clock size={18} /> {formatTime(timer)}
                    </div>
                  </div>
                  <div className="bg-purple-50/50 rounded-xl p-3 flex flex-col items-center justify-center border border-purple-100">
                    <div className="text-[10px] uppercase font-bold text-purple-400 mb-1">Moves</div>
                    <div className="text-xl font-black text-purple-600 flex items-center gap-1.5">
                      <Move size={18} /> {moves}
                    </div>
                  </div>
                  <div className="bg-green-50/50 rounded-xl p-3 flex flex-col items-center justify-center border border-green-100">
                    <div className="text-[10px] uppercase font-bold text-green-400 mb-1">Score</div>
                    <div className="text-xl font-black text-green-600 flex items-center gap-1.5">
                      <Trophy size={18} /> {calculateScore()}
                    </div>
                  </div>
                  <div className="bg-orange-50/50 rounded-xl p-3 flex flex-col items-center justify-center border border-orange-100">
                    <div className="text-[10px] uppercase font-bold text-orange-400 mb-1">Streak</div>
                    <div className="text-xl font-black text-orange-600 flex items-center gap-1.5">
                      <Zap size={18} /> {streak}d
                    </div>
                  </div>
                </div>
              </div>

              {/* Level Selection Section - Allowed after completion */}
              <div className="bg-slate-50 rounded-2xl p-4 mb-4 border border-slate-200">
                <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-3">Try Another Level?</h4>
                <div className="flex flex-wrap justify-center gap-2">
                  {Object.entries(difficultyLevels).map(([key, value]) => (
                    <button
                      key={key}
                      onClick={() => startGame(key)}
                      className={`px-4 py-2 rounded-xl font-bold text-sm transition-all shadow-sm ${difficulty === key
                        ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-400'
                        : 'bg-white text-slate-700 hover:bg-white/80 border border-slate-200'
                        }`}
                    >
                      {value.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                <button
                  onClick={() => navigate('/vote')}
                  className="bg-indigo-600 text-white py-3 rounded-xl font-bold text-sm hover:bg-indigo-700 transition-all flex items-center justify-center gap-2 shadow-md"
                >
                  <Calendar size={18} /> Vote for Tomorrow
                </button>
                <button
                  onClick={shareScore}
                  className="bg-blue-500 text-white py-3 rounded-xl font-bold text-sm hover:bg-blue-600 transition-all flex items-center justify-center gap-2 shadow-md"
                >
                  <Share2 size={18} /> Share Score
                </button>
                <button
                  onClick={() => navigate('/leaderboard')}
                  className="bg-amber-500 text-white py-3 rounded-xl font-bold text-sm hover:bg-amber-600 transition-all flex items-center justify-center gap-2 shadow-md"
                >
                  <Trophy size={18} /> Leaderboard
                </button>
                <button
                  onClick={() => setGameState('menu')}
                  className="bg-gray-100 text-gray-700 py-3 rounded-xl font-bold text-sm hover:bg-gray-200 transition-all"
                >
                  Back to Menu
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const gridSize = difficultyLevels[difficulty]?.grid || 3;

  return (
    <div className="h-[calc(100vh-64px)] bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 p-2 sm:p-4 flex flex-col overflow-hidden font-sans">
      <div className="w-full max-w-4xl mx-auto h-full flex flex-col min-h-0">
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-2 mb-2 text-white shrink-0 flex flex-col sm:flex-row items-center justify-between gap-2 shadow-sm">
          <div className="flex items-center gap-3 w-full sm:w-auto overflow-hidden">
            <h2 className="text-[15px] sm:text-base font-black tracking-tight flex items-center gap-1.5 shrink-0">
              <Trophy size={16} className="text-yellow-400" />
              Solve It!
            </h2>

            <div className="flex items-center gap-3 text-xs font-semibold bg-white/10 px-2 py-1 rounded-lg shrink-0">
              <span className="flex items-center gap-1"><Clock size={14} className="text-blue-300" /> {formatTime(timer)}</span>
              <span className="flex items-center gap-1"><Move size={14} className="text-indigo-300" /> {moves}</span>
              <span className="flex items-center gap-1"><Zap size={14} className="text-orange-400" /> {streak}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 w-full sm:w-auto justify-end">
            <button onClick={() => setShowHint(!showHint)} className="px-2.5 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg flex items-center gap-1.5 transition font-bold text-xs text-white shadow-sm border border-white/10">
              <Eye size={14} /> Hint
            </button>
            <button onClick={() => startGame(difficulty)} className="px-2.5 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg flex items-center gap-1.5 transition font-bold text-xs text-white shadow-sm border border-white/10">
              <RotateCcw size={14} /> Restart
            </button>
            <button onClick={() => setGameState('menu')} className="p-1 bg-red-500/80 hover:bg-red-500 rounded-lg ml-1 transition shadow-sm border border-red-400/50">
              <X size={16} className="text-white" />
            </button>
          </div>
        </div>

        {showHint && (
          <div className="bg-white rounded-xl p-1.5 mb-2 shadow-sm border border-gray-100 flex items-center justify-center shrink-0">
            {currentBrand?.logoSvg ? (
              <div
                className="w-full max-w-[200px] h-10 mx-auto opacity-60 grayscale overflow-hidden"
                dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }}
              />
            ) : (
              <div className="w-full h-10 bg-gray-100 rounded text-gray-400 font-bold text-sm flex items-center justify-center">
                {currentBrand?.brand}
              </div>
            )}
          </div>
        )}

        <div className="bg-white rounded-xl p-2 shadow-xl flex-1 flex flex-col min-h-0 relative">
          <div className="mb-0.5 text-center shrink-0">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Progress: {Object.keys(solvedPositions).length} / {pieces.length}
            </div>
          </div>

          <div ref={boardContainerRef} className="flex-1 w-full min-h-0 relative mt-1 overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center p-2">
              <div className="grid gap-[2px] shadow-lg" style={{ gridTemplateColumns: `repeat(${gridSize}, 1fr)`, width: boardSize, height: boardSize }}>
                {Array.from({ length: gridSize * gridSize }).map((_, position) => {
                  const piece = pieces.find(p => p.currentPosition === position);
                  if (!piece) return null;

                  const row = Math.floor(piece.correctPosition / gridSize);
                  const col = piece.correctPosition % gridSize;
                  const isSolved = solvedPositions[piece.id];

                  return (
                    <div
                      key={position}
                      className={`relative cursor-grab active:cursor-grabbing ${isSolved ? 'ring-4 ring-green-400' : 'ring-2 ring-gray-400'} rounded-sm bg-white overflow-hidden transition-all ${draggedPiece?.id === piece.id ? 'opacity-50 scale-95' : 'opacity-100'}`}
                      style={{ aspectRatio: '1', touchAction: 'none' }}
                      draggable
                      onDragStart={(e) => handleDragStart(e, piece)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, position)}
                    >
                      {currentBrand?.logoSvg ? (
                        <>
                          <div
                            className="absolute pointer-events-none select-none"
                            style={{
                              width: `${gridSize * 100}%`,
                              height: `${gridSize * 100}%`,
                              left: `${-col * 100}%`,
                              top: `${-row * 100}%`,
                            }}
                            dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }}
                          />
                          <div
                            className="absolute pointer-events-none select-none flex items-center justify-center opacity-10"
                            style={{
                              width: `${gridSize * 100}%`,
                              height: `${gridSize * 100}%`,
                              left: `${-col * 100}%`,
                              top: `${-row * 100}%`,
                              zIndex: 10
                            }}
                          >
                            <div
                              style={{
                                fontSize: `${Math.max(boardSize / 8, 20)}px`,
                                fontWeight: '900',
                                color: '#000000',
                                transform: 'rotate(-35deg)',
                                whiteSpace: 'pre',
                                textAlign: 'center',
                                lineHeight: '1.4',
                                letterSpacing: '0.1em'
                              }}
                            >
                              {currentBrand.brand}<br />{currentBrand.ticker}
                            </div>
                          </div>
                        </>
                      ) : (
                        <div
                          style={{
                            position: 'absolute',
                            width: `${gridSize * 100}%`,
                            height: `${gridSize * 100}%`,
                            left: `${-col * 100}%`,
                            top: `${-row * 100}%`,
                            backgroundColor: '#f3f4f6',
                            pointerEvents: 'none',
                            userSelect: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: `${boardSize / gridSize / 3}px`,
                            fontWeight: 'bold',
                            color: '#9ca3af',
                            textAlign: 'center',
                            padding: '10%'
                          }}
                        >
                          {currentBrand?.brand}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-3 text-center text-white/80 text-[13px] font-medium shrink-0">
          Drag and drop pieces to solve the puzzle!
        </div>
      </div>
    </div>
  );
}
