import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Trophy, Zap, Clock, Move, RotateCcw, Eye, X, Award,
  TrendingUp, Lightbulb, Check, Sparkles, HelpCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NIFTY50_BRANDS } from '../data/brands';

export default function PuzzleGame() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [gameState, setGameState] = useState('loading'); // loading, menu, playing, completed
  const [difficulty, setDifficulty] = useState('easy');
  const [currentBrand, setCurrentBrand] = useState(null);
  const [dbPuzzleId, setDbPuzzleId] = useState(null);
  const [selectionMethod, setSelectionMethod] = useState(null);
  const [voteCount, setVoteCount] = useState(0);

  // Puzzle Board State
  const [pieces, setPieces] = useState([]);
  const [solvedPositions, setSolvedPositions] = useState({});
  const [draggedPiece, setDraggedPiece] = useState(null);
  const [selectedPieceId, setSelectedPieceId] = useState(null);
  const [timer, setTimer] = useState(0);
  const [boardSize, setBoardSize] = useState(380);
  const boardParentRef = useRef(null);

  const [teacherInsight, setTeacherInsight] = useState(null);
  const [isFetchingInsight, setIsFetchingInsight] = useState(false);

  const [moves, setMoves] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [streak, setStreak] = useState(0);
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);

  // Clues & Guessing State
  const [wordCloud, setWordCloud] = useState('');
  const [clues, setClues] = useState({});
  const [currentClueIdx, setCurrentClueIdx] = useState(1);
  const [userGuess, setUserGuess] = useState('');
  const [dynamicFeedback, setDynamicFeedback] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [isGuessing, setIsGuessing] = useState(false);
  const [isJigsawCompleted, setIsJigsawCompleted] = useState(false);

  const timerRef = useRef(null);

  const difficultyLevels = {
    easy: { grid: 3, pieces: 9, label: 'Easy' },
    medium: { grid: 4, pieces: 16, label: 'Medium' },
    hard: { grid: 5, pieces: 25, label: 'Hard' }
  };

  // Helper to reliably retrieve the brand's original image / SVG
  const getBrandImageSrc = (brand) => {
    if (!brand) return '';
    if (brand.logoSvg && brand.logoSvg.trim().startsWith('<svg')) {
      return `data:image/svg+xml;utf8,${encodeURIComponent(brand.logoSvg.trim())}`;
    }
    if (brand.ticker) {
      return `/investbrand/logos/${brand.ticker}.png`;
    }
    if (brand.logoUrl && !brand.logoUrl.includes('wikipedia.org')) {
      return brand.logoUrl;
    }
    return '';
  };

  useEffect(() => {
    const updateSize = () => {
      if (boardParentRef.current) {
        const { width, height } = boardParentRef.current.getBoundingClientRect();
        const available = Math.min(width - 32, height - 120, 520);
        setBoardSize(Math.max(280, available));
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
    if (gameState === 'playing' && !isJigsawCompleted) {
      if (!timerRef.current) {
        timerRef.current = setInterval(() => setTimer(t => t + 1), 1000);
      }
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [gameState, isJigsawCompleted]);

  const fetchDailyPuzzle = async () => {
    const timeoutId = setTimeout(() => {
      if (gameState === 'loading') {
        setGameState('menu');
      }
    }, 8000);

    try {
      const { data } = await axios.get('/api/puzzles/daily');
      if (data) {
        setDbPuzzleId(data.id);
        setSelectionMethod(data.selectionMethod);
        setVoteCount(data.voteCount || data.total_votes || 0);

        try {
          const clueResponse = await axios.get(`/api/puzzles/${data.id}/clues`);
          if (clueResponse.data?.success) {
            setWordCloud(clueResponse.data.clues.wordCloud || '');
            setClues(clueResponse.data.clues);
          }
        } catch (e) {
          console.error("Failed to fetch clues", e);
        }

        const matchedBrand = NIFTY50_BRANDS.find(b => b.ticker === data.ticker) || NIFTY50_BRANDS[0];
        setCurrentBrand(matchedBrand);
      } else {
        setCurrentBrand(NIFTY50_BRANDS[0]);
      }

      if (user) {
        setStreak(user.streak || 0);
        setScore(user.total_score || user.score || 0);
        setBestScore(user.best_score || user.bestScore || 0);
      }
    } catch (err) {
      console.error('Failed to fetch daily puzzle', err);
      setCurrentBrand(NIFTY50_BRANDS[0]);
    } finally {
      clearTimeout(timeoutId);
      setGameState('menu');
    }
  };

  const startGame = (diff) => {
    setDifficulty(diff);
    setTimer(0);
    setMoves(0);
    setSolvedPositions({});
    setIsJigsawCompleted(false);
    setSelectedPieceId(null);
    setAttempts(0);
    setUserGuess('');
    setDynamicFeedback('');
    setCurrentClueIdx(1);
    setShowHint(false);

    const gridSize = difficultyLevels[diff]?.grid || 3;
    const puzzlePieces = [];
    for (let i = 0; i < gridSize * gridSize; i++) {
      puzzlePieces.push({ id: i, correctPosition: i, currentPosition: i });
    }
    // Shuffle positions
    for (let i = puzzlePieces.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [puzzlePieces[i].currentPosition, puzzlePieces[j].currentPosition] = [puzzlePieces[j].currentPosition, puzzlePieces[i].currentPosition];
    }
    setPieces(puzzlePieces);

    // Initial check for any coincidentally solved positions
    const initialSolved = {};
    puzzlePieces.forEach(p => {
      if (p.correctPosition === p.currentPosition) initialSolved[p.id] = true;
    });
    setSolvedPositions(initialSolved);

    setGameState('playing');
  };

  const swapPieces = (idA, idB) => {
    if (idA === idB) return;
    const newPieces = [...pieces];
    const pieceA = newPieces.find(p => p.id === idA);
    const pieceB = newPieces.find(p => p.id === idB);

    if (pieceA && pieceB) {
      const tempPos = pieceA.currentPosition;
      pieceA.currentPosition = pieceB.currentPosition;
      pieceB.currentPosition = tempPos;

      setPieces(newPieces);
      const newMoves = moves + 1;
      setMoves(newMoves);

      const newSolved = {};
      newPieces.forEach(p => {
        if (p.correctPosition === p.currentPosition) newSolved[p.id] = true;
      });
      setSolvedPositions(newSolved);

      const solvedCount = Object.keys(newSolved).length;
      if (solvedCount >= Math.floor(newPieces.length * 0.4) && currentClueIdx < 2) {
        setCurrentClueIdx(2);
      }
      if (solvedCount >= Math.floor(newPieces.length * 0.7) && currentClueIdx < 3) {
        setCurrentClueIdx(3);
      }

      if (solvedCount === newPieces.length) {
        setIsJigsawCompleted(true);
        setCurrentClueIdx(3);
        setDynamicFeedback('🎉 Brand image fully assembled! Now identify the stock to claim your victory.');
      }
    }
  };

  const handlePieceClick = (piece) => {
    if (isJigsawCompleted) return;
    if (selectedPieceId === null) {
      setSelectedPieceId(piece.id);
    } else if (selectedPieceId === piece.id) {
      setSelectedPieceId(null);
    } else {
      swapPieces(selectedPieceId, piece.id);
      setSelectedPieceId(null);
    }
  };

  const handleDragStart = (e, piece) => {
    if (isJigsawCompleted) return;
    e.dataTransfer.effectAllowed = 'move';
    setDraggedPiece(piece);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetPosition) => {
    e.preventDefault();
    if (!draggedPiece || isJigsawCompleted) return;
    const targetPieceObj = pieces.find(p => p.currentPosition === targetPosition);
    if (targetPieceObj) {
      swapPieces(draggedPiece.id, targetPieceObj.id);
    }
    setDraggedPiece(null);
    setSelectedPieceId(null);
  };

  const autoSolve = () => {
    const solved = pieces.map(p => ({ ...p, currentPosition: p.correctPosition }));
    setPieces(solved);
    const allSolved = {};
    solved.forEach(p => { allSolved[p.id] = true; });
    setSolvedPositions(allSolved);
    setIsJigsawCompleted(true);
    setCurrentClueIdx(3);
    setDynamicFeedback('Brand reconstructed! Enter your guess below to finish the challenge.');
  };

  const handleGuess = async (e) => {
    if (e) e.preventDefault();
    if (!userGuess.trim() || attempts >= 3 || isGuessing) return;

    setIsGuessing(true);
    try {
      const { data } = await axios.post(`/api/puzzles/${dbPuzzleId || 1}/guess`, { guess: userGuess });
      const feedbackMsg = data.feedback || data.message || '';
      setDynamicFeedback(feedbackMsg);
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);

      if (data.isCorrect || data.correct) {
        setDynamicFeedback(`🎯 CORRECT! You identified ${currentBrand?.brand || data.brand}!`);
        setTimeout(() => completeGame(moves, newAttempts), 1200);
      } else {
        if (currentClueIdx < 3) setCurrentClueIdx(prev => prev + 1);
        if (newAttempts >= 3) {
          setDynamicFeedback(`Challenge finished! The answer was ${currentBrand?.brand || 'the mystery stock'}. Loading analysis...`);
          setTimeout(() => completeGame(moves, newAttempts), 2000);
        }
      }
    } catch (error) {
      console.error('Failed to evaluate guess', error);
      // Fallback local evaluation
      const normalizedGuess = userGuess.trim().toLowerCase();
      const bName = (currentBrand?.brand || '').toLowerCase();
      const ticker = (currentBrand?.ticker || '').toLowerCase();
      const comp = (currentBrand?.company || '').toLowerCase();

      if (normalizedGuess === bName || normalizedGuess === ticker || normalizedGuess === comp || (normalizedGuess.length >= 3 && bName.includes(normalizedGuess))) {
        setDynamicFeedback(`🎯 CORRECT! You identified ${currentBrand?.brand}!`);
        setTimeout(() => completeGame(moves, attempts + 1), 1200);
      } else {
        setDynamicFeedback('Not quite! Check the terminal clues on the left.');
      }
    } finally {
      setIsGuessing(false);
    }
  };

  const completeGame = async (finalMoves, finalAttempts) => {
    if (timerRef.current) clearInterval(timerRef.current);
    const gameScore = calculateScore(finalMoves, finalAttempts);
    setGameState('completed');
    fetchTeacherInsight();
    await saveGameData(gameScore, finalMoves, timer);
  };

  const saveGameData = async (gameScore, movesUsed, timeTaken) => {
    if (!dbPuzzleId) return;
    try {
      const { data } = await axios.post(`/api/puzzles/${dbPuzzleId}/complete`, {
        score: gameScore, movesUsed, timeTaken, difficulty: difficulty || 'easy'
      });
      if (data?.success) {
        setStreak(data.streak || streak + 1);
        setScore(data.realTotal || data.total_score || score + gameScore);
        if (gameScore > bestScore) setBestScore(gameScore);
      }
    } catch (e) { console.error('Failed to save result', e); }
  };

  const fetchTeacherInsight = async () => {
    if (!dbPuzzleId && !currentBrand) return;
    setIsFetchingInsight(true);
    try {
      const response = await axios.get(`/api/puzzles/${dbPuzzleId || currentBrand?.id || 1}/insight`);
      if (response.data) {
        setTeacherInsight(response.data);
      }
    } catch (e) { console.error('Failed AI insight', e); }
    finally { setIsFetchingInsight(false); }
  };

  const calculateScore = (finalMoves, finalAttempts) => {
    let points = 10;
    if (finalAttempts === 2) points = 7;
    else if (finalAttempts === 3) points = 5;
    return points * 100 + ((difficultyLevels[difficulty]?.grid || 3) * 50);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const brandImageSrc = getBrandImageSrc(currentBrand);
  const gridSize = difficultyLevels[difficulty]?.grid || 3;
  const totalPieces = gridSize * gridSize;
  const solvedCount = Object.keys(solvedPositions).length;
  const progressPercent = Math.round((solvedCount / totalPieces) * 100);

  if (gameState === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen text-white font-bold bg-[#030014]">
        Loading challenge...
      </div>
    );
  }

  // 1. Menu State
  if (gameState === 'menu') {
    return (
      <div className="fixed inset-0 top-[65px] bg-[#030014] p-4 flex items-center justify-center overflow-auto h-[calc(100vh-65px)]">
        <div className="absolute inset-0 z-0 opacity-40 pointer-events-none transform scale-110">
          <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/20 blur-[150px] mix-blend-screen animate-blob" />
          <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-cyan-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
        </div>

        <div className="max-w-4xl w-full relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-black uppercase tracking-widest mb-4">
            <Sparkles size={14} /> Brand Intelligence Challenge
          </div>
          <h1 className="text-4xl sm:text-5xl font-black text-white mb-3 tracking-tight">Market Puzzle</h1>
          <p className="text-lg text-slate-300 mb-8 max-w-xl mx-auto font-medium">
            Reconstruct the official brand logo, decode market intelligence, and identify the Nifty 50 giant!
          </p>

          <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 sm:p-8 mb-8 shadow-2xl">
            <div className="flex justify-center gap-12 mb-8 border-b border-white/10 pb-6">
              <div className="text-white">
                <div className="text-xs uppercase tracking-widest text-slate-400 mb-1">Streak</div>
                <div className="text-2xl font-black text-indigo-400">{streak} Days</div>
              </div>
              <div className="text-white">
                <div className="text-xs uppercase tracking-widest text-slate-400 mb-1">Total Score</div>
                <div className="text-2xl font-black text-white">{score}</div>
              </div>
              <div className="text-white">
                <div className="text-xs uppercase tracking-widest text-slate-400 mb-1">Best Score</div>
                <div className="text-2xl font-black text-emerald-400">{bestScore}</div>
              </div>
            </div>

            <div className="text-left mb-6">
              <div className="text-xs font-black uppercase text-indigo-300 tracking-widest mb-3">Select Difficulty</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {Object.entries(difficultyLevels).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => startGame(key)}
                    className="group bg-slate-800/80 hover:bg-indigo-600/30 p-6 rounded-2xl font-bold border border-white/10 hover:border-indigo-500/50 transition-all text-left shadow-lg transform hover:scale-[1.02] active:scale-98"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xl font-black text-white group-hover:text-indigo-300">{value.label}</span>
                      <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold">{value.grid}x{value.grid}</span>
                    </div>
                    <div className="text-xs text-slate-400">{value.pieces} jigsaw tiles to assemble</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-4 text-xs text-slate-400 flex items-center justify-center gap-3">
              <HelpCircle size={16} className="text-indigo-400" />
              <span>Tip: Click any two tiles (or drag & drop) to swap them into the correct brand logo.</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. Completed / Victory State
  if (gameState === 'completed') {
    return (
      <div className="fixed inset-0 top-[65px] bg-[#030014] p-4 flex items-center justify-center overflow-auto h-[calc(100vh-65px)]">
        <div className="max-w-4xl w-full bg-slate-900 border border-indigo-500/30 rounded-[2.5rem] p-6 sm:p-10 text-center shadow-2xl relative z-10 animate-in zoom-in-95 duration-300">
          <div className="mb-6">
            <div className="inline-flex p-3 bg-emerald-500/20 rounded-2xl border border-emerald-500/30 mb-3">
              <Trophy size={40} className="text-emerald-400" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Challenge Solved!</h2>
            <div className="text-indigo-400 font-bold uppercase tracking-widest text-sm mt-1">
              You Identified {currentBrand?.brand} ({currentBrand?.ticker})
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-slate-800/80 p-6 rounded-3xl border border-white/10 flex flex-col items-center justify-center">
              <div className="w-28 h-28 mb-3 rounded-2xl bg-white p-3 flex items-center justify-center shadow-xl overflow-hidden">
                {currentBrand?.logoSvg ? (
                  <div className="w-full h-full flex items-center justify-center" dangerouslySetInnerHTML={{ __html: currentBrand.logoSvg }} />
                ) : (
                  <img src={brandImageSrc} alt={currentBrand?.brand} className="max-w-full max-h-full object-contain" />
                )}
              </div>
              <h3 className="text-2xl font-black text-white">{currentBrand?.brand}</h3>
              <p className="text-indigo-300 text-xs font-semibold mt-1">Parent: {currentBrand?.company} • {currentBrand?.sector}</p>
              <p className="text-slate-400 font-medium text-xs mt-3 leading-relaxed text-center px-4">{currentBrand?.insight}</p>
            </div>

            <div className="bg-indigo-950/40 p-6 rounded-3xl border border-indigo-500/30 text-left flex flex-col justify-between">
              <div>
                <div className="text-xs font-black text-indigo-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Lightbulb size={16} /> AI Teacher & Market Lesson
                </div>
                {isFetchingInsight ? (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-4 bg-indigo-500/20 rounded w-3/4" />
                    <div className="h-4 bg-indigo-500/20 rounded w-full" />
                    <div className="h-4 bg-indigo-500/20 rounded w-2/3" />
                  </div>
                ) : (
                  <p className="text-indigo-100 font-medium text-sm leading-relaxed">
                    {teacherInsight?.teacher_tip || teacherInsight?.insight || `${currentBrand?.brand} is a cornerstone brand under ${currentBrand?.company} (${currentBrand?.ticker}) providing strong pricing power and competitive moat.`}
                  </p>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-indigo-500/20 grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-white/5">
                  <div className="text-[10px] text-slate-400 uppercase font-black">Time</div>
                  <div className="text-sm font-bold text-white">{formatTime(timer)}</div>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-white/5">
                  <div className="text-[10px] text-slate-400 uppercase font-black">Moves</div>
                  <div className="text-sm font-bold text-white">{moves}</div>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-white/5">
                  <div className="text-[10px] text-slate-400 uppercase font-black">Earned</div>
                  <div className="text-sm font-bold text-emerald-400">+{calculateScore(moves, attempts)} pts</div>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={() => setGameState('menu')}
            className="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white py-4 rounded-2xl font-black text-lg transition-all shadow-xl hover:shadow-indigo-500/25 transform hover:scale-[1.01]"
          >
            Play Next Challenge →
          </button>
        </div>
      </div>
    );
  }

  // 3. Main Gameplay Board
  return (
    <div className="fixed inset-0 top-[65px] bg-[#030014] p-2 sm:p-4 flex items-center justify-center overflow-auto h-[calc(100vh-65px)]">
      {/* Ambient background glows */}
      <div className="absolute inset-0 z-0 opacity-30 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] rounded-full bg-blue-600/15 blur-[140px]" />
        <div className="absolute bottom-[-30%] left-[20%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/15 blur-[140px]" />
      </div>

      <div ref={boardParentRef} className="max-w-6xl w-full h-full flex flex-col relative z-10 justify-between">
        {/* Top Control Bar */}
        <div className="w-full flex items-center justify-between bg-slate-900/80 backdrop-blur-md rounded-2xl p-3 sm:p-4 border border-white/10 shadow-xl text-white mb-2">
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-2 font-black text-xs sm:text-sm uppercase tracking-widest text-slate-300">
              <Clock size={16} className="text-indigo-400" /> {formatTime(timer)}
            </div>
            <div className="flex items-center gap-2 font-black text-xs sm:text-sm uppercase tracking-widest text-slate-300">
              <Move size={16} className="text-cyan-400" /> {moves} Moves
            </div>
            <div className="hidden sm:flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              <Check size={14} /> {solvedCount}/{totalPieces} Aligned ({progressPercent}%)
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowHint(!showHint)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${showHint ? 'bg-indigo-600 text-white border-indigo-400' : 'bg-slate-800 text-slate-300 border-white/10 hover:bg-slate-700'}`}
              title="Toggle Target Solution Preview"
            >
              <Eye size={14} /> <span className="hidden sm:inline">{showHint ? 'Hide Hint' : 'Peek Solution'}</span>
            </button>
            <button
              onClick={autoSolve}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/10 transition-colors"
              title="Auto-assemble the jigsaw"
            >
              ⚡ Auto-Solve
            </button>
            <button
              onClick={() => setGameState('menu')}
              className="p-2 hover:bg-white/10 rounded-xl transition-colors text-slate-400 hover:text-white"
              title="Exit Game"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Action / Guidance Banner */}
        <div className="w-full bg-indigo-950/40 border border-indigo-500/30 rounded-xl px-4 py-2 text-xs text-indigo-200 flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-indigo-400 flex-shrink-0" />
            <span>
              {isJigsawCompleted
                ? "🎯 Brand logo fully assembled! Read the clues and submit your guess."
                : "🧩 Click or drag any two tiles to swap & assemble the brand logo!"}
            </span>
          </div>
          {selectedPieceId !== null && (
            <span className="text-cyan-300 font-bold animate-pulse">Tile #{selectedPieceId + 1} selected — click another tile to swap</span>
          )}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 w-full flex flex-col md:flex-row gap-4 items-center justify-center min-h-0">
          {/* Left: Terminal Intelligence & Clues */}
          <div className="w-full md:w-1/3 flex flex-col gap-3 order-2 md:order-1">
            <div className="bg-slate-900/80 backdrop-blur-md p-5 rounded-3xl border border-white/10 shadow-xl">
              <div className="text-xs font-black text-indigo-300 uppercase tracking-widest mb-3 flex items-center gap-2">
                <TrendingUp size={16} /> Terminal Intelligence
              </div>
              <div className="space-y-2.5">
                {[1, 2, 3].map(idx => (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl text-xs leading-relaxed transition-all ${idx <= currentClueIdx ? 'bg-indigo-600/25 border border-indigo-500/40 text-indigo-100 shadow-md' : 'bg-slate-800/40 text-slate-500 border border-transparent'}`}
                  >
                    <div className="font-black uppercase tracking-wider text-[10px] mb-1 text-indigo-400">
                      Phase {idx} Clue {idx <= currentClueIdx ? '• Unlocked' : '• Locked'}
                    </div>
                    {idx <= currentClueIdx ? clues[`clue${idx}`] || `Operating in the ${currentBrand?.sector || 'Market'} sector.` : 'Reconstruct more pieces to unlock.'}
                  </div>
                ))}
              </div>

              {wordCloud && (
                <div className="mt-4 pt-3 border-t border-white/10">
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Market Keywords</div>
                  <div className="flex flex-wrap gap-1.5">
                    {wordCloud.split(',').map((w, i) => (
                      <span key={i} className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/20">
                        {w.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Center/Right: Scrambled Brand Logo Jigsaw */}
          <div className="flex-1 w-full flex flex-col items-center justify-center order-1 md:order-2">
            <div className="relative flex items-center justify-center">
              {/* Target Hint Ghost Overlay */}
              {showHint && (
                <div
                  className="absolute z-20 rounded-2xl overflow-hidden border-2 border-dashed border-indigo-400 bg-white/90 p-4 shadow-2xl transition-all duration-300 flex items-center justify-center pointer-events-none"
                  style={{ width: boardSize, height: boardSize }}
                >
                  <img src={brandImageSrc} alt="Hint" className="max-w-full max-h-full object-contain opacity-75" />
                  <div className="absolute bottom-2 bg-slate-900/80 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider">
                    Target Brand Solution
                  </div>
                </div>
              )}

              {/* Jigsaw Board Grid */}
              <div
                className="grid bg-slate-800/90 backdrop-blur-sm rounded-2xl overflow-hidden shadow-2xl border-2 border-white/15 relative"
                style={{
                  gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                  gridTemplateRows: `repeat(${gridSize}, 1fr)`,
                  width: boardSize,
                  height: boardSize,
                  gap: '2px',
                  padding: '4px'
                }}
              >
                {pieces.map((piece, positionIdx) => {
                  const actualPiece = pieces.find(p => p.currentPosition === positionIdx) || piece;
                  const isSolved = solvedPositions[actualPiece.id];
                  const isSelected = selectedPieceId === actualPiece.id;
                  const row = Math.floor(actualPiece.correctPosition / gridSize);
                  const col = actualPiece.correctPosition % gridSize;

                  return (
                    <div
                      key={positionIdx}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, positionIdx)}
                      onClick={() => handlePieceClick(actualPiece)}
                      className={`relative flex items-center justify-center overflow-hidden rounded-lg cursor-pointer transition-all duration-200 select-none ${
                        isSelected
                          ? 'ring-4 ring-cyan-400 scale-[1.03] z-10 shadow-cyan-500/50 shadow-lg'
                          : isSolved
                          ? 'border border-emerald-500/50 shadow-sm'
                          : 'border border-white/10 hover:border-indigo-400 hover:scale-[1.02]'
                      }`}
                      style={{ width: '100%', height: '100%' }}
                    >
                      {/* Sliced Piece Visual from Original Brand Image */}
                      <div
                        draggable={!isJigsawCompleted}
                        onDragStart={(e) => handleDragStart(e, actualPiece)}
                        className={`absolute inset-0 transition-opacity ${isSolved ? 'opacity-100' : 'opacity-90'}`}
                        style={{
                          backgroundImage: `url("${brandImageSrc}")`,
                          backgroundSize: `${gridSize * 100}% ${gridSize * 100}%`,
                          backgroundPosition: `${gridSize > 1 ? (col / (gridSize - 1)) * 100 : 0}% ${gridSize > 1 ? (row / (gridSize - 1)) * 100 : 0}%`,
                          backgroundRepeat: 'no-repeat',
                          backgroundColor: '#ffffff'
                        }}
                      />

                      {/* Piece Number Badge */}
                      <div className="absolute top-1 left-1 bg-slate-900/75 text-slate-300 rounded px-1.5 py-0.5 text-[9px] font-black pointer-events-none">
                        #{actualPiece.id + 1}
                      </div>

                      {/* Solved Check Badge */}
                      {isSolved && (
                        <div className="absolute top-1 right-1 bg-emerald-500 text-white rounded-full p-1 shadow-lg pointer-events-none">
                          <Award size={10} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Guessing Form */}
            <div className="w-full max-w-lg mt-4">
              <form onSubmit={handleGuess} className="relative flex items-center">
                <input
                  value={userGuess}
                  onChange={e => setUserGuess(e.target.value)}
                  placeholder="Identify the brand or stock (e.g., ITC, Jio, TCS)..."
                  className="w-full bg-slate-900/90 border border-white/15 rounded-2xl px-5 py-3.5 text-white text-sm font-semibold placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-xl transition-all"
                />
                <button
                  type="submit"
                  disabled={isGuessing || !userGuess.trim()}
                  className="absolute right-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-5 py-2 rounded-xl font-black text-xs transition-all shadow-md"
                >
                  {isGuessing ? 'Checking...' : 'Submit Guess'}
                </button>
              </form>

              {dynamicFeedback && (
                <div className="mt-2.5 p-3 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-center text-indigo-200 font-bold text-xs animate-in fade-in duration-200">
                  {dynamicFeedback}
                </div>
              )}

              <div className="flex justify-between items-center mt-2 px-3 text-[10px] font-black uppercase text-slate-400 tracking-wider">
                <span>Attempts: {attempts}/3</span>
                <span className="text-emerald-400">Score Potential: {calculateScore(moves, attempts + 1)} pts</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(25px, -40px) scale(1.08); }
          66% { transform: translate(-20px, 20px) scale(0.95); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob { animation: blob 15s infinite alternate ease-in-out; }
        .animation-delay-4000 { animation-delay: 4s; }
      `}} />
    </div>
  );
}
