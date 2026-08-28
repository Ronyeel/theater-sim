"""
Entities Package
Player controller, autonomous NPC moviegoers with A* pathfinding, and theater staff.
"""

from game.entities.player import Player, Stage
from game.entities.npc import NPC, build_npcs, moviegoer_sprite
from game.entities.staff import StaffMember, build_staff

# Alias for backwards-compatibility
MoviegoerNPC = NPC

__all__ = [
    "Player",
    "Stage",
    "NPC",
    "MoviegoerNPC",
    "build_npcs",
    "moviegoer_sprite",
    "StaffMember",
    "build_staff",
]
