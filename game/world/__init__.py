"""
World Package
Spatial interaction zones, proximity triggers, and zone queries.
"""

from game.world.interactions import Zone, build_zones, find_nearest_zone

__all__ = ["Zone", "build_zones", "find_nearest_zone"]
