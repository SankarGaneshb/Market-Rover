"""
InvestBrand Bull vs Bear 1v1 Real-Time Duel Manager
Handles WebSocket connections, room lifecycle, synchronized puzzle generation,
live progress broadcasting, server-authoritative guess validation, and rematch negotiation.
"""
import asyncio
import json
import logging
import random
import string
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import WebSocket

logger = logging.getLogger("market_rover.investbrand.duel")

# Load brands data for duel seeding
BRANDS_FILE = Path(__file__).resolve().parent / "brands_data.json"
DUEL_BRANDS: List[Dict[str, Any]] = []

if BRANDS_FILE.exists():
    try:
        with open(BRANDS_FILE, "r", encoding="utf-8") as f:
            DUEL_BRANDS = json.load(f)
    except Exception as e:
        logger.warning(f"[DuelManager] Error loading brands_data.json: {e}")

if not DUEL_BRANDS:
    DUEL_BRANDS = [
        {"id": 1, "brand": "Jio", "company": "Reliance Industries", "ticker": "RELIANCE", "sector": "Energy", "insight": "Digital powerhouse revolutionizing telecom & retail.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#0057FF'/><text x='200' y='220' fill='white' font-size='80' text-anchor='middle'>Jio</text></svg>"},
        {"id": 2, "brand": "TCS", "company": "Tata Consultancy Services", "ticker": "TCS", "sector": "IT", "insight": "Pioneered India's IT export boom.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#002D72'/><text x='200' y='220' fill='white' font-size='80' text-anchor='middle'>TCS</text></svg>"},
        {"id": 3, "brand": "HDFC Bank", "company": "HDFC Bank", "ticker": "HDFCBANK", "sector": "Financials", "insight": "India's premier private banking institution.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#004C8F'/><text x='200' y='220' fill='white' font-size='60' text-anchor='middle'>HDFC</text></svg>"},
        {"id": 4, "brand": "Infosys", "company": "Infosys", "ticker": "INFY", "sector": "IT", "insight": "Global leader in digital consulting and software.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#007CC3'/><text x='200' y='220' fill='white' font-size='60' text-anchor='middle'>Infosys</text></svg>"},
        {"id": 5, "brand": "SBI", "company": "State Bank of India", "ticker": "SBIN", "sector": "Financials", "insight": "Largest public sector bank in India.", "logoSvg": "<svg viewBox='0 0 400 400'><rect width='400' height='400' fill='#1F4788'/><text x='200' y='220' fill='white' font-size='70' text-anchor='middle'>SBI</text></svg>"}
    ]


class DuelPlayer:
    def __init__(self, player_id: str, name: str, avatar: str, role: str, ws: Optional[WebSocket] = None):
        self.player_id = player_id
        self.name = name or ("Bull Trader" if role == "bull" else "Bear Trader")
        self.avatar = avatar or ""
        self.role = role  # "bull" (host) or "bear" (challenger)
        self.ws = ws
        self.ready = False
        self.score = 0
        self.moves = 0
        self.solved_count = 0
        self.current_clue_idx = 1
        self.attempts = 0
        self.finished = False
        self.finish_time = 0.0
        self.rematch_requested = False

    def to_dict(self, include_ws: bool = False) -> Dict[str, Any]:
        d = {
            "playerId": self.player_id,
            "name": self.name,
            "avatar": self.avatar,
            "role": self.role,
            "ready": self.ready,
            "score": self.score,
            "moves": self.moves,
            "solvedCount": self.solved_count,
            "currentClueIdx": self.current_clue_idx,
            "attempts": self.attempts,
            "finished": self.finished,
            "rematchRequested": self.rematch_requested
        }
        return d


