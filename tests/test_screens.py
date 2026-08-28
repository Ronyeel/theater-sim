"""
Integration tests for all Pygame screen states (MainMenu, SetupScreen, ExteriorScreen, GameScreen, ResultsScreen).
"""

import os
import unittest

# Headless SDL video driver for headless CI / testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame


class TestScreens(unittest.TestCase):
    """Integration test suite for screen rendering and updating."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        from game.settings import SCREEN_W, SCREEN_H
        cls.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_all_screens_lifecycle(self) -> None:
        from game.__main__ import (
            App, STATE_TITLE, STATE_SETUP, STATE_EXTERIOR, STATE_GAME, STATE_RESULTS
        )

        app = App(self.screen)
        states = [STATE_TITLE, STATE_SETUP, STATE_EXTERIOR, STATE_GAME, STATE_RESULTS]

        for state in states:
            app._current_state = state
            # Test update tick
            app.update(0.016)
            # Test draw render
            app.draw()
            # Test mouse and keyboard event handling
            mouse_evt = pygame.event.Event(
                pygame.MOUSEMOTION, {"pos": (200, 200), "rel": (0, 0), "buttons": (0, 0, 0)}
            )
            app.handle_event(mouse_evt)

    def test_high_npc_performance(self) -> None:
        """Verify that updating and drawing with 100 NPCs runs smoothly."""
        import time
        from game.screens.game_screen import GameScreen
        from game.entities.npc import build_npcs

        game = GameScreen(self.screen, lambda *_: None)
        # Add 100 NPCs
        game.npcs = build_npcs(count=100)
        for i, npc in enumerate(game.npcs):
            npc.spawn_delay = 0.0  # activate immediately
            npc.x = 48 * (2 + (i % 15))
            npc.y = 48 * (15 + (i % 8))

        t0 = time.perf_counter()
        # Simulate 60 frames (1 full second at 60 FPS)
        for _ in range(60):
            game.update(0.016)
            game.draw(self.screen)
        elapsed = time.perf_counter() - t0

        # 60 full frames with 100 NPCs should easily complete within 1 second
        self.assertLess(elapsed, 1.0, f"Rendering & update took {elapsed:.3f}s for 60 frames")
    def test_usher_queue_formation(self) -> None:
        """Verify that usher queues line up horizontally along row 15 extending outwards."""
        from game.entities.npc import NPC

        # Left usher booth (col 7)
        self.assertEqual(NPC._calc_usher_wait_tile(7, 0), (7, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(7, 1), (6, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(7, 2), (5, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(7, 6), (1, 15))

        # Right usher booth (col 12)
        self.assertEqual(NPC._calc_usher_wait_tile(12, 0), (12, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(12, 1), (13, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(12, 2), (14, 15))
        self.assertEqual(NPC._calc_usher_wait_tile(12, 6), (18, 15))

    def test_fcfs_queue_discipline(self) -> None:
        """Verify that newly arriving guests never cut in front of existing queue members."""
        from game.entities.npc import NPC

        npc_early = NPC(character_id=0, start_col=10, start_row=24, queue_slot=5)
        npc_early.usher_lane = 0
        npc_early.state = NPC.USHER_LINE
        npc_early.usher_seq = 10

        npc_later = NPC(character_id=1, start_col=10, start_row=24, queue_slot=0)  # Lower spawn slot, but arrived later
        npc_later.usher_lane = 0
        npc_later.state = NPC.USHER_LINE
        npc_later.usher_seq = 20

        # npc_later should see npc_early as a leader
        leaders_for_later = npc_later._queue_leaders([npc_early, npc_later], 2, {NPC.USHER_LINE})
        self.assertIn(npc_early, leaders_for_later)

        # npc_early should have NO leaders
        leaders_for_early = npc_early._queue_leaders([npc_early, npc_later], 2, {NPC.USHER_LINE})
        self.assertEqual(len(leaders_for_early), 0)

    def test_ticket_side_wing_queuing(self) -> None:
        """Verify that deep ticket queues gather in side wings and avoid center aisle."""
        from game.entities.npc import NPC

        # Kiosks 4 and 7 should stage into left wing (cols 1..6)
        for depth in range(3, 10):
            tile_4 = NPC._calc_ticket_wait_tile(4, depth)
            tile_7 = NPC._calc_ticket_wait_tile(7, depth)
            self.assertNotIn(tile_4[0], [8, 9, 10, 11])
            self.assertNotIn(tile_7[0], [8, 9, 10, 11])

        # Kiosks 10 and 13 should stage into right wing (cols 12..18)
        for depth in range(3, 10):
            tile_10 = NPC._calc_ticket_wait_tile(10, depth)
            tile_13 = NPC._calc_ticket_wait_tile(13, depth)
            self.assertNotIn(tile_10[0], [8, 9, 10, 11])
            self.assertNotIn(tile_13[0], [8, 9, 10, 11])

    def test_npc_exit_through_door_only(self) -> None:
        """Verify that NPCs only exit through the bottom doors on row 24."""
        from game.entities.npc import NPC

        npc = NPC(character_id=0, start_col=2, start_row=20, queue_slot=0)
        npc._start_exit_route()
        self.assertEqual(npc.state, NPC.LEAVING)
        # Should not despawn until reaching bottom row 24
        npc._arrive_at_step()
        self.assertFalse(npc.has_left)

        # Move to bottom exit door
        npc.x = 9 * 48 + 24
        npc.y = 24 * 48 + 24
        npc._arrive_at_step()
        self.assertTrue(npc.has_left)

    def test_usher_fcfs_lobby_bypass(self) -> None:
        """Verify that a guest already at the usher line is not blocked by a guest far away in the lobby."""
        from game.entities.npc import NPC

        # Guest 1 is at the usher line (row 15)
        npc_waiting = NPC(character_id=0, start_col=7, start_row=15, queue_slot=5)
        npc_waiting.usher_lane = 0
        npc_waiting.state = NPC.USHER_LINE
        npc_waiting.usher_seq = 20

        # Guest 2 is far away in the lobby (row 20), but bought a ticket earlier (lower usher_seq)
        npc_distant = NPC(character_id=1, start_col=10, start_row=20, queue_slot=0)
        npc_distant.usher_lane = 0
        npc_distant.state = NPC.USHER_LINE
        npc_distant.usher_seq = 10

        # npc_waiting is at the checkpoint, so npc_distant (still in lobby) does NOT block them
        leaders = npc_waiting._queue_leaders([npc_waiting, npc_distant], 2, {NPC.USHER_LINE})
        self.assertEqual(len(leaders), 0)

    def test_usher_desk_occupancy_guard(self) -> None:
        """Verify that a guest waiting in line does not overlap onto an NPC in CHECKING_TICKET."""
        from game.entities.npc import NPC

        # Guest 1 is at the desk being checked
        npc_at_desk = NPC(character_id=0, start_col=7, start_row=15, queue_slot=0)
        npc_at_desk.usher_lane = 0
        npc_at_desk.state = NPC.CHECKING_TICKET
        npc_at_desk.usher_seq = 10

        # Guest 2 is waiting in the usher line
        npc_next = NPC(character_id=1, start_col=6, start_row=15, queue_slot=1)
        npc_next.usher_lane = 0
        npc_next.state = NPC.USHER_LINE
        npc_next.usher_seq = 20

        # Arriving at step should not enter CHECKING_TICKET while desk is occupied
        npc_next._arrive_at_step([npc_at_desk, npc_next])
        self.assertEqual(npc_next.state, NPC.USHER_LINE)


if __name__ == "__main__":
    unittest.main()
