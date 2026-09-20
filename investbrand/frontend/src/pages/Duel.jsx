import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Swords, Trophy, Shield, Zap, Clock, Move, ArrowRight,
  Sparkles, Check, X, RefreshCw, Copy, Share2, HelpCircle,
  TrendingUp, TrendingDown, Volume2, VolumeX, Send, Flame
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function DuelArena() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { roomCode: urlRoomCode } = useParams();

  // ── Connection & Room State ────────────────────────────────────────────────
  const [stage, setStage] = useState('lobby'); // lobby, matching, countdown, arena, results
  const [roomCode, setRoomCode] = useState(urlRoomCode || '');
  const [joinCodeInput, setJoinCodeInput] = useState('');
  const [playerName, setPlayerName] = useState(user?.name || `Trader_${Math.floor(Math.random() * 900 + 100)}`);
  const [playerId, setPlayerId] = useState(null);
  const [playerRole, setPlayerRole] = useState('bull'); // 'bull' (Host) or 'bear' (Challenger)
  const [isHost, setIsHost] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // ── Opponent State ────────────────────────────────────────────────────────
  const [opponent, setOpponent] = useState(null);
  const [opponentProgress, setOpponentProgress] = useState(0);
  const [opponentSolvedCount, setOpponentSolvedCount] = useState(0);
  const [opponentClueIdx, setOpponentClueIdx] = useState(1);
  const [opponentMoves, setOpponentMoves] = useState(0);

  // ── Puzzle Board State ─────────────────────────────────────────────────────
  const [pieces, setPieces] = useState([]);
  const [solvedPositions, setSolvedPositions] = useState({});
  const [draggedPiece, setDraggedPiece] = useState(null);
  const [selectedPieceId, setSelectedPieceId] = useState(null);
  const [boardSize, setBoardSize] = useState(380);
  const [gridSize, setGridSize] = useState(3);
  const [moves, setMoves] = useState(0);
  const [currentBrand, setCurrentBrand] = useState(null);
  const [clues, setClues] = useState({});
  const [currentClueIdx, setCurrentClueIdx] = useState(1);
  const [userGuess, setUserGuess] = useState('');
  const [feedback, setFeedback] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [isSubmittingGuess, setIsSubmittingGuess] = useState(false);

  // ── Match Timer & Battle Feed ──────────────────────────────────────────────
  const [countdown, setCountdown] = useState(3);
  const [matchTimer, setMatchTimer] = useState(90);
  const [battleFeed, setBattleFeed] = useState([]);
  const [floatingEmojis, setFloatingEmojis] = useState([]);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // ── Results State ──────────────────────────────────────────────────────────
  const [matchResult, setMatchResult] = useState(null); // { winnerId, winnerName, winnerRole, brand, endReason }
  const [rematchRequested, setRematchRequested] = useState(false);
  const [opponentRematch, setOpponentRematch] = useState(false);

  // ── References ─────────────────────────────────────────────────────────────
  const wsRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const boardParentRef = useRef(null);
  const playerIdRef = useRef(null);
  const roomCodeRef = useRef(null);

  // Auto-fill player name if user auth updates
  useEffect(() => {
    if (user?.name) {
      setPlayerName(user.name);
    }
  }, [user]);

  // Handle URL room code parameter
  useEffect(() => {
    if (urlRoomCode) {
      setJoinCodeInput(urlRoomCode.toUpperCase());
    }
  }, [urlRoomCode]);

  // Adjust puzzle board dimensions dynamically
  useEffect(() => {
    const handleResize = () => {
      if (boardParentRef.current) {
        const { width, height } = boardParentRef.current.getBoundingClientRect();
        const available = Math.min(width - 24, height - 80, 480);
        setBoardSize(Math.max(260, available));
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [stage]);

  // ── Web Audio Synthesizer (Bells, Buzzers, Snaps) ──────────────────────────
  const playSfx = (type) => {
    if (!soundEnabled) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'bell') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.8);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
        osc.start();
        osc.stop(ctx.currentTime + 0.8);
      } else if (type === 'snap') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(320, ctx.currentTime);
        osc.frequency.setValueAtTime(580, ctx.currentTime + 0.05);
        gain.gain.setValueAtTime(0.2, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      } else if (type === 'victory') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15);
        osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3);
        osc.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.45);
        gain.gain.setValueAtTime(0.25, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.9);
        osc.start();
        osc.stop(ctx.currentTime + 0.9);
      } else if (type === 'wrong') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(200, ctx.currentTime);
        osc.frequency.setValueAtTime(140, ctx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
      }
    } catch (e) {
      // Audio context might be restricted before user gesture
    }
  };

  // ── Universal API & WebSocket Setup ─────────────────────────────────────────
  const getApiBase = () => {
    return window.location.port === '3000' ? 'http://127.0.0.1:8080' : '';
  };

  const apiPost = async (endpoint, payload) => {
    const base = getApiBase();
    try {
      return await axios.post(`${base}/api/v1/investbrand${endpoint}`, payload);
    } catch (e) {
      return await axios.post(`${base}/api${endpoint}`, payload);
    }
  };

  const connectWebSocket = (targetRoomCode, targetPlayerId) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isDev = window.location.port === '3000';
    const host = isDev ? `${window.location.hostname}:8080` : window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/investbrand/ws/duel/${targetRoomCode}?playerId=${targetPlayerId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      addBattleLog('⚡ Connected to Bull vs Bear Duel Server');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      addBattleLog('⚠️ Connection error. Trying to reconnect...');
    };

    ws.onclose = () => {
      addBattleLog('🔌 Disconnected from Duel Arena.');
    };
  };

  // ── Handle Server Messages ─────────────────────────────────────────────────
  const handleServerMessage = (msg) => {
    switch (msg.type) {
      case 'CONNECTED': {
        if (msg.room?.players) {
          updatePlayersFromRoom(msg.room.players);
        }
        break;
      }

      case 'OPPONENT_JOINED': {
        addBattleLog(`🐂 ${msg.newPlayer?.name || 'Challenger'} entered the arena!`);
        if (msg.room?.players) {
          updatePlayersFromRoom(msg.room.players);
        }
        playSfx('bell');
        break;
      }

      case 'PLAYER_READY_UPDATE': {
        if (msg.players) {
          updatePlayersFromRoom(msg.players);
        }
        break;
      }

      case 'MATCH_START': {
        playSfx('bell');
        setMatchResult(null);
        setRematchRequested(false);
        setOpponentRematch(false);
        setFeedback('');
        setAttempts(0);
        setUserGuess('');
        setMoves(0);
        setSelectedPieceId(null);

        const room = msg.room;
        if (room) {
          setCurrentBrand(room.brand);
          setClues(room.clues || {});
          setGridSize(room.gridSize || 3);
          setMatchTimer(room.matchDurationSeconds || 90);

          // Initialize pieces
          const initialPieces = room.pieces || [];
          setPieces(initialPieces);

          const initialSolved = {};
          initialPieces.forEach(p => {
            if (p.correctPosition === p.currentPosition) initialSolved[p.id] = true;
          });
          setSolvedPositions(initialSolved);
        }

        // Trigger 3s countdown
        setStage('countdown');
        let count = 3;
        setCountdown(3);
        const countInterval = setInterval(() => {
          count -= 1;
          if (count > 0) {
            setCountdown(count);
          } else {
            clearInterval(countInterval);
            setStage('arena');
            startMatchTimer();
          }
        }, 1000);
        break;
      }

      case 'OPPONENT_PROGRESS': {
        setOpponentProgress(msg.progress || 0);
        setOpponentSolvedCount(msg.solvedCount || 0);
        setOpponentClueIdx(msg.currentClueIdx || 1);
        setOpponentMoves(msg.moves || 0);

        if (msg.currentClueIdx > opponentClueIdx) {
          addBattleLog(`🔍 Opponent unlocked Clue #${msg.currentClueIdx}!`);
        }
        break;
      }

      case 'GUESS_RESPONSE': {
        setIsSubmittingGuess(false);
        if (msg.isCorrect) {
          playSfx('victory');
          setFeedback(msg.message || '🎯 CORRECT GUESS!');
        } else {
          playSfx('wrong');
          setFeedback(msg.message || '❌ Incorrect guess!');
        }
        break;
      }

      case 'GUESS_FEEDBACK': {
        addBattleLog(`🎯 ${msg.feedback}`);
        break;
      }

      case 'REACTION': {
        triggerFloatingEmoji(msg.emoji, msg.role === playerRole ? 'player' : 'opponent');
        break;
      }

      case 'MATCH_OVER': {
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
        }
        setMatchResult(msg);
        setStage('results');
        if (msg.winnerId === playerId) {
          playSfx('victory');
        } else {
          playSfx('wrong');
        }
        break;
      }

      case 'REMATCH_REQUESTED': {
        if (msg.playerId !== playerId) {
          setOpponentRematch(true);
          addBattleLog(`🔄 ${msg.playerName} requested a rematch!`);
        }
        break;
      }

      case 'PLAYER_LEFT': {
        addBattleLog(`👋 ${msg.playerName || 'Player'} left the arena.`);
        setOpponent(null);
        setIsReady(false);
        break;
      }

      default:
        break;
    }
  };

  const updatePlayersFromRoom = (playersObj, currentPid) => {
    const myId = currentPid || playerIdRef.current;
    let foundOpp = null;
    if (playersObj) {
      Object.values(playersObj).forEach(p => {
        if (p.playerId === myId) {
          setIsReady(p.ready);
          setPlayerRole(p.role || 'bull');
        } else {
          foundOpp = p;
        }
      });
    }
    setOpponent(foundOpp);
  };

  const addBattleLog = (text) => {
    setBattleFeed(prev => [
      { id: Date.now() + Math.random(), text, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) },
      ...prev.slice(0, 25)
    ]);
  };

  const triggerFloatingEmoji = (emoji, source) => {
    const id = Date.now() + Math.random();
    setFloatingEmojis(prev => [...prev, { id, emoji, source }]);
    setTimeout(() => {
      setFloatingEmojis(prev => prev.filter(e => e.id !== id));
    }, 2000);
  };

  const startMatchTimer = () => {
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    timerIntervalRef.current = setInterval(() => {
      setMatchTimer(prev => {
        if (prev <= 1) {
          clearInterval(timerIntervalRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // ── Lobby Actions: Create, Join, Quick Match ──────────────────────────────
  const handleCreateRoom = async () => {
    try {
      const { data } = await apiPost('/puzzles/duel/create', {
        name: playerName,
        avatar: user?.avatar || '',
        difficulty: 'easy'
      });
      if (data.success) {
        setRoomCode(data.roomCode);
        roomCodeRef.current = data.roomCode;
        setPlayerId(data.playerId);
        playerIdRef.current = data.playerId;
        setPlayerRole('bull');
        setIsHost(true);
        setIsReady(false);
        setOpponent(null);
        connectWebSocket(data.roomCode, data.playerId);
        setStage('lobby_waiting');
        addBattleLog(`🛡️ Arena #${data.roomCode} created. Share the code with your rival!`);
      }
    } catch (err) {
      console.error('Failed to create duel room', err);
      alert('Failed to create duel room. Please ensure the backend server is running.');
    }
  };

  const handleJoinRoom = async () => {
    if (!joinCodeInput.trim()) return;
    try {
      const targetCode = joinCodeInput.trim().toUpperCase();
      const { data } = await apiPost('/puzzles/duel/join', {
        roomCode: targetCode,
        name: playerName,
        avatar: user?.avatar || ''
      });
      if (data.success) {
        setRoomCode(data.roomCode);
        roomCodeRef.current = data.roomCode;
        setPlayerId(data.playerId);
        playerIdRef.current = data.playerId;
        setPlayerRole('bear');
        setIsHost(false);
        setIsReady(false);
        if (data.room?.players) {
          updatePlayersFromRoom(data.room.players, data.playerId);
        }
        connectWebSocket(data.roomCode, data.playerId);
        setStage('lobby_waiting');
        addBattleLog(`⚔️ Joined Arena #${data.roomCode}. Ready up for battle!`);
      }
    } catch (err) {
      console.error('Failed to join room', err);
      alert(err.response?.data?.detail || 'Failed to join arena. Check room code.');
    }
  };

  const handleQuickMatch = async () => {
    setStage('matching');
    try {
      const { data } = await apiPost('/puzzles/duel/quick-match', {
        name: playerName,
        avatar: user?.avatar || ''
      });
      if (data.success) {
        setRoomCode(data.roomCode);
        roomCodeRef.current = data.roomCode;
        setPlayerId(data.playerId);
        playerIdRef.current = data.playerId;
        setPlayerRole(data.matched ? 'bear' : 'bull');
        setIsHost(!data.matched);
        setIsReady(false);
        if (data.room?.players) {
          updatePlayersFromRoom(data.room.players, data.playerId);
        }
        connectWebSocket(data.roomCode, data.playerId);
        setStage('lobby_waiting');
        if (data.matched) {
          addBattleLog('🎯 Matched with an active trader! Ready up!');
        } else {
          addBattleLog('⏳ Waiting for an opponent to join your arena...');
        }
      }
    } catch (err) {
      console.error('Quick match error', err);
      setStage('lobby');
      alert('Quick Match failed. Try creating a private arena.');
    }
  };

  const handleToggleReady = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'READY' }));
      setIsReady(true);
      playSfx('snap');
    }
  };

  // ── Puzzle Tile Swap Logic ─────────────────────────────────────────────────
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
      playSfx('snap');

      const newSolved = {};
      newPieces.forEach(p => {
        if (p.correctPosition === p.currentPosition) newSolved[p.id] = true;
      });
      setSolvedPositions(newSolved);

      const solvedCount = Object.keys(newSolved).length;
      let nextClue = currentClueIdx;
      if (solvedCount >= Math.floor(newPieces.length * 0.4) && currentClueIdx < 2) {
        nextClue = 2;
        setCurrentClueIdx(2);
      }
      if (solvedCount >= Math.floor(newPieces.length * 0.7) && currentClueIdx < 3) {
        nextClue = 3;
        setCurrentClueIdx(3);
      }

      // Broadcast move update to opponent over WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'MOVE_UPDATE',
          solvedCount,
          currentClueIdx: nextClue,
          moves: newMoves
        }));
      }
    }
  };

  const handlePieceClick = (piece) => {
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
    const targetPieceObj = pieces.find(p => p.currentPosition === targetPosition);
    if (targetPieceObj) {
      swapPieces(draggedPiece.id, targetPieceObj.id);
    }
    setDraggedPiece(null);
    setSelectedPieceId(null);
  };

  // ── Guess Submission ───────────────────────────────────────────────────────
  const handleGuessSubmit = (e) => {
    if (e) e.preventDefault();
    if (!userGuess.trim() || attempts >= 3 || isSubmittingGuess) return;

    setIsSubmittingGuess(true);
    setAttempts(prev => prev + 1);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'SUBMIT_GUESS',
        guess: userGuess.trim()
      }));
    }
  };

  const sendReaction = (emoji) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'REACTION',
        emoji
      }));
      triggerFloatingEmoji(emoji, 'player');
    }
  };

  const handleRequestRematch = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'REMATCH' }));
      setRematchRequested(true);
      playSfx('snap');
    }
  };

  // Helper for brand image / svg
  const getBrandImageSrc = (brand) => {
    if (!brand) return '';
    if (brand.logoSvg && brand.logoSvg.trim().startsWith('<svg')) {
      return `data:image/svg+xml;utf8,${encodeURIComponent(brand.logoSvg.trim())}`;
    }
    if (brand.ticker) {
      return `/investbrand/logos/${brand.ticker}.png`;
    }
    return '';
  };

  const brandImageSrc = getBrandImageSrc(currentBrand);
  const totalPieces = gridSize * gridSize;
  const mySolvedCount = Object.keys(solvedPositions).length;
  const myProgress = Math.round((mySolvedCount / totalPieces) * 100);

  // ═════════════════════════════════════════════════════════════════════════════
  // VIEW 1: LOBBY VIEW (Create / Join / Quick Match)
  // ═════════════════════════════════════════════════════════════════════════════
  if (stage === 'lobby' || stage === 'matching') {
    return (
      <div className="min-h-[calc(100vh-65px)] bg-[#030014] text-white p-4 flex items-center justify-center relative overflow-hidden">
        {/* Ambient Glows */}
        <div className="absolute top-10 left-10 w-96 h-96 bg-emerald-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-rose-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-xl w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 backdrop-blur-xl relative z-10 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-black uppercase tracking-widest mb-3">
              <Swords size={14} /> 1v1 Real-Time Multiplayer
            </div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white mb-2 flex items-center justify-center gap-3">
              <span className="text-emerald-400">Bull</span>
              <span className="text-slate-500 text-2xl font-light">vs</span>
              <span className="text-rose-400">Bear</span>
            </h1>
            <p className="text-slate-400 text-sm">
              Race in real-time to reconstruct the brand logo and identify the mystery stock before your rival!
            </p>
          </div>

          {/* Player Name Input */}
          <div className="mb-6 bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              Your Trader Alias
            </label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-white font-semibold outline-none transition-colors"
              placeholder="Enter your name"
              maxLength={20}
            />
          </div>

          {/* Action Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Create Arena */}
            <button
              onClick={handleCreateRoom}
              className="p-5 bg-gradient-to-br from-emerald-950/40 to-slate-900 border border-emerald-500/30 hover:border-emerald-400/60 rounded-2xl text-left transition-all hover:scale-[1.02] active:scale-[0.98] group"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Shield size={20} />
              </div>
              <h3 className="font-bold text-white text-base mb-1 flex items-center justify-between">
                Host Private Arena
                <ArrowRight size={16} className="text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </h3>
              <p className="text-xs text-slate-400">Get a 6-letter room code to invite a friend or coworker.</p>
            </button>

            {/* Quick Match */}
            <button
              onClick={handleQuickMatch}
              className="p-5 bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/30 hover:border-indigo-400/60 rounded-2xl text-left transition-all hover:scale-[1.02] active:scale-[0.98] group"
            >
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Zap size={20} />
              </div>
              <h3 className="font-bold text-white text-base mb-1 flex items-center justify-between">
                Quick Match
                <ArrowRight size={16} className="text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </h3>
              <p className="text-xs text-slate-400">Instant matchmaking queue with any available trader.</p>
            </button>
          </div>

          {/* Join With Code */}
          <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex gap-2">
            <input
              type="text"
              value={joinCodeInput}
              onChange={(e) => setJoinCodeInput(e.target.value.toUpperCase())}
              placeholder="ENTER 6-LETTER ROOM CODE"
              maxLength={8}
              className="flex-1 bg-slate-900 border border-slate-700 focus:border-rose-500 rounded-xl px-4 py-2.5 text-white font-mono uppercase font-bold tracking-widest text-center outline-none"
            />
            <button
              onClick={handleJoinRoom}
              className="px-6 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition-all hover:scale-105 active:scale-95"
            >
              Join
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════════
  // VIEW 2: LOBBY WAITING ROOM (Ready Check)
  // ═════════════════════════════════════════════════════════════════════════════
  if (stage === 'lobby_waiting') {
    const inviteLink = `${window.location.origin}/investbrand/duel/${roomCode}`;
    return (
      <div className="min-h-[calc(100vh-65px)] bg-[#030014] text-white p-4 flex items-center justify-center relative">
        <div className="max-w-xl w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 backdrop-blur-xl relative z-10 shadow-2xl">
          {/* Room Code Badge */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 text-slate-300 text-xs font-bold mb-2">
              DUEL ARENA CODE
            </div>
            <div className="flex items-center justify-center gap-3">
              <span className="text-4xl font-black font-mono tracking-widest text-indigo-400 bg-indigo-950/40 px-6 py-2 rounded-2xl border border-indigo-500/30">
                {roomCode}
              </span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(inviteLink);
                  alert('Invite link copied to clipboard!');
                }}
                className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 hover:text-white transition-colors"
                title="Copy Invite Link"
              >
                <Copy size={20} />
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-2">Send this code to your opponent to join.</p>
          </div>

          {/* Versus Matchup Card */}
          <div className="grid grid-cols-2 gap-4 my-8">
            {/* Player (You) */}
            <div className={`p-5 rounded-2xl border ${playerRole === 'bull' ? 'bg-emerald-950/30 border-emerald-500/40' : 'bg-rose-950/30 border-rose-500/40'} text-center`}>
              <div className="text-xs font-black uppercase tracking-wider mb-2 text-slate-400">
                {playerRole === 'bull' ? '🐂 Bull (Host)' : '🐻 Bear (Challenger)'}
              </div>
              <div className="text-lg font-bold text-white mb-2 truncate">{playerName} (You)</div>
              <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${isReady ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                {isReady ? <><Check size={12} /> Ready</> : 'Waiting...'}
              </div>
            </div>

            {/* Opponent */}
            <div className={`p-5 rounded-2xl border ${opponent ? (playerRole === 'bull' ? 'bg-rose-950/30 border-rose-500/40' : 'bg-emerald-950/30 border-emerald-500/40') : 'bg-slate-950/40 border-slate-800'} text-center`}>
              <div className="text-xs font-black uppercase tracking-wider mb-2 text-slate-400">
                {playerRole === 'bull' ? '🐻 Bear (Rival)' : '🐂 Bull (Host)'}
              </div>
              <div className="text-lg font-bold text-white mb-2 truncate">
                {opponent ? opponent.name : 'Waiting for rival...'}
              </div>
              <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${opponent?.ready ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                {opponent ? (opponent.ready ? <><Check size={12} /> Ready</> : 'Waiting...') : 'Empty Slot'}
              </div>
            </div>
          </div>

          {/* Ready Button */}
          <button
            onClick={handleToggleReady}
            disabled={!opponent || isReady}
            className={`w-full py-4 rounded-2xl font-black text-lg uppercase tracking-wider transition-all flex items-center justify-center gap-2 ${
              !opponent
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : isReady
                ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 cursor-default'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {!opponent ? 'Waiting for Rival to Join...' : isReady ? 'Waiting for Match Start...' : 'Ready Up for Battle ⚔️'}
          </button>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════════
  // VIEW 3: 3-SECOND COUNTDOWN
  // ═════════════════════════════════════════════════════════════════════════════
  if (stage === 'countdown') {
    return (
      <div className="min-h-[calc(100vh-65px)] bg-[#030014] text-white flex flex-col items-center justify-center relative">
        <div className="text-center animate-pulse">
          <div className="text-sm font-black tracking-widest text-indigo-400 uppercase mb-4">
            OPENING BELL APPROACHING
          </div>
          <div className="text-8xl md:text-9xl font-black font-mono text-transparent bg-clip-text bg-gradient-to-b from-white to-slate-500">
            {countdown}
          </div>
          <div className="text-lg font-bold text-slate-400 mt-4">
            {playerRole === 'bull' ? '🐂 Bull Desk' : '🐻 Bear Desk'} vs {opponent?.name || 'Rival'}
          </div>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════════
  // VIEW 4: LIVE DUEL ARENA (Match In Progress)
  // ═════════════════════════════════════════════════════════════════════════════
  if (stage === 'arena') {
    const formatTime = (secs) => {
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
      <div className="min-h-[calc(100vh-65px)] bg-[#030014] text-white p-2 md:p-4 flex flex-col">
        {/* Floating Emojis */}
        <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
          {floatingEmojis.map(e => (
            <div
              key={e.id}
              className={`absolute text-4xl animate-bounce transition-all ${e.source === 'player' ? 'left-1/4' : 'right-1/4'} bottom-24`}
            >
              {e.emoji}
            </div>
          ))}
        </div>

        {/* Top Arena Header: Score, Progress, Countdown */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl px-4 py-2.5 mb-3 flex items-center justify-between shadow-xl">
          {/* Your Status */}
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${playerRole === 'bull' ? 'bg-emerald-400' : 'bg-rose-400'} animate-ping`} />
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase">
                {playerRole === 'bull' ? '🐂 You (Bull)' : '🐻 You (Bear)'}
              </div>
              <div className="text-sm font-black text-white">{myProgress}% Solved ({moves} moves)</div>
            </div>
          </div>

          {/* Central Match Timer */}
          <div className="flex items-center gap-2 bg-slate-950 px-4 py-1.5 rounded-xl border border-slate-800 font-mono font-bold text-lg text-amber-400">
            <Clock size={18} />
            <span>{formatTime(matchTimer)}</span>
          </div>

          {/* Opponent Status */}
          <div className="flex items-center gap-3 text-right">
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase">
                {playerRole === 'bull' ? `🐻 ${opponent?.name || 'Bear'}` : `🐂 ${opponent?.name || 'Bull'}`}
              </div>
              <div className="text-sm font-black text-white">{opponentProgress}% Solved ({opponentMoves} moves)</div>
            </div>
            <div className={`w-3 h-3 rounded-full ${playerRole === 'bull' ? 'bg-rose-400' : 'bg-emerald-400'}`} />
          </div>
        </div>

        {/* Main Duel Grid Layout */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0">
          {/* Left / Center: Your Puzzle Canvas & Guess Input (8 Cols) */}
          <div className="lg:col-span-8 flex flex-col gap-3">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex-1 flex flex-col items-center justify-center relative min-h-[360px]" ref={boardParentRef}>
              {/* Sliced Jigsaw Grid */}
              <div
                className="grid gap-1.5 bg-slate-950/80 p-2 rounded-2xl border border-slate-800 shadow-2xl relative select-none"
                style={{
                  gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                  width: `${boardSize}px`,
                  height: `${boardSize}px`
                }}
              >
                {Array.from({ length: totalPieces }).map((_, slotIndex) => {
                  const piece = pieces.find(p => p.currentPosition === slotIndex);
                  if (!piece) return <div key={slotIndex} className="bg-slate-900/50 rounded-lg" />;

                  const isSolved = piece.correctPosition === piece.currentPosition;
                  const isSelected = selectedPieceId === piece.id;

                  const correctRow = Math.floor(piece.id / gridSize);
                  const correctCol = piece.id % gridSize;
                  const bgX = (correctCol / (gridSize - 1)) * 100;
                  const bgY = (correctRow / (gridSize - 1)) * 100;

                  return (
                    <div
                      key={piece.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, piece)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, slotIndex)}
                      onClick={() => handlePieceClick(piece)}
                      className={`relative rounded-xl cursor-pointer overflow-hidden transition-all duration-150 ${
                        isSelected ? 'ring-4 ring-indigo-400 scale-[1.03] z-20 shadow-xl' : ''
                      } ${isSolved ? 'border-2 border-emerald-500/50' : 'border border-white/10 hover:border-white/30'}`}
                      style={{
                        backgroundImage: brandImageSrc ? `url("${brandImageSrc}")` : 'none',
                        backgroundSize: `${boardSize}px ${boardSize}px`,
                        backgroundPosition: `${bgX}% ${bgY}%`,
                        backgroundColor: '#1e1b4b'
                      }}
                    >
                      {/* Solved checkmark */}
                      {isSolved && (
                        <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-emerald-500/80 flex items-center justify-center">
                          <Check size={10} className="text-white" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Clue Bar */}
              <div className="w-full max-w-lg mt-3 bg-slate-950/80 p-3 rounded-xl border border-slate-800 text-xs">
                <div className="font-bold text-indigo-400 mb-1 flex items-center justify-between">
                  <span>CLUES UNLOCKED ({currentClueIdx}/3)</span>
                  <span className="text-slate-500">Solve more tiles to reveal</span>
                </div>
                <div className="text-slate-300">
                  {currentClueIdx >= 1 && <p>• {clues.clue1}</p>}
                  {currentClueIdx >= 2 && <p>• {clues.clue2}</p>}
                  {currentClueIdx >= 3 && <p>• {clues.clue3}</p>}
                </div>
              </div>
            </div>

            {/* Bottom Guessing Bar */}
            <form onSubmit={handleGuessSubmit} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3 flex gap-2 items-center">
              <input
                type="text"
                value={userGuess}
                onChange={(e) => setUserGuess(e.target.value)}
                placeholder="IDENTIFY STOCK / BRAND (e.g. TCS, HDFC, INFY)..."
                disabled={attempts >= 3 || isSubmittingGuess}
                className="flex-1 bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-white font-bold uppercase tracking-wider outline-none text-sm"
              />
              <button
                type="submit"
                disabled={!userGuess.trim() || attempts >= 3 || isSubmittingGuess}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-bold rounded-xl transition-all"
              >
                {isSubmittingGuess ? 'Validating...' : `Submit (${3 - attempts} left)`}
              </button>
            </form>
            {feedback && (
              <div className="text-center text-xs font-bold text-amber-400 animate-pulse">
                {feedback}
              </div>
            )}
          </div>

          {/* Right: Opponent Ghost Radar, Reactions & Battle Feed (4 Cols) */}
          <div className="lg:col-span-4 flex flex-col gap-3">
            {/* Opponent Ghost Radar Card */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-black uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                  <Shield size={14} /> Rival Ghost Radar
                </span>
                <span className="text-xs font-bold text-slate-400">{opponent?.name || 'Rival'}</span>
              </div>

              {/* Mini Ghost Grid */}
              <div className="flex items-center justify-center my-2">
                <div
                  className="grid gap-1 bg-slate-950 p-2 rounded-xl border border-slate-800 w-32 h-32"
                  style={{ gridTemplateColumns: `repeat(${gridSize}, 1fr)` }}
                >
                  {Array.from({ length: totalPieces }).map((_, i) => (
                    <div
                      key={i}
                      className={`rounded ${
                        i < opponentSolvedCount ? 'bg-rose-500/60 border border-rose-400' : 'bg-slate-900 border border-slate-800'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800 my-2">
                <div
                  className="bg-rose-500 h-full transition-all duration-300"
                  style={{ width: `${opponentProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>{opponentSolvedCount}/{totalPieces} Tiles Locked</span>
                <span>Clues: {opponentClueIdx}/3</span>
              </div>
            </div>

            {/* Quick Emoji Reaction Bar */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3">
              <div className="text-[11px] font-bold text-slate-400 uppercase mb-2">Send Live Reaction</div>
              <div className="flex justify-between gap-1">
                {['🚀', '🐂', '🐻', '💎🙌', '📉', '🔥'].map(emoji => (
                  <button
                    key={emoji}
                    onClick={() => sendReaction(emoji)}
                    className="flex-1 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-lg transition-transform active:scale-125"
                  >
                    {emoji}
                  </button>
                ))}
              </div>
            </div>

            {/* Battle Feed */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex-1 flex flex-col min-h-[160px]">
              <div className="text-xs font-black text-slate-400 uppercase tracking-wider mb-2">
                Live Battle Feed
              </div>
              <div className="flex-1 overflow-y-auto space-y-1.5 text-xs text-slate-300 pr-1">
                {battleFeed.map(item => (
                  <div key={item.id} className="bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 text-[10px] mr-1.5">{item.time}</span>
                    {item.text}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════════
  // VIEW 5: VICTORY / DEFEAT RESULTS SCREEN
  // ═════════════════════════════════════════════════════════════════════════════
  if (stage === 'results') {
    const isWinner = matchResult?.winnerId === playerId;
    const revealedBrand = matchResult?.brand;

    return (
      <div className="min-h-[calc(100vh-65px)] bg-[#030014] text-white p-4 flex items-center justify-center relative">
        <div className="max-w-2xl w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 backdrop-blur-xl relative z-10 shadow-2xl text-center">
          {/* Winner Trophy Banner */}
          <div className="mb-6">
            <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center mb-3 bg-gradient-to-br from-amber-400 to-amber-600 text-slate-950 shadow-lg shadow-amber-500/20">
              <Trophy size={32} />
            </div>
            <h1 className="text-3xl md:text-4xl font-black mb-1">
              {isWinner ? '🎉 VICTORY! YOU WON!' : '⚔️ MATCH COMPLETED'}
            </h1>
            <p className="text-slate-400 text-sm">
              {isWinner
                ? 'Your market instinct and agility outmatched your rival!'
                : `${matchResult?.winnerName || 'Your opponent'} identified the mystery stock first!`}
            </p>
          </div>

          {/* Revealed Brand Card */}
          {revealedBrand && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 my-6 flex items-center gap-4 text-left">
              <div className="w-16 h-16 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center overflow-hidden p-1 flex-shrink-0">
                {brandImageSrc && <img src={brandImageSrc} alt="" className="w-full h-full object-contain" />}
              </div>
              <div className="flex-1">
                <div className="text-xs font-bold text-indigo-400 uppercase">{revealedBrand.sector} Sector</div>
                <div className="text-xl font-black text-white">{revealedBrand.brand} ({revealedBrand.company})</div>
                <div className="text-xs text-slate-400">Ticker: <span className="font-mono text-emerald-400 font-bold">{revealedBrand.ticker}</span></div>
              </div>
            </div>
          )}

          {/* AI Teacher Insight / Lore */}
          {revealedBrand?.insight && (
            <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-2xl p-4 mb-6 text-left text-xs text-indigo-200">
              <span className="font-bold text-indigo-300 block mb-1 flex items-center gap-1.5">
                <Sparkles size={14} /> AI Market Lore & Moat:
              </span>
              {revealedBrand.insight}
            </div>
          )}

          {/* Rematch & Navigation Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleRequestRematch}
              disabled={rematchRequested}
              className={`flex-1 py-3.5 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${
                rematchRequested
                  ? 'bg-slate-800 text-slate-400 cursor-default'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
              }`}
            >
              <RefreshCw size={16} className={rematchRequested ? 'animate-spin' : ''} />
              {rematchRequested ? (opponentRematch ? 'Restarting Match...' : 'Rematch Requested...') : 'Request Rematch'}
            </button>
            <button
              onClick={() => {
                setStage('lobby');
                navigate('/duel');
              }}
              className="px-6 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl transition-colors"
            >
              Back to Lobby
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
