
from game.entities.player import Player, Stage
from game.entities.npc import NPC, build_npcs, moviegoer_sprite
from game.entities.staff import StaffMember, build_staff

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
