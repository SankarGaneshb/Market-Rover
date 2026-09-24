"""
Unit and Integration Tests for InvestBrand Bull vs Bear (1v1 Real-Time Duel)
Tests room lifecycle, synchronized puzzle generation, progress broadcasting,
server-authoritative guessing, and REST API integration.
"""
import pytest
import asyncio
from investbrand.backend.duel_manager import DuelRoomManager, DuelRoom, DuelPlayer


@pytest.mark.asyncio
async def test_duel_manager_create_and_join_room():
    manager = DuelRoomManager()

    # 1. Create Room
    room_code, p1_id = await manager.create_room(host_name="Bull_Ace", host_avatar="", difficulty="easy")
    assert room_code is not None
    assert len(room_code) == 6
    assert p1_id.startswith("p1_")

    room = manager.rooms.get(room_code)
    assert room is not None
    assert room.state == "waiting"
    assert len(room.players) == 1
    assert room.players[p1_id].name == "Bull_Ace"
    assert room.players[p1_id].role == "bull"

    # 2. Join Room
    joined_room, p2_id, err = await manager.join_room(room_code, player_name="Bear_King", player_avatar="")
    assert err is None
    assert p2_id.startswith("p2_")
    assert joined_room.state == "ready"
    assert len(joined_room.players) == 2
    assert joined_room.players[p2_id].name == "Bear_King"
    assert joined_room.players[p2_id].role == "bear"

    # 3. Third Player Cannot Join Full Room
    _, _, err3 = await manager.join_room(room_code, player_name="Third_Wheel", player_avatar="")
    assert "already full" in err3


@pytest.mark.asyncio
async def test_duel_puzzle_seeding_and_readiness():
    manager = DuelRoomManager()
    room_code, p1_id = await manager.create_room(host_name="Bull1", host_avatar="")
    _, p2_id, _ = await manager.join_room(room_code, player_name="Bear1", player_avatar="")

    room = manager.rooms[room_code]

    # Player 1 ready
    await manager.handle_player_ready(room_code, p1_id)
    assert room.players[p1_id].ready is True
    assert room.state == "ready"  # Waiting for p2

    # Player 2 ready -> Trigger match start
    await manager.handle_player_ready(room_code, p2_id)
    assert room.players[p2_id].ready is True
    assert room.state == "playing"
    assert room.brand is not None
    assert len(room.pieces) == 9  # 3x3 easy grid
    assert "clue1" in room.clues
    assert "clue2" in room.clues
    assert "clue3" in room.clues


@pytest.mark.asyncio
async def test_duel_move_update_and_clues():
    manager = DuelRoomManager()
    room_code, p1_id = await manager.create_room(host_name="Bull1", host_avatar="")
    _, p2_id, _ = await manager.join_room(room_code, player_name="Bear1", player_avatar="")
    await manager.handle_player_ready(room_code, p1_id)
    await manager.handle_player_ready(room_code, p2_id)

    # Update move for p1
    await manager.handle_move_update(room_code, p1_id, solved_count=5, clue_idx=2, moves=6)
    p1 = manager.rooms[room_code].players[p1_id]
    assert p1.solved_count == 5
    assert p1.current_clue_idx == 2
    assert p1.moves == 6


@pytest.mark.asyncio
async def test_duel_server_authoritative_guess():
    manager = DuelRoomManager()
    room_code, p1_id = await manager.create_room(host_name="Bull1", host_avatar="")
    _, p2_id, _ = await manager.join_room(room_code, player_name="Bear1", player_avatar="")
    await manager.handle_player_ready(room_code, p1_id)
    await manager.handle_player_ready(room_code, p2_id)

    room = manager.rooms[room_code]
    correct_brand_name = room.brand["brand"]

    # 1. Test Wrong Guess
    wrong_res = await manager.handle_guess(room_code, p1_id, "CompletelyWrongStockXYZ")
    assert wrong_res["success"] is True
    assert wrong_res["isCorrect"] is False
    assert wrong_res["attempts"] == 1
    assert room.state == "playing"

    # 2. Test Correct Guess by Player 2
    correct_res = await manager.handle_guess(room_code, p2_id, correct_brand_name)
    assert correct_res["success"] is True
    assert correct_res["isCorrect"] is True
    assert correct_res["score"] > 0
    assert room.state == "finished"
    assert room.winner_id == p2_id
    assert room.winner_name == "Bear1"


@pytest.mark.asyncio
async def test_duel_quick_match_flow():
    manager = DuelRoomManager()

    # Player 1 enters quick match
    room_code1, p1_id, matched1 = await manager.get_or_create_quick_match("QuickBull", "")
    assert matched1 is False
    assert manager.quick_match_queue == room_code1

    # Player 2 enters quick match
    room_code2, p2_id, matched2 = await manager.get_or_create_quick_match("QuickBear", "")
    assert matched2 is True
    assert room_code1 == room_code2
    assert manager.quick_match_queue is None

    room = manager.rooms[room_code1]
    assert len(room.players) == 2
    assert room.state == "ready"


@pytest.mark.asyncio
async def test_duel_disconnect_forfeit():
    manager = DuelRoomManager()
    room_code, p1_id = await manager.create_room(host_name="Bull1", host_avatar="")
    _, p2_id, _ = await manager.join_room(room_code, player_name="Bear1", player_avatar="")
    await manager.handle_player_ready(room_code, p1_id)
    await manager.handle_player_ready(room_code, p2_id)

    room = manager.rooms[room_code]
    assert room.state == "playing"

    # Player 1 disconnects -> Player 2 wins by forfeit
    await manager.handle_disconnect(room_code, p1_id)
    assert room.state == "finished"
    assert room.winner_id == p2_id
    assert room.end_reason == "opponent_forfeit"


@pytest.mark.asyncio
async def test_duel_grid_sizes_easy_medium_hard():
    """Verify 3x3 (9 pieces), 4x4 (16 pieces), 5x5 (25 pieces) grid puzzle generation."""
    # 3x3 Easy
    room_easy = DuelRoom(room_code="EASY01", difficulty="easy")
    assert room_easy.grid_size == 3
    assert room_easy.total_pieces == 9
    room_easy.generate_puzzle()
    assert len(room_easy.pieces) == 9

    # 4x4 Medium
    room_med = DuelRoom(room_code="MEDM01", difficulty="medium")
    assert room_med.grid_size == 4
    assert room_med.total_pieces == 16
    room_med.generate_puzzle()
    assert len(room_med.pieces) == 16

    # 5x5 Hard
    room_hard = DuelRoom(room_code="HARD01", difficulty="hard")
    assert room_hard.grid_size == 5
    assert room_hard.total_pieces == 25
    room_hard.generate_puzzle()
    assert len(room_hard.pieces) == 25