class DuelRoom:
    def __init__(self, room_code: str, difficulty: str = "easy"):
        self.room_code = room_code.upper()
        self.difficulty = difficulty
        self.grid_size = 3 if difficulty == "easy" else (4 if difficulty == "medium" else 5)
        self.total_pieces = self.grid_size * self.grid_size
        self.created_at = time.time()
        self.players: Dict[str, DuelPlayer] = {}
        self.state = "waiting"  # waiting, ready, playing, finished
        self.brand: Optional[Dict[str, Any]] = None
        self.pieces: List[Dict[str, int]] = []
        self.winner_id: Optional[str] = None
        self.winner_name: Optional[str] = None
        self.end_reason: Optional[str] = None
        self.match_start_time: Optional[float] = None
        self.clues: Dict[str, str] = {}
        self.word_cloud: str = ""
        self.match_duration_seconds: int = 90

    def generate_puzzle(self):
        """Select a random brand and generate a deterministic shuffle for both players."""
        self.brand = random.choice(DUEL_BRANDS)
        self.clues = {
            "clue1": f"Sector Clue: Operating in the {self.brand.get('sector', 'Indian Market')} sector.",
            "clue2": f"Word Clue: {len(self.brand.get('brand', ''))} letters, starts with '{self.brand.get('brand', ['?'])[0]}'",
            "clue3": f"Stock Clue: Owned by {self.brand.get('company', self.brand.get('brand'))} (Ticker: {self.brand.get('ticker', '')})."
        }
        self.word_cloud = f"Market Moat, {self.brand.get('sector', 'Growth')}, High Liquidity, Institutional Focus, {self.brand.get('ticker', '')}"

        # Generate piece positions
        grid_total = self.total_pieces
        puzzle_pieces = [{"id": i, "correctPosition": i, "currentPosition": i} for i in range(grid_total)]
        # Fisher-Yates shuffle
        for i in range(grid_total - 1, 0, -1):
            j = random.randint(0, i)
            puzzle_pieces[i]["currentPosition"], puzzle_pieces[j]["currentPosition"] = (
                puzzle_pieces[j]["currentPosition"],
                puzzle_pieces[i]["currentPosition"]
            )
        self.pieces = puzzle_pieces

    def to_summary(self, reveal_brand: bool = False) -> Dict[str, Any]:
        """Return room state summary. Obfuscate true brand name if match is currently active."""
        brand_info = None
        if self.brand:
            if reveal_brand or self.state == "finished":
                brand_info = self.brand
            else:
                # Sanitized brand metadata for active match (no brand name/ticker leak)
                brand_info = {
                    "id": self.brand.get("id"),
                    "sector": self.brand.get("sector"),
                    "logoSvg": self.brand.get("logoSvg"),
                    "ticker": self.brand.get("ticker")  # Used for sliced image background styling
                }

        return {
            "roomCode": self.room_code,
            "state": self.state,
            "difficulty": self.difficulty,
            "gridSize": self.grid_size,
            "totalPieces": self.total_pieces,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "brand": brand_info,
            "pieces": self.pieces,
            "clues": self.clues,
            "wordCloud": self.word_cloud,
            "winnerId": self.winner_id,
            "winnerName": self.winner_name,
            "endReason": self.end_reason,
            "matchDurationSeconds": self.match_duration_seconds
        }


