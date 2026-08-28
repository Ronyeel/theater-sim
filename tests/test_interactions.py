"""
Unit tests for interaction zones and tilemap in game/world/interactions.py and game/core/tilemap.py.
"""

import unittest
from game.world.interactions import build_zones, find_nearest_zone, Zone
from game.core.tilemap import tile_at, is_walkable, MAP_COLS, MAP_ROWS, TILE_WALL, TILE_FLOOR, TILE_SEAT
from game.settings import INTERACT_RADIUS


class TestInteractionsAndTilemap(unittest.TestCase):
    """Tests for spatial queries, zones, and tilemap bounds."""

    def test_build_zones_counts(self) -> None:
        zones = build_zones(num_cashiers=3, num_ushers=2, num_servers=2)
        cashier_zones = [z for z in zones if z.name == "cashier"]
        usher_zones = [z for z in zones if z.name == "usher"]
        server_zones = [z for z in zones if z.name == "snack"]

        self.assertEqual(len(cashier_zones), 3)
        self.assertEqual(len(usher_zones), 2)
        self.assertEqual(len(server_zones), 2)

    def test_find_nearest_zone(self) -> None:
        zones = [
            Zone("cashier", 100.0, 100.0, label="Buy Ticket"),
            Zone("snack", 300.0, 300.0, label="Buy Snacks"),
        ]
        # Point close to cashier
        near = find_nearest_zone(zones, 105.0, 102.0)
        self.assertIsNotNone(near)
        self.assertEqual(near.name, "cashier")

        # Point far away
        far = find_nearest_zone(zones, 900.0, 900.0)
        self.assertIsNone(far)

        # Filter by name
        filtered = find_nearest_zone(zones, 105.0, 102.0, filter_name="snack")
        self.assertIsNone(filtered)

    def test_tilemap_bounds_and_walkability(self) -> None:
        # Out of bounds returns TILE_WALL
        self.assertEqual(tile_at(-1, 0), TILE_WALL)
        self.assertEqual(tile_at(MAP_COLS + 5, 0), TILE_WALL)
        self.assertEqual(tile_at(0, -5), TILE_WALL)
        self.assertEqual(tile_at(0, MAP_ROWS + 5), TILE_WALL)

        # Top border is wall
        self.assertEqual(tile_at(0, 0), TILE_WALL)
        self.assertFalse(is_walkable(0, 0))

        # Open lobby tile (e.g. col 10, row 20) is floor and walkable
        self.assertEqual(tile_at(10, 20), TILE_FLOOR)
        self.assertTrue(is_walkable(10, 20))


if __name__ == "__main__":
    unittest.main()
