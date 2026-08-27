"""
CinePlex Dreams — Speech Bubbles & Dialog Prompts
Pop-in bubbles above characters and [E] interact prompts near zones.
"""
import pygame
import math
from game.settings import C_NEON_GOLD, C_NEON_PINK, C_TEXT_WHITE, C_BG_DARK


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


SPEECH_LINES = [
    "One ticket please!",
    "Mmm, popcorn!",
    "Can't wait!",
    "So excited!",
    "What's on today?",
    "Finally my turn!",
    "Yay, snacks!",
    "Front row!",
]


class SpeechBubble:
    """A pop-in speech bubble that fades out above a world position."""

    _font = None

    def __init__(self, text: str, wx: float, wy: float,
                 color=C_TEXT_WHITE, lifetime=2.5):
        if SpeechBubble._font is None:
            SpeechBubble._font = _font("consolas", 12)
        self.text     = text
        self.wx       = wx
        self.wy       = wy
        self.lifetime = lifetime
        self.max_life = lifetime
        self.color    = color
        self.alive    = True
        self._scale_t = 0.0  # pop-in progress (0→1)
        self._rendered = SpeechBubble._font.render(text, True, (50, 40, 60))

    def update(self, dt: float):
        self._scale_t = min(1.0, self._scale_t + dt * 6)
        self.lifetime -= dt
        self.wy       -= 12 * dt   # float upward
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.wx, self.wy)

        # Pop-in scale
        scale = min(1.0, self._scale_t)
        if scale <= 0: return

        tw, th = self._rendered.get_size()
        pad  = 6
        bw   = tw + pad*2
        bh   = th + pad*2 + 6

        bubble = pygame.Surface((bw, bh), pygame.SRCALPHA)
        # Background
        pygame.draw.rect(bubble, (255, 255, 255, 230), (0, 0, bw, bh-6), border_radius=6)
        pygame.draw.rect(bubble, (160, 150, 160), (0, 0, bw, bh-6), 1, border_radius=6)
        # Tail
        pygame.draw.polygon(bubble, (255, 255, 255, 230),
                            [(bw//2-4, bh-6), (bw//2+4, bh-6), (bw//2, bh)])
        bubble.blit(self._rendered, (pad, pad))

        # Alpha based on lifetime
        alpha = min(255, int(255 * min(1.0, self.lifetime / 0.5)))
        bubble.set_alpha(alpha)

        # Scale
        if scale < 1.0:
            nw, nh = int(bw*scale), int(bh*scale)
            if nw < 1 or nh < 1: return
            bubble = pygame.transform.scale(bubble, (nw, nh))
            bw, bh = nw, nh

        surface.blit(bubble, (int(sx) - bw//2, int(sy) - bh - 4))


class DialogPrompt:
    """The [E] interaction hint shown near an active zone."""

    _font    = None
    _sm_font = None

    def __init__(self):
        if DialogPrompt._font is None:
            DialogPrompt._font    = _font("consolas", 15, bold=True)
            DialogPrompt._sm_font = _font("consolas", 12)
        self._text    = ""
        self._visible = False
        self._t       = 0.0

    def show(self, label: str):
        self._text    = label
        self._visible = True
        self._t       = 0.0

    def hide(self):
        self._visible = False

    def update(self, dt):
        if self._visible:
            self._t += dt

    def draw(self, surface: pygame.Surface):
        if not self._visible or not self._text: return
        pulse = 0.85 + 0.15 * math.sin(self._t * 4.0)
        color = tuple(int(c * pulse) for c in C_NEON_GOLD[:3])

        # Key hint box
        s = DialogPrompt._font.render(self._text, True, color)
        pad = 8
        w, h = s.get_width() + pad*2, s.get_height() + pad*2
        x = surface.get_width()//2 - w//2
        y = surface.get_height() - 80

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((15, 10, 35, 200))
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, color, (x, y, w, h), 2, border_radius=6)
        surface.blit(s, (x + pad, y + pad))