class DuelRoomManager:
    def __init__(self):
        self.rooms: Dict[str, DuelRoom] = {}
        self.quick_match_queue: Optional[str] = None
        self._lock = asyncio.Lock()

    def _generate_code(self) -> str:
        """Generate a clean 6-character room code."""
        prefixes = ["BULL", "BEAR", "NIFT", "ROVR", "RUSH"]
        prefix = random.choice(prefixes)
        digits = "".join(random.choices(string.digits, k=2))
        return f"{prefix}{digits}"

    async def create_room(self, host_name: str, host_avatar: str, difficulty: str = "easy") -> tuple[str, str]:
        """Create a new room with the creator as Player 1 (Bull)."""
        async with self._lock:
            room_code = self._generate_code()
            while room_code in self.rooms:
                room_code = self._generate_code()

            room = DuelRoom(room_code=room_code, difficulty=difficulty)
            player_id = f"p1_{random.randint(10000, 99999)}"
            player = DuelPlayer(player_id=player_id, name=host_name, avatar=host_avatar, role="bull")
            room.players[player_id] = player
            self.rooms[room_code] = room
            logger.info(f"[DuelManager] Created room {room_code} by {host_name} ({player_id})")
            return room_code, player_id

    async def join_room(self, room_code: str, player_name: str, player_avatar: str) -> tuple[Optional[DuelRoom], Optional[str], Optional[str]]:
        """Join an existing room as Player 2 (Bear)."""
        async with self._lock:
            room_code = room_code.upper().strip()
            room = self.rooms.get(room_code)
            if not room:
                return None, None, "Room not found. Please verify the 6-character code."

            if len(room.players) >= 2:
                # Check if this is a reconnecting player
                for pid, p in room.players.items():
                    if p.name == player_name:
                        return room, pid, None
                return None, None, "This Duel Arena is already full (2/2 players)."

            if room.state not in ["waiting", "ready"]:
                return None, None, "Match is already in progress in this Arena."

            player_id = f"p2_{random.randint(10000, 99999)}"
            player = DuelPlayer(player_id=player_id, name=player_name, avatar=player_avatar, role="bear")
            room.players[player_id] = player
            room.state = "ready"
            logger.info(f"[DuelManager] Player {player_name} ({player_id}) joined room {room_code}")
            return room, player_id, None

    async def get_or_create_quick_match(self, player_name: str, player_avatar: str) -> tuple[str, str, bool]:
        """Find an open quick match room or create a new one."""
        async with self._lock:
            if self.quick_match_queue and self.quick_match_queue in self.rooms:
                room_code = self.quick_match_queue
                room = self.rooms[room_code]
                if len(room.players) < 2 and room.state == "waiting":
                    player_id = f"p2_{random.randint(10000, 99999)}"
                    player = DuelPlayer(player_id=player_id, name=player_name, avatar=player_avatar, role="bear")
                    room.players[player_id] = player
                    room.state = "ready"
                    self.quick_match_queue = None
                    return room_code, player_id, True

            # Create new room and put on quick match queue
            room_code = self._generate_code()
            room = DuelRoom(room_code=room_code, difficulty="easy")
            player_id = f"p1_{random.randint(10000, 99999)}"
            player = DuelPlayer(player_id=player_id, name=player_name, avatar=player_avatar, role="bull")
            room.players[player_id] = player
            self.rooms[room_code] = room
            self.quick_match_queue = room_code
            return room_code, player_id, False

    async def attach_websocket(self, room_code: str, player_id: str, ws: WebSocket) -> bool:
        """Attach active WebSocket connection to player."""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players:
            return False
        room.players[player_id].ws = ws
        return True

    async def broadcast_to_room(self, room_code: str, message: Dict[str, Any], exclude_player_id: Optional[str] = None):
        """Send WebSocket payload to all players in the room."""
        room = self.rooms.get(room_code.upper())
        if not room:
            return

        disconnected_pids = []
        for pid, player in room.players.items():
            if exclude_player_id and pid == exclude_player_id:
                continue
            if player.ws:
                try:
                    await player.ws.send_json(message)
                except Exception as e:
                    logger.warning(f"[DuelManager] Failed to send WS to {pid} in {room_code}: {e}")
                    disconnected_pids.append(pid)

    async def handle_player_ready(self, room_code: str, player_id: str) -> None:
        """Mark player ready. If both ready, start the match!"""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players:
            return

        room.players[player_id].ready = True
        logger.info(f"[DuelManager] Player {player_id} ready in {room_code}")

        # Broadcast ready state
        await self.broadcast_to_room(room_code, {
            "type": "PLAYER_READY_UPDATE",
            "playerId": player_id,
            "players": {pid: p.to_dict() for pid, p in room.players.items()}
        })

        # Check if both players ready
        if len(room.players) == 2 and all(p.ready for p in room.players.values()):
            room.state = "playing"
            room.generate_puzzle()
            room.match_start_time = time.time()
            logger.info(f"[DuelManager] Starting match in {room_code} for brand {room.brand.get('brand')}")

            await self.broadcast_to_room(room_code, {
                "type": "MATCH_START",
                "room": room.to_summary(reveal_brand=False),
                "startTime": room.match_start_time
            })

    async def handle_move_update(self, room_code: str, player_id: str, solved_count: int, clue_idx: int, moves: int):
        """Update player progress and broadcast ghost radar to the opponent."""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players or room.state != "playing":
            return

        player = room.players[player_id]
        player.solved_count = solved_count
        player.current_clue_idx = max(player.current_clue_idx, clue_idx)
        player.moves = moves

        # Calculate progress percent
        progress_pct = int((solved_count / max(1, room.total_pieces)) * 100)

        # Broadcast progress to opponent
        await self.broadcast_to_room(room_code, {
            "type": "OPPONENT_PROGRESS",
            "playerId": player_id,
            "solvedCount": solved_count,
            "totalPieces": room.total_pieces,
            "progress": progress_pct,
            "currentClueIdx": player.current_clue_idx,
            "moves": moves
        }, exclude_player_id=player_id)

    async def handle_guess(self, room_code: str, player_id: str, raw_guess: str) -> Dict[str, Any]:
        """Validate player's stock guess on the server with early-guess bonus scoring."""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players or room.state != "playing":
            return {"success": False, "message": "Match is not active."}

        player = room.players[player_id]
        player.attempts += 1
        guess = raw_guess.strip().lower()

        brand_name = (room.brand.get("brand") or "").lower()
        ticker = (room.brand.get("ticker") or "").lower()
        company = (room.brand.get("company") or "").lower()

        is_correct = (
            guess == brand_name or
            guess == ticker or
            guess == company or
            (len(guess) >= 3 and guess in brand_name) or
            (len(guess) >= 3 and brand_name in guess)
        )

        if is_correct:
            player.finished = True
            player.finish_time = time.time()
            # Calculate final score: Base 1000 pts - time penalty + early guess bonus
            elapsed = int(time.time() - (room.match_start_time or time.time()))
            time_bonus = max(0, 90 - elapsed) * 10
            attempt_multiplier = 1.0 if player.attempts == 1 else (0.8 if player.attempts == 2 else 0.6)
            early_clue_bonus = 300 if player.current_clue_idx == 1 else (150 if player.current_clue_idx == 2 else 50)

            player.score = int((1000 + time_bonus + early_clue_bonus) * attempt_multiplier)
            room.winner_id = player_id
            room.winner_name = player.name
            room.end_reason = "correct_guess"
            room.state = "finished"

            logger.info(f"[DuelManager] {player.name} won {room_code} with guess '{raw_guess}'! Score: {player.score}")

            # Broadcast Match Over with brand revealed and score
            await self.broadcast_to_room(room_code, {
                "type": "MATCH_OVER",
                "winnerId": player_id,
                "winnerName": player.name,
                "winnerRole": player.role,
                "endReason": "correct_guess",
                "score": player.score,
                "winnerScore": player.score,
                "brand": room.brand,
                "room": room.to_summary(reveal_brand=True)
            })

            return {"success": True, "isCorrect": True, "score": player.score, "message": f"🎯 Correct! You identified {room.brand.get('brand')}!"}

        else:
            # Incorrect guess: penalty
            penalty_msg = f"❌ '{raw_guess}' is incorrect! (Attempt {player.attempts}/3)"
            if player.attempts >= 3:
                penalty_msg += " All attempts exhausted for this round."

            await self.broadcast_to_room(room_code, {
                "type": "GUESS_FEEDBACK",
                "playerId": player_id,
                "playerName": player.name,
                "feedback": f"{player.name} submitted a guess ({player.attempts}/3)",
                "attempts": player.attempts
            })

            return {"success": True, "isCorrect": False, "message": penalty_msg, "attempts": player.attempts}

    async def handle_reaction(self, room_code: str, player_id: str, emoji: str):
        """Broadcast live emoji reaction to the room."""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players:
            return

        player = room.players[player_id]
        await self.broadcast_to_room(room_code, {
            "type": "REACTION",
            "playerId": player_id,
            "playerName": player.name,
            "role": player.role,
            "emoji": emoji
        })

    async def handle_rematch(self, room_code: str, player_id: str):
        """Handle player requesting a rematch."""
        room = self.rooms.get(room_code.upper())
        if not room or player_id not in room.players:
            return

        player = room.players[player_id]
        player.rematch_requested = True
        player.ready = True

        await self.broadcast_to_room(room_code, {
            "type": "REMATCH_REQUESTED",
            "playerId": player_id,
            "playerName": player.name
        })

        # If both requested rematch, restart room
        if all(p.rematch_requested for p in room.players.values()):
            room.state = "playing"
            room.winner_id = None
            room.winner_name = None
            room.end_reason = None
            for p in room.players.values():
                p.score = 0
                p.moves = 0
                p.solved_count = 0
                p.current_clue_idx = 1
                p.attempts = 0
                p.finished = False
                p.rematch_requested = False

            room.generate_puzzle()
            room.match_start_time = time.time()
            logger.info(f"[DuelManager] Rematch started in {room_code}")

            await self.broadcast_to_room(room_code, {
                "type": "MATCH_START",
                "room": room.to_summary(reveal_brand=False),
                "startTime": room.match_start_time
            })

    async def handle_disconnect(self, room_code: str, player_id: str):
        """Handle player disconnection or forfeit."""
        async with self._lock:
            room = self.rooms.get(room_code.upper())
            if not room:
                return

            if player_id in room.players:
                player = room.players[player_id]
                logger.info(f"[DuelManager] Player {player.name} disconnected from {room_code}")

                # If match was active, award win to remaining player
                if room.state == "playing":
                    remaining_pids = [pid for pid in room.players if pid != player_id]
                    if remaining_pids:
                        winner = room.players[remaining_pids[0]]
                        room.winner_id = winner.player_id
                        room.winner_name = winner.name
                        room.end_reason = "opponent_forfeit"
                        room.state = "finished"

                        await self.broadcast_to_room(room_code, {
                            "type": "MATCH_OVER",
                            "winnerId": winner.player_id,
                            "winnerName": winner.name,
                            "winnerRole": winner.role,
                            "endReason": "opponent_forfeit",
                            "brand": room.brand,
                            "room": room.to_summary(reveal_brand=True)
                        }, exclude_player_id=player_id)
                else:
                    del room.players[player_id]
                    await self.broadcast_to_room(room_code, {
                        "type": "PLAYER_LEFT",
                        "playerId": player_id,
                        "playerName": player.name
                    })

                # Clean up empty room
                if len(room.players) == 0:
                    del self.rooms[room_code.upper()]
                    if self.quick_match_queue == room_code.upper():
                        self.quick_match_queue = None
                    logger.info(f"[DuelManager] Deleted empty room {room_code}")


# Singleton instance
duel_manager = DuelRoomManager()
