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
  const [puzzleMode, setPuzzleMode] = useState('stock'); // 'logo' or 'stock'
  const [difficulty, setDifficulty] = useState(null);
  const [currentBrand, setCurrentBrand] = useState(null);
  const [dbPuzzleId, setDbPuzzleId] = useState(null);
  const [completedToday, setCompletedToday] = useState(false);
  const [selectionMethod, setSelectionMethod] = useState(null);
  const [voteCount, setVoteCount] = useState(0);
  const [mergedPuzzleUrl, setMergedPuzzleUrl] = useState('');

  const [pieces, setPieces] = useState([]);
  const [solvedPositions, setSolvedPositions] = useState({});
  const [draggedPiece, setDraggedPiece] = useState(null);
  const [timer, setTimer] = useState(0);
  const [boardSize, setBoardSize] = useState(300);
  const [boardHeight, setBoardHeight] = useState(300);
  const boardContainerRef = useRef(null);
  const boardParentRef = useRef(null);

  const [puzzleFeedback, setPuzzleFeedback] = useState(null);
  const [logoFeedback, setLogoFeedback] = useState(null);
  const [teacherInsight, setTeacherInsight] = useState(null);
  const [isFetchingInsight, setIsFetchingInsight] = useState(false);

  const [moves, setMoves] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [streak, setStreak] = useState(0);
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);

  // Clues & Guessing
  const [wordCloud, setWordCloud] = useState('');
  const [clues, setClues] = useState({});
  const [currentClueIdx, setCurrentClueIdx] = useState(1);
  const [userGuess, setUserGuess] = useState('');
  const [dynamicFeedback, setDynamicFeedback] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [isGuessing, setIsGuessing] = useState(false);
  const [isJigsawCompleted, setIsJigsawCompleted] = useState(false);
  const [isGuessPhase, setIsGuessPhase] = useState(false);

  const timerRef = useRef(null);

  const difficultyLevels = {
    easy: { grid: 3, pieces: 9, label: 'Easy' },
    medium: { grid: 4, pieces: 16, label: 'Medium' },
    hard: { grid: 5, pieces: 25, label: 'Hard' }
  };

  useEffect(() => {
    const updateSize = () => {
      if (boardParentRef.current) {
        const { width, height } = boardParentRef.current.getBoundingClientRect();
        const size = Math.min(width - 16, height - 16, 1000);
        setBoardSize(size);
        setBoardHeight(puzzleMode === 'stock' ? size * 0.75 : size); // 4:3 for stock
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [gameState, showHint, puzzleMode]);

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
    }, 10000);

    try {
      const { data } = await axios.get('/api/puzzles/daily');
      if (data) {
        setDbPuzzleId(data.id);
        setSelectionMethod(data.selectionMethod);
        setVoteCount(data.voteCount || 0);

        try {
          const clueResponse = await axios.get(`/api/puzzles/${data.id}/clues`);
          if (clueResponse.data?.success) {
            setWordCloud(clueResponse.data.clues.wordCloud);
            setClues(clueResponse.data.clues);
            setMergedPuzzleUrl(clueResponse.data.clues.mergedPuzzleSvg);
          }
        } catch (e) {
          console.error("Failed to fetch clues", e);
        }

        const matchedBrand = NIFTY50_BRANDS.find(b => b.ticker === data.ticker) || NIFTY50_BRANDS[0];
        setCurrentBrand(matchedBrand);
      }

      if (user) {
        setStreak(user.streak || 0);
        setScore(user.score || 0);
        setBestScore(user.bestScore || 0);
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
    setAttempts(0);
    setUserGuess('');
    setDynamicFeedback('');
    setCurrentClueIdx(1);

    const gridSize = difficultyLevels[diff].grid;
    const puzzlePieces = [];
    for (let i = 0; i < gridSize * gridSize; i++) {
      puzzlePieces.push({ id: i, correctPosition: i, currentPosition: i });
    }
    // Shuffle
    for (let i = puzzlePieces.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [puzzlePieces[i].currentPosition, puzzlePieces[j].currentPosition] = [puzzlePieces[j].currentPosition, puzzlePieces[i].currentPosition];
    }
    setPieces(puzzlePieces);
    setGameState('playing');
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

    const newPieces = [...pieces];
    const draggedPieceObj = newPieces.find(p => p.id === draggedPiece.id);
    const targetPieceObj = newPieces.find(p => p.currentPosition === targetPosition);

    if (draggedPieceObj && targetPieceObj && draggedPieceObj.id !== targetPieceObj.id) {
      [draggedPieceObj.currentPosition, targetPieceObj.currentPosition] = [targetPieceObj.currentPosition, draggedPieceObj.currentPosition];
      setPieces(newPieces);
      const newMoves = moves + 1;
      setMoves(newMoves);

      const newSolved = {};
      newPieces.forEach(piece => {
        if (piece.correctPosition === piece.currentPosition) newSolved[piece.id] = true;
      });
      setSolvedPositions(newSolved);

      if (Object.keys(newSolved).length === newPieces.length) {
        setIsJigsawCompleted(true);
        if (puzzleMode === 'stock') {
          setIsGuessPhase(true);
          setDynamicFeedback('Vision reconstructed! Now, identify the stock in the terminal clues.');
        } else {
          // Logo puzzle completed
          setTimeout(() => completeGame(moves, attempts), 1000);
        }
      }
    }
    setDraggedPiece(null);
  };

  const handleGuess = async (e) => {
    if (e) e.preventDefault();
    if (!userGuess.trim() || attempts >= 3 || isGuessing) return;

    setIsGuessing(true);
    try {
      const { data } = await axios.post(`/api/puzzles/${dbPuzzleId}/guess`, { guess: userGuess });
      setDynamicFeedback(data.feedback);
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);

      if (data.isCorrect) {
        setDynamicFeedback('BINGO! You identified the giant. Final Challenge: Reconstruct the Official Logo!');
        setTimeout(() => {
          setPuzzleMode('logo');
          setIsJigsawCompleted(false);
          setIsGuessPhase(false);
          setUserGuess('');
          // Re-generate pieces for logo
          fetchDaily();
        }, 1500);
      } else {
        if (currentClueIdx < 3) setCurrentClueIdx(prev => prev + 1);
        if (newAttempts >= 3) {
          setDynamicFeedback('3 unsuccessful attempts. Revealing the answer in 2 seconds...');
          setTimeout(() => completeGame(moves, newAttempts), 2500);
        }
      }
    } catch (error) {
      console.error('Failed to evaluate guess', error);
      setDynamicFeedback('Unable to check your guess right now.');
    } finally {
      setIsGuessing(false);
    }
  };

  const completeGame = async (finalMoves, finalAttempts) => {
    if (timerRef.current) clearInterval(timerRef.current);
    const gameScore = calculateScore(finalMoves, finalAttempts);
    setGameState('completed');
    setCompletedToday(true);
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
        setStreak(data.streak);
        setScore(data.realTotal || score + gameScore);
        if (gameScore > bestScore) setBestScore(gameScore);
      }
    } catch (e) { console.error('Failed to save result', e); }
  };

  const fetchTeacherInsight = async () => {
    if (!dbPuzzleId) return;
    setIsFetchingInsight(true);
    try {
      const response = await axios.get(`/api/puzzles/${dbPuzzleId}/insight`);
      if (response.data?.insight) setTeacherInsight(response.data.insight);
    } catch (e) { console.error('Failed AI insight', e); }
    finally { setIsFetchingInsight(false); }
  };

  const calculateScore = (finalMoves, finalAttempts) => {
    let points = 0;
    if (finalAttempts === 1) points = 10;
    else if (finalAttempts === 2) points = 7;
    else if (finalAttempts === 3) points = 5;
    return points * 100 + (difficultyLevels[difficulty]?.grid * 50 || 0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (gameState === 'loading') return <div className="flex items-center justify-center min-h-screen text-white font-bold bg-[#030014]">Loading challenge...</div>;

  if (gameState === 'menu') {
    return (
      <div className="fixed inset-0 top-[65px] bg-[#030014] p-4 flex items-center justify-center overflow-hidden h-[calc(100vh-65px)]">
         <div className="absolute inset-0 z-0 opacity-40 pointer-events-none transform scale-110">
          <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/20 blur-[150px] mix-blend-screen animate-blob" />
          <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-cyan-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
        </div>
        <div className="max-w-6xl w-full relative z-10 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">Market Puzzle</h1>
          <p className="text-xl text-white/90 mb-8 font-medium">Reconstruct the terminal and identify the mystery stock!</p>

          <div className="bg-white/10 backdrop-blur-xl border border-white/10 rounded-3xl p-8 mb-8 shadow-2xl">
             <div className="flex justify-center gap-8 mb-8">
                <div className="text-white">
                   <div className="text-sm uppercase tracking-widest text-white/50 mb-1">Streak</div>
                   <div className="text-2xl font-black">{streak} Days</div>
                </div>
                <div className="text-white">
                   <div className="text-sm uppercase tracking-widest text-white/50 mb-1">Score</div>
                   <div className="text-2xl font-black">{score}</div>
                </div>
             </div>
             <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
               {Object.entries(difficultyLevels).map(([key, value]) => (
                 <button key={key} onClick={() => startGame(key)} className="bg-white/10 hover:bg-white/20 text-white p-6 rounded-2xl font-bold border border-white/5 transition-all">
                    {value.label}
                    <div className="text-xs opacity-60">{value.pieces} pieces</div>
                 </button>
               ))}
             </div>
          </div>
        </div>
      </div>
    );
  }

  if (gameState === 'completed') {
    return (
      <div className="fixed inset-0 top-[65px] bg-[#030014] p-4 flex items-center justify-center overflow-auto h-[calc(100vh-65px)]">
        <div className="max-w-4xl w-full bg-white rounded-[2.5rem] p-8 text-center shadow-2xl border border-white/20">
           <div className="mb-8">
              <div className="text-5xl mb-4">🏆</div>
              <h2 className="text-4xl font-black text-slate-800 tracking-tight">Challenge Mastered!</h2>
              <div className="text-indigo-600 font-bold uppercase tracking-widest text-sm mt-2">You Identified {currentBrand?.brand}</div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="bg-slate-50 p-8 rounded-3xl border border-slate-100 flex flex-col items-center justify-center">
                 <div className="w-24 h-24 mb-4" dangerouslySetInnerHTML={{ __html: currentBrand?.logoSvg }} />
                 <h3 className="text-2xl font-black text-slate-800">{currentBrand?.brand}</h3>
                 <p className="text-slate-500 font-medium text-sm mt-2">{currentBrand?.insight}</p>
              </div>
              <div className="bg-indigo-50 p-8 rounded-3xl border border-indigo-100 text-left">
                  <div className="text-sm font-black text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                     <Lightbulb size={18} /> Teacher Insight
                  </div>
                  {isFetchingInsight ? (
                    <div className="animate-pulse h-20 bg-indigo-200/50 rounded-xl" />
                  ) : (
                    <p className="text-indigo-900 font-medium leading-relaxed">{teacherInsight?.insight || 'Loading expert analysis...'}</p>
                  )}
              </div>
           </div>

           <button onClick={() => setGameState('menu')} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-black text-lg transition-all shadow-xl">
             Play Next Challenge
           </button>
        </div>
      </div>
    );
  }

  const gridSize = difficultyLevels[difficulty]?.grid || 3;

  return (
    <div className="fixed inset-0 top-[65px] bg-[#030014] p-2 sm:p-4 flex items-center justify-center overflow-hidden h-[calc(100vh-65px)]">
        <div className="absolute inset-0 z-0 opacity-40">
          <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-blue-600/10 blur-[150px] animate-blob" />
          <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-indigo-600/10 blur-[150px] animate-blob animation-delay-4000" />
        </div>

        <div ref={boardParentRef} className="max-w-6xl w-full h-full flex flex-col items-center justify-center relative z-10">
           <div className="w-full flex items-center justify-between mb-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/5 shadow-xl text-white">
              <div className="flex items-center gap-4">
                 <div className="flex items-center gap-2 font-black text-sm uppercase tracking-widest"><Clock size={16}/> {formatTime(timer)}</div>
                 <div className="flex items-center gap-2 font-black text-sm uppercase tracking-widest"><Move size={16}/> {moves}</div>
              </div>
              <button onClick={() => setGameState('menu')} className="p-2 hover:bg-white/10 rounded-xl transition-colors"><X size={24}/></button>
           </div>

           <div className="relative flex-1 w-full flex flex-col md:flex-row gap-4 min-h-0 items-center justify-center">

              <div className="w-full md:w-1/4 flex flex-col gap-4 order-2 md:order-1">
                 <div className="bg-white/5 backdrop-blur-md p-6 rounded-3xl border border-white/10 shadow-xl overflow-hidden">
                    <div className="text-[10px] font-black text-indigo-300 uppercase tracking-widest mb-4 flex items-center gap-2"><TrendingUp size={14} /> Terminal Intelligence</div>
                    <div className="space-y-3">
                       {[1, 2, 3].map(idx => (
                         <div key={idx} className={`p-4 rounded-2xl text-xs leading-relaxed transition-all ${idx <= currentClueIdx ? 'bg-indigo-600/30 border border-indigo-500/30 text-indigo-50' : 'bg-white/5 text-white/20 border-transparent'}`}>
                            <div className="font-black uppercase tracking-tighter text-[9px] mb-1 opacity-60">Phase {idx} Clue</div>
                            {idx <= currentClueIdx ? clues[`clue${idx}`] : 'Locked'}
                         </div>
                       ))}
                    </div>
                 </div>

                 {isGuessPhase && (
                    <div className="bg-white/5 backdrop-blur-md p-4 rounded-3xl border border-indigo-500/30 shadow-xl animate-in fade-in slide-in-from-left-5">
                       <div className="text-[9px] font-black text-indigo-300 uppercase tracking-widest mb-2 px-2 flex items-center gap-2"><Lightbulb size={12}/> Identify Brand</div>
                       <form onSubmit={handleGuess} className="relative">
                          <input
                             value={userGuess}
                             onChange={e => setUserGuess(e.target.value)}
                             placeholder="Stock name..."
                             className="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-2 text-white text-xs placeholder:text-white/20 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all"
                          />
                          <button type="submit" disabled={isGuessing} className="absolute right-1 top-1 bottom-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 rounded-lg font-black text-[10px] transition-all">
                             {isGuessing ? "..." : "GO"}
                          </button>
                       </form>
                    </div>
                 )}
              </div>

              <div className="flex-1 w-full h-full flex flex-col items-center justify-center order-1 md:order-2">
                 <div
                    ref={boardContainerRef}
                    className="grid bg-slate-900/50 backdrop-blur-sm rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/5"
                    style={{ gridTemplateColumns: `repeat(${gridSize}, 1fr)`, gridTemplateRows: `repeat(${gridSize}, 1fr)`, width: boardSize, height: boardHeight, gap: '0px', padding: '0px' }}
                   >
                    {pieces.map((piece, positionIdx) => {
                      const actualPiece = pieces.find(p => p.currentPosition === positionIdx);
                      const isSolved = solvedPositions[actualPiece.id];
                      const row = Math.floor(actualPiece.correctPosition / gridSize);
                      const col = actualPiece.correctPosition % gridSize;

                      return (
                        <div key={positionIdx} onDragOver={handleDragOver} onDrop={(e) => handleDrop(e, positionIdx)} className={`relative flex items-center justify-center overflow-hidden transition-all duration-300 ${!isJigsawCompleted ? 'hover:z-10 hover:scale-[1.02]' : ''}`} style={{ width: '100%', height: '100%' }}>
                           <div draggable onDragStart={(e) => handleDragStart(e, actualPiece)} className={`absolute inset-0 cursor-grab active:cursor-grabbing ${isSolved ? 'opacity-100' : 'opacity-90'}`} style={{
                             backgroundImage: `url("${mergedPuzzleUrl}")`,
                             backgroundSize: `${gridSize * 100}% ${gridSize * 100}%`,
                             backgroundPosition: `${gridSize > 1 ? (col / (gridSize - 1)) * 100 : 0}% ${gridSize > 1 ? (row / (gridSize - 1)) * 100 : 0}%`,
                             backgroundRepeat: 'no-repeat'
                           }} />
                           {isSolved && <div className="absolute top-1 right-1 bg-green-500 text-white rounded-full p-1 shadow-2xl"><Award size={10}/></div>}
                        </div>
                      )
                    })}
                 </div>

                 {isGuessPhase && (
                   <div className="w-full max-w-lg mt-6 animate-in fade-in slide-in-from-bottom-5 duration-500">
                      <form onSubmit={handleGuess} className="relative">
                         <input value={userGuess} onChange={e => setUserGuess(e.target.value)} placeholder="Analyze the word cloud. Identify the stock..." className="w-full bg-slate-900/80 border border-white/10 rounded-2xl px-6 py-4 text-white font-bold placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all shadow-2xl" />
                         <button type="submit" disabled={isGuessing} className="absolute right-2 top-2 bottom-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 rounded-xl font-black text-sm transition-all shadow-lg">{isGuessing ? "Refining..." : "Guess!"}</button>
                      </form>
                      {dynamicFeedback && <div className="mt-4 p-4 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-center text-indigo-300 font-bold text-sm animate-pulse">📢 {dynamicFeedback}</div>}
                      <div className="flex justify-between mt-2 px-2 text-[10px] font-black uppercase text-white/30 tracking-widest">
                         <span>Attempts: {attempts}/3</span>
                         <span className="text-indigo-400">Reward Potential: {calculateScore(moves, attempts+1)} pts</span>
                      </div>
                   </div>
                 )}
              </div>
           </div>
        </div>

        <style dangerouslySetInnerHTML={{ __html: `
          @keyframes blob {
            0% { transform: translate(0px, 0px) scale(1); }
            33% { transform: translate(30px, -50px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
            100% { transform: translate(0px, 0px) scale(1); }
          }
          .animate-blob { animation: blob 15s infinite alternate ease-in-out; }
          .animation-delay-4000 { animation-delay: 4s; }
          *::-webkit-scrollbar { display: none; }
          * { scrollbar-width: none; }
        `}} />
    </div>
  );
}
