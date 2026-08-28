"""
UI Package
Reusable widgets (Button, Slider), live HUD dashboard, dialog menus, simulation panels, and speech bubbles.
"""

from game.ui.button import Button, Slider, draw_panel, draw_text
from game.ui.hud import HUD
from game.ui.dialog_menu import DialogMenu, TicketDialog, ConcessionDialog, UsherDialog
from game.ui.simulation_panel import SimulationPanel, NumberInput
from game.ui.speech_bubble import SpeechBubble, DialogPrompt

__all__ = [
    "Button",
    "Slider",
    "draw_panel",
    "draw_text",
    "HUD",
    "DialogMenu",
    "TicketDialog",
    "ConcessionDialog",
    "UsherDialog",
    "SimulationPanel",
    "NumberInput",
    "SpeechBubble",
    "DialogPrompt",
]
