"""
CinePlex Dreams — NPC Entities
Ambient townspeople that wander around the cinema lobby, making the world feel alive.
Uses a mix of the character animation sheets in assets/sprites/.
"""
import os
import pygame
import random
import secrets
import math
import heapq
from game.settings import (
    TILE_SIZE, SPRITES_DIR, CASHIER_DESK_COLS, USHER_DESK_COLS,
    SNACK_DESK_COLS, SEAT_COLS, SEAT_ROWS, TILE_SEAT,
    USHER_DESK_ROW, USHER_PASSAGE_COLS, DEBUG_NPC_COLLISION_RANGE,
)
from game.core.tilemap import is_walkable, tile_at

# ── Spritesheet constants ──────────────────────────────────────────────────
# NPC sheet slicer assumes a fixed 18×26 grid.
# Each character sheet is 216×416, 12 cols × 16 rows, 18×26px per frame.
# Each character: 3 animation frames (walk cycle), 4 directions (D, L, R, U)
# So one character = 3 cols × 4 rows = 12 frames
# 4 characters per row-group, 4 row-groups => 16 characters total
_FRAME_W = 18
_FRAME_H = 26
_ANIM_FRAMES = 3       # walk frames per direction
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

# Character indices (0-15) in row-major order:
# Row-group 0: chars 0-3    (rows 0-3)
# Row-group 1: chars 4-7    (rows 4-7)
# Row-group 2: chars 8-11   (rows 8-11)
# Row-group 3: chars 12-15  (rows 12-15)

_NPC_SHEETS = (
    "Townspeople_Animations.png",
    "MinersConstruction_Animations.png",
    "ForestNpcs_Animations.png",
)
_CHARACTERS_PER_SHEET = 16

_npc_sheets: dict[int, pygame.Surface | None] = {}
_npc_frame_cache: dict[str, pygame.Surface] = {}
_sprite_rng = secrets.SystemRandom()

# Scale target for NPC sprites (match player roughly)
_NPC_DRAW_W = 42
_NPC_DRAW_H = 58
# Footprint radius for NPC-to-NPC yielding.  A smaller value lets guests pass
# through the broad lobby without stopping at an unrealistic visible gap.
_NPC_COLLISION_RADIUS = 8

# Only use the tiles that are actually cinema seats.  SEAT_COLS also spans
# the centre aisle, so filtering the map prevents NPCs from sitting there.
_AUDITORIUM_SEATS = tuple(
    (col, row)
    for row in SEAT_ROWS
    for col in SEAT_COLS
    if tile_at(col, row) == TILE_SEAT
)


def _inside_npc_service_area(col: int, row: int) -> bool:
    """Keep moviegoers in the central, customer-facing circulation area."""
    # These invisible bounds follow the marked lobby lanes: wide around
    # concessions/checkpoint, narrow behind the ticket kiosks, then centered
    # around the queues and exit. The player is deliberately unaffected.
    if 10 <= row <= 14:
        return 3 <= col <= 14
    if 15 <= row <= 17:
        return 2 <= col <= 17
    if 18 <= row <= 24:
        return 4 <= col <= 13
    return True


def _tile_path(start: tuple[int, int], goal: tuple[int, int],
               blocked: set[tuple[int, int]] | None = None,
               can_walk=None) -> list[tuple[int, int]]:
    """Find a deterministic shortest 4-direction route with A*."""
    blocked = blocked or set()
    can_walk = can_walk or is_walkable
    if start == goal and start not in blocked:
        return [start]
    if goal in blocked or not can_walk(*start) or not can_walk(*goal):
        return []

    def neighbours(col: int, row: int):
        dx = goal[0] - col
        dy = goal[1] - row
        horizontal = (1 if dx > 0 else -1, 0) if dx else None
        vertical = (0, 1 if dy > 0 else -1) if dy else None
        # Prefer the axis with the most remaining distance.  The remaining
        # entries allow a route around furniture without introducing chance.
        preferred = [horizontal, vertical] if abs(dx) >= abs(dy) else [vertical, horizontal]
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if direction not in preferred:
                preferred.append(direction)
        for step in preferred:
            if step is not None:
                yield col + step[0], row + step[1]

    def distance(tile: tuple[int, int]) -> int:
        return abs(goal[0] - tile[0]) + abs(goal[1] - tile[1])

    # The insertion order makes equally good routes reproducible.
    frontier = [(distance(start), 0, 0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    insertion_order = 0
    while frontier:
        _, cost, _, (col, row) = heapq.heappop(frontier)
        if cost != cost_so_far.get((col, row)):
            continue
        for nxt in neighbours(col, row):
            if nxt in blocked or not can_walk(*nxt):
                continue
            next_cost = cost + 1
            if next_cost >= cost_so_far.get(nxt, math.inf):
                continue
            came_from[nxt] = (col, row)
            cost_so_far[nxt] = next_cost
            if nxt == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(came_from[path[-1]])
                return list(reversed(path))
            insertion_order += 1
            heapq.heappush(
                frontier,
                (next_cost + distance(nxt), next_cost, insertion_order, nxt),
            )
    return []


def _load_npc_sheet(sheet_idx: int) -> pygame.Surface | None:
    """Load one of the compatible NPC character sheets on demand."""
    if sheet_idx in _npc_sheets:
        return _npc_sheets[sheet_idx]

    path = os.path.join(SPRITES_DIR, _NPC_SHEETS[sheet_idx])
    if os.path.exists(path):
        _npc_sheets[sheet_idx] = pygame.image.load(path).convert_alpha()
    else:
        _npc_sheets[sheet_idx] = None
    return _npc_sheets[sheet_idx]


def _get_npc_frame(character_id: int, direction: int, frame: int) -> pygame.Surface:
    """Extract a frame from the selected sheet and character slot."""
    sheet_idx = (character_id // _CHARACTERS_PER_SHEET) % len(_NPC_SHEETS)
    char_idx = character_id % _CHARACTERS_PER_SHEET
    key = f"npc_{sheet_idx}_{char_idx}_{direction}_{frame}"
    if key in _npc_frame_cache:
        return _npc_frame_cache[key]

    sheet = _load_npc_sheet(sheet_idx)
    if sheet is None:
        # Fallback: colored rectangle
        s = pygame.Surface((_NPC_DRAW_W, _NPC_DRAW_H), pygame.SRCALPHA)
        pygame.draw.rect(s, (200, 100, 100), (4, 4, _NPC_DRAW_W-8, _NPC_DRAW_H-8), border_radius=6)
        _npc_frame_cache[key] = s
        return s

    # Character position in the 12 × 16 sheet grid.  Copying this exact
    # source rectangle keeps adjacent animation cells out of the sprite.
    row_group = char_idx // 4    # which group of 4 rows (0-3)
    col_group = char_idx % 4     # which character within that group (0-3)
    source = pygame.Rect(
        col_group * _ANIM_FRAMES * _FRAME_W + (frame % _ANIM_FRAMES) * _FRAME_W,
        row_group * 4 * _FRAME_H + (direction % 4) * _FRAME_H,
        _FRAME_W,
        _FRAME_H,
    )
    if not sheet.get_rect().contains(source):
        raise ValueError(f"NPC sprite source rect is outside {_NPC_SHEETS[sheet_idx]}: {source}")

    s = sheet.subsurface(source).copy()
    # Keep the supplied pixel art crisp; smooth scaling makes the sprites
    # look soft at the larger in-game size.
    s = pygame.transform.scale(s, (_NPC_DRAW_W, _NPC_DRAW_H))
    _npc_frame_cache[key] = s
    return s


def moviegoer_sprite(character_id: int, frame: int = 0,
                     direction: int = _DIR_DOWN) -> pygame.Surface:
    """Return a real moviegoer animation-sheet frame for use outside the map."""
    return _get_npc_frame(character_id, direction, frame)


# ── NPC Character Names & Personality ─────────────────────────────────────

_NPC_NAMES = [
    "Alex", "Sam", "Jordan", "Casey", "Riley",
    "Morgan", "Avery", "Quinn", "Blake", "Drew",
    "Taylor", "Reese", "Harper", "Skyler", "Finley",
    "Logan",
]

_NPC_IDLE_LINES = [
    "The movie starts soon!",
    "I love this place.",
    "Popcorn smells amazing!",
    "Which movie should I see?",
    "I heard this film is great!",
    "Where's my ticket...",
    "Need more snacks!",
    "Let's find our seats!",
    "This carpet is so plush!",
    "What a cool cinema!",
]


class NPC:
    """A moviegoer that visibly completes the theater visit flow."""

    TICKET_LINE = "ticket_line"
    BUYING_TICKET = "buying_ticket"
    USHER_LINE = "usher_line"
    CHECKING_TICKET = "checking_ticket"
    GOING_TO_SNACK = "going_to_snack"
    SNACK_LINE = "snack_line"
    BUYING_SNACK = "buying_snack"
    ENTERING_AUDITORIUM = "entering_auditorium"
    FINDING_SEAT = "finding_seat"
    SEATED = "seated"
    LEAVING = "leaving"
    LEFT = "left"

    _STATUS = {
        TICKET_LINE: "Ticket line",
        BUYING_TICKET: "Buying ticket",
        USHER_LINE: "Usher line",
        CHECKING_TICKET: "Ticket check",
        GOING_TO_SNACK: "Going to concessions",
        SNACK_LINE: "Concession line",
        BUYING_SNACK: "Buying snacks",
        ENTERING_AUDITORIUM: "Entering theater",
        FINDING_SEAT: "Finding seat",
        SEATED: "Watching movie",
        LEAVING: "Leaving theater",
        LEFT: "Left cinema",
    }

    _ACTION_LINES = {
        BUYING_TICKET: ("One ticket, please!", "I'd like a ticket.", "Ticket for the show, please."),
        CHECKING_TICKET: ("Here's my ticket.", "Ticket ready!", "Please check my ticket."),
        BUYING_SNACK: ("Popcorn, please!", "I'd like some snacks.", "One drink and popcorn!"),
    }

    # The counter sprites are part of the map rather than individual NPC
    # entities, so their half of the conversation is drawn at the active
    # counter while a moviegoer is being served.
    _VENDOR_LINES = {
        BUYING_TICKET: ("Enjoy the show!", "Here is your ticket.", "Next guest, please!"),
        CHECKING_TICKET: ("You're all set.", "Ticket checked—enjoy!", "Have a great movie!"),
        BUYING_SNACK: ("Fresh popcorn coming up!", "That will be ready shortly.", "Enjoy your snacks!"),
    }

    def __init__(self, character_id: int, start_col: int, start_row: int,
                 name: str = "", queue_slot: int = 0,
                 seat: tuple[int, int] | None = None, spawn_delay: float = 0.0):
        self.character_id = character_id
        self.name = name or _NPC_NAMES[character_id % len(_NPC_NAMES)]
        self.queue_slot = queue_slot
        # Reserve a lane once at arrival. Left ticket booths feed the left
        # usher; right booths feed the right usher. This prevents lane hopping.
        self.ticket_lane = queue_slot % len(CASHIER_DESK_COLS)
        self.usher_lane = 0 if self.ticket_lane < 2 else 1
        self.snack_lane = 0 if self.usher_lane == 0 else 2
        self._ticket_lane_locked = False
        # The map has a fixed number of drawn counters. These capacities
        # decide which of those counters can actually serve a visual guest.
        self.cashier_capacity = len(CASHIER_DESK_COLS)
        self.usher_capacity = len(USHER_DESK_COLS)
        self.server_capacity = len(SNACK_DESK_COLS)
        self.ticket_line_depth = queue_slot // len(CASHIER_DESK_COLS)
        self.usher_line_depth = self._line_depth(queue_slot, "usher", self.usher_lane)
        self.snack_line_depth = self._line_depth(queue_slot, "snack", self.snack_lane)
        self.wants_food = random.random() < 0.55
        self.has_ticket = False
        self.ticket_checked = False
        self.has_food = False
        # Each guest has a slightly different idea of a good seat.  Keeping
        # these preferences on the character (rather than on the queue slot)
        # means a new wave naturally fills the auditorium in a different way.
        self.preferred_row = random.choices(SEAT_ROWS, weights=(2, 5, 5, 3))[0]
        self.preferred_side = random.choice((-1, 1))  # left / right block
        self.prefers_company = random.random() < 0.42
        self._seat_tiebreaker = random.uniform(0.0, 1.4)
        # A seat is claimed only after the NPC enters the auditorium.  This
        # lets them react to seats occupied by earlier arrivals.
        self.seat = seat
        self.spawn_delay = max(0.0, spawn_delay)

        # World position
        self.x = float(start_col * TILE_SIZE + TILE_SIZE // 2)
        self.y = float(start_row * TILE_SIZE + TILE_SIZE // 2)

        # Movement and journey state
        self.state = self.TICKET_LINE
        self.direction = _DIR_DOWN
        self.speed = random.uniform(40, 65)  # slower than player
        self._route: list[tuple[int, int]] = []
        self._target_x = self.x
        self._target_y = self.y
        self._service_timer = 0.0
        self._service_duration = 0.0
        self._vendor_text = ""
        self._vendor_timer = 0.0
        self._collision_debug_target: tuple[float, float] | None = None
        self._detour_cooldown = 0.0
        self._occupied_seat_tiles: set[tuple[int, int]] = set()
        # Track a physical block separately from intentional service waits.
        self._stalled_for = 0.0
        self._recovery_cooldown = 0.0
        self._watch_time = 0.0
        # A few guests lose interest early, while others stay until the
        # session ends.  This range is long enough to let them settle in,
        # but short enough for the behaviour to be visible during play.
        self._boredom_limit = random.uniform(24.0, 52.0)
        self.has_left = False
        # Go directly from the entrance to the reserved ticket-line slot.
        # The grid planner chooses the shortest walkable route instead of
        # forcing an NPC to wander through lobby staging points.
        self._set_route([self._ticket_wait_tile()])

        # Animation
        self._anim_t = random.uniform(0, 3)  # offset so NPCs don't sync
        self._frame = 0

        # Speech bubble
        self._speech_text = self._STATUS[self.state]
        self._speech_timer = 9999.0
        try:
            self._font = pygame.font.SysFont("consolas", 11)
        except Exception:
            self._font = pygame.font.Font(None, 11)

    def _cashier_col(self) -> int:
        return CASHIER_DESK_COLS[self.ticket_lane]

    def set_service_capacity(self, cashiers: int, ushers: int, servers: int):
        """Limit service to the map's visible stalls without spawning extras."""
        self.cashier_capacity = max(0, min(len(CASHIER_DESK_COLS), cashiers))
        self.usher_capacity = max(0, min(len(USHER_DESK_COLS), ushers))
        self.server_capacity = max(0, min(len(SNACK_DESK_COLS), servers))

    def _choose_ticket_lane(self, nearby_npcs: list["NPC"] | None):
        """Reserve the least-busy reachable ticket counter before moving.

        A ticket lane used to be assigned only from the arrival number.  That
        can leave several late arrivals in one vertical line while another
        booth is open.  This uses the guests actually at the counters instead.
        """
        active_states = {self.TICKET_LINE, self.BUYING_TICKET}
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        choices = []
        for lane, col in enumerate(CASHIER_DESK_COLS[:self.cashier_capacity]):
            occupants = [
                other for other in nearby_npcs or []
                if other is not self
                and other.state in active_states
                and other.ticket_lane == lane
            ]
            depth = len(occupants)
            if depth <= 2:
                target = col, 20 + depth
            else:
                direction = -1 if col < 10 else 1
                target = max(4, min(13, col + direction * (depth - 2))), 22
            route = _tile_path(start, target, self._gate_blocked_tiles(), self._can_walk)
            if route:
                choices.append((len(occupants), len(route), lane, depth))
        if not choices:
            return
        _, _, lane, depth = min(choices, key=lambda choice: choice[:3])
        self.ticket_lane = lane
        self.ticket_line_depth = depth
        # The chosen ticket side determines the compatible usher checkpoint.
        self.usher_lane = 0 if lane < 2 else 1

    @staticmethod
    def _line_depth(slot: int, line: str, lane: int) -> int:
        """Count only earlier arrivals assigned to this same service lane."""
        depth = 0
        for previous in range(slot):
            previous_usher = 0 if (previous % len(CASHIER_DESK_COLS)) < 2 else 1
            previous_lane = previous_usher if line == "usher" else (0 if previous_usher == 0 else 2)
            if previous_lane == lane:
                depth += 1
        return depth

    def _usher_col(self) -> int:
        return USHER_DESK_COLS[self.usher_lane]

    def _ticket_exit_gap(self) -> int:
        """Open tile immediately beyond the booth the NPC just used."""
        return {
            4: 5,   # gap between booth 1 and booth 2
            7: 8,   # gap between booth 2 and booth 3
            10: 11, # gap between booth 3 and booth 4
            13: 12, # gap before booth 4
        }.get(self._cashier_col(), 11)

    def _ticket_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        """Return a walkable ticket-line slot for the requested live depth."""
        col = self._cashier_col()
        depth = self.ticket_line_depth if depth is None else depth
        if depth <= 2:
            return col, 20 + depth
        direction = -1 if col < 10 else 1
        return max(4, min(13, col + direction * (depth - 2))), 22

    def _ticket_follow_tile(self, depth: int) -> tuple[int, int]:
        """Queue slot that keeps the counter approach tile open.

        Row 19 is the only path from the line to the counter on row 18.  A
        follower standing there can trap the active customer, so the first
        waiting position must stay on row 20.
        """
        return self._ticket_wait_tile(depth)

    def _snack_col(self) -> int:
        return SNACK_DESK_COLS[self.snack_lane]

    def _choose_snack_lane(self, nearby_npcs: list["NPC"] | None):
        """Choose the nearest reachable concession counter with the shortest line.

        Concessions are not tied to the ticket lane.  Looking at the current
        guests lets a moviegoer walk directly to an open stall instead of
        trailing the person ahead toward an already busy one.
        """
        active_states = {self.GOING_TO_SNACK, self.SNACK_LINE, self.BUYING_SNACK}
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        choices = []
        for lane, col in enumerate(SNACK_DESK_COLS[:self.server_capacity]):
            occupants = [
                other for other in nearby_npcs or []
                if other is not self
                and other.state in active_states
                and other.snack_lane == lane
            ]
            route = _tile_path(start, (col, 12), self._gate_blocked_tiles(), self._can_walk)
            if not route:
                continue
            # Queue length is the primary choice.  Route length makes equally
            # open stalls feel purposeful, and lane is a stable final tie-break.
            choices.append((len(occupants), len(route), lane, occupants))
        if not choices:
            return
        _, _, lane, occupants = min(choices, key=lambda choice: choice[:3])
        self.snack_lane = lane
        self.snack_line_depth = len(occupants)

    def _service_approach_tile(self) -> tuple[int, int] | None:
        """The one-tile interaction range immediately in front of each booth."""
        if self.state == self.BUYING_TICKET:
            return self._cashier_col(), 18
        if self.state == self.CHECKING_TICKET:
            return self._usher_col(), 15
        if self.state == self.BUYING_SNACK:
            # Row 11 is directly in front of the concession counter on row
            # 10.  Row 12 is only the queue lane, which made customers look
            # as though they were ordering from empty floor space.
            return self._snack_col(), 11
        return None

    def _can_walk(self, col: int, row: int) -> bool:
        """Apply map collision plus the ticket-controlled usher passage."""
        if not _inside_npc_service_area(col, row):
            return False
        # Seats stay traversable only when empty. This preserves routes from
        # the middle rows while making an occupied or reserved chair a real
        # obstacle instead of floor an NPC can walk through.
        if tile_at(col, row) == TILE_SEAT and (col, row) in self._occupied_seat_tiles:
            return False
        if row == USHER_DESK_ROW:
            # Emergency/session-end departures may cross the same central
            # passage in the opposite direction even if ticket service was
            # interrupted before the guest was checked.
            return (self.ticket_checked or self.state == self.LEAVING) and col in USHER_PASSAGE_COLS
        return is_walkable(col, row)

    def _gate_blocked_tiles(self) -> set[tuple[int, int]]:
        """Tiles excluded from a route by the usher checkpoint rule."""
        if not self.ticket_checked and self.state != self.LEAVING:
            return {(col, USHER_DESK_ROW) for col in range(1, 19)}
        return {
            (col, USHER_DESK_ROW) for col in range(1, 19)
            if col not in USHER_PASSAGE_COLS
        }

    def _snack_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        """Return one distinct concession queue tile for the live depth."""
        col = self._snack_col()
        depth = self.snack_line_depth if depth is None else depth
        if depth == 0:
            return col, 12
        direction = -1 if col < 10 else 1
        # Use the row behind the counter first, then spill into the aisle
        # below it. This avoids giving every late arrival the same end tile.
        if depth <= 4:
            return max(1, min(18, col + direction * depth)), 12
        return max(1, min(18, col + direction * (depth - 4))), 13

    def _usher_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        """Return a walkable staging tile for this NPC's usher queue position."""
        queue_position = self.usher_line_depth if depth is None else depth
        usher_col = self._usher_col()
        if queue_position <= 5:
            return max(1, min(18, usher_col + (-1 if usher_col < 10 else 1)
                              * queue_position)), 15
        # Continue on row 16 once the walkway row is full. The old hard cap
        # at columns 5/13 put every later guest onto one tile.
        direction = -1 if usher_col < 10 else 1
        return max(1, min(18, usher_col + direction * (queue_position - 5))), 16

    def _choose_usher_lane(self, nearby_npcs: list["NPC"] | None):
        """Route ticket holders to the least-busy reachable usher desk."""
        active_states = {self.USHER_LINE, self.CHECKING_TICKET}
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        choices = []
        for lane, col in enumerate(USHER_DESK_COLS[:self.usher_capacity]):
            occupants = [
                other for other in nearby_npcs or []
                if other is not self
                and other.state in active_states
                and other.usher_lane == lane
            ]
            depth = len(occupants)
            if depth == 0:
                target = col, 15
            else:
                direction = -1 if col < 10 else 1
                target = max(5, min(13, col + direction * (depth - 1))), 16
            route = _tile_path(start, target, self._gate_blocked_tiles(), self._can_walk)
            if route:
                choices.append((len(occupants), len(route), lane, depth))
        if not choices:
            return
        _, _, lane, depth = min(choices, key=lambda choice: choice[:3])
        self.usher_lane = lane
        self.usher_line_depth = depth

    def _usher_wait_route(self) -> list[tuple[int, int]]:
        # `_set_route` uses breadth-first search, so one final target gives
        # the guest the shortest valid route from the ticket counter.
        return [self._usher_wait_tile()]

    def _usher_service_route(self) -> list[tuple[int, int]]:
        return [(self._usher_col(), 15)]

    def _near_service_point(self) -> bool:
        """Only begin a transaction when the NPC is close to its counter."""
        if self.state == self.BUYING_TICKET:
            col, row = self._cashier_col(), 17
        elif self.state == self.CHECKING_TICKET:
            col, row = self._usher_col(), 14
        elif self.state == self.BUYING_SNACK:
            col, row = self._snack_col(), 11
        else:
            return False
        px = col * TILE_SIZE + TILE_SIZE // 2
        py = row * TILE_SIZE + TILE_SIZE // 2
        # The customer must be on the approach tile below the booth, not just
        # somewhere nearby in the aisle.
        return math.hypot(self.x - px, self.y - py) <= TILE_SIZE * 1.02

    def _begin_service(self):
        self._service_timer = self._service_duration
        self._speech_text = random.choice(self._ACTION_LINES[self.state])
        self._speech_timer = self._service_duration
        self._vendor_text = random.choice(self._VENDOR_LINES[self.state])
        self._vendor_timer = self._service_duration

    def _vendor_tile(self) -> tuple[int, int] | None:
        """Map location of the vendor currently serving this moviegoer."""
        if self.state == self.BUYING_TICKET:
            return self._cashier_col(), 17
        if self.state == self.CHECKING_TICKET:
            return self._usher_col(), USHER_DESK_ROW
        if self.state == self.BUYING_SNACK:
            return self._snack_col(), 10
        return None

    def _set_route(self, tiles: list[tuple[int, int]]):
        """Expand waypoints into a collision-safe 4-direction tile route."""
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        expanded: list[tuple[int, int]] = []
        for goal in tiles:
            segment = _tile_path(start, goal, self._gate_blocked_tiles(), self._can_walk)
            if not segment:
                # Never turn an unreachable destination into a direct movement
                # target.  That used to let an NPC press into walls after a map
                # edit, which looked like it had chosen somewhere random.
                self._route = []
                self._target_x = self.x
                self._target_y = self.y
                return False
            expanded.extend(segment[1:])
            start = goal
        self._route = expanded
        self._advance_route()
        return True

    def _advance_route(self):
        if self._route:
            col, row = self._route.pop(0)
            self._target_x = float(col * TILE_SIZE + TILE_SIZE // 2)
            self._target_y = float(row * TILE_SIZE + TILE_SIZE // 2)
        else:
            self._target_x = self.x
            self._target_y = self.y

    def _set_state(self, state: str, route: list[tuple[int, int]] | None = None,
                   service_time: float = 0.0):
        self.state = state
        self._speech_text = self._STATUS[state]
        self._speech_timer = 9999.0
        self._service_timer = 0.0
        self._service_duration = service_time
        if route is not None:
            self._set_route(route)

    def _has_queue_leader(self, nearby_npcs: list["NPC"] | None,
                          lane_count: int, active_states: set[str]) -> bool:
        """Whether a lower queue slot is still occupying this service lane."""
        return bool(self._queue_leaders(nearby_npcs, lane_count, active_states))

    def _queue_leaders(self, nearby_npcs: list["NPC"] | None,
                       lane_count: int, active_states: set[str]) -> list["NPC"]:
        """Return the earlier guests still using this service lane."""
        if not nearby_npcs:
            return []
        if lane_count == len(USHER_DESK_COLS):
            lane = self.usher_lane
        elif lane_count == len(SNACK_DESK_COLS):
            lane = self.snack_lane
        else:
            lane = self.ticket_lane
        return [
            other
            for other in nearby_npcs
            if other is not self
            and other.spawn_delay <= 0
            and other.queue_slot < self.queue_slot
            and (
                (other.usher_lane if lane_count == len(USHER_DESK_COLS)
                 else other.snack_lane if lane_count == len(SNACK_DESK_COLS)
                 else other.ticket_lane) == lane
            )
            and other.state in active_states
        ]

    def _arrive_at_step(self, nearby_npcs: list["NPC"] | None = None):
        """Advance only after reaching the front of each line or destination."""
        if self.state == self.TICKET_LINE:
            if self.cashier_capacity == 0:
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(CASHIER_DESK_COLS),
                {self.TICKET_LINE, self.BUYING_TICKET})
            if leaders:
                # Move forward to fill the newly open slot rather than
                # remaining at the arrival-time queue depth.  The person at
                # the counter is not a floor queue slot, hence ``- 1``.
                target = self._ticket_follow_tile(max(0, len(leaders) - 1))
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            self._set_state(self.BUYING_TICKET,
                            [(self._cashier_col(), 18)],
                            1.0 + self.ticket_line_depth * 0.35)
        elif self.state == self.USHER_LINE:
            if self.usher_capacity == 0:
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(USHER_DESK_COLS),
                {self.USHER_LINE, self.CHECKING_TICKET})
            if leaders:
                target = self._usher_wait_tile(len(leaders))
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            self._set_state(self.CHECKING_TICKET,
                            self._usher_service_route(), 0.75)
        elif self.state == self.GOING_TO_SNACK:
            # The walk to the concession area is complete; now take the
            # reserved queue position rather than using the aisle as a line.
            self._set_state(self.SNACK_LINE)
        elif self.state == self.SNACK_LINE:
            if self.server_capacity == 0:
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(SNACK_DESK_COLS),
                {self.SNACK_LINE, self.BUYING_SNACK})
            if leaders:
                # The active customer is already at row 11, not in a floor
                # queue slot, so do not count it when selecting this slot.
                waiting = sum(other.state == self.SNACK_LINE for other in leaders)
                target = self._snack_wait_tile(waiting)
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            # Evaluate this while still in SNACK_LINE, so use the explicit
            # counter-front tile rather than the state-dependent helper.
            self._set_state(self.BUYING_SNACK,
                            [(self._snack_col(), 11)], 1.1)
        elif self.state in (self.BUYING_TICKET, self.CHECKING_TICKET, self.BUYING_SNACK):
            if self._near_service_point():
                self._begin_service()
            else:
                # Re-approach the counter if a future layout change leaves the
                # NPC outside the interaction radius.
                self._set_route([self._service_approach_tile()])
        elif self.state == self.FINDING_SEAT:
            # Another guest may have reached this chair while this NPC was
            # detouring. Never force two people into the same seat: release
            # the old claim and select a currently clear alternative.
            if self._seat_is_clear(self.seat, nearby_npcs):
                self._set_state(self.SEATED)
            else:
                self.seat = None
                replacement = self._claim_available_seat(nearby_npcs)
                if replacement is not None:
                    self._set_route([replacement])
                else:
                    self._start_exit_route()
        elif self.state == self.LEAVING:
            self._set_state(self.LEFT)
            self.has_left = True
        elif self.state == self.ENTERING_AUDITORIUM:
            # The NPC has crossed the four-door theater entrance; only now
            # does it claim an open seat.  Seats being approached count as
            # occupied too, so two guests cannot choose the same one.
            seat = self._claim_available_seat(nearby_npcs)
            if seat is not None:
                self._set_state(self.FINDING_SEAT, [seat])

    def _refresh_queue_target(self, nearby_npcs: list["NPC"] | None):
        """Keep a moving queue's destination in sync while it is blocked.

        Previously a guest only reconsidered its slot after physically
        reaching it. If that tile was still occupied, the guest could never
        arrive and therefore never notice that the line had moved.
        """
        if self.state == self.TICKET_LINE:
            leaders = self._queue_leaders(
                nearby_npcs, len(CASHIER_DESK_COLS),
                {self.TICKET_LINE, self.BUYING_TICKET})
            target = self._ticket_follow_tile(max(0, len(leaders) - 1))
        elif self.state == self.USHER_LINE:
            leaders = self._queue_leaders(
                nearby_npcs, len(USHER_DESK_COLS),
                {self.USHER_LINE, self.CHECKING_TICKET})
            target = self._usher_wait_tile(len(leaders))
        elif self.state == self.SNACK_LINE:
            leaders = self._queue_leaders(
                nearby_npcs, len(SNACK_DESK_COLS),
                {self.SNACK_LINE, self.BUYING_SNACK})
            target = self._snack_wait_tile(
                sum(other.state == self.SNACK_LINE for other in leaders))
        else:
            return

        current_goal = self._route[-1] if self._route else (
            int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        if target != current_goal:
            self._set_route([target])

    def _claim_available_seat(self, nearby_npcs: list["NPC"] | None) -> tuple[int, int] | None:
        """Claim a real, currently unoccupied auditorium seat.

        An explicitly requested seat is used when free; otherwise the guest
        chooses from a personal row/side preference, with a gentle bias toward
        sitting near (but not directly on top of) other moviegoers.  A guest
        walking to a seat reserves it immediately, which makes later guests
        react to the crowd already in the room.
        """
        claimed = {
            other.seat
            for other in nearby_npcs or []
            if other is not self
            and not other.has_left
            and other.seat is not None
        }
        # Include a guest physically standing on a seat even if their state
        # has just changed; a seat is unavailable until the sprite moves away.
        claimed.update(
            (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
            for other in nearby_npcs or []
            if other is not self
            and not other.has_left
            and tile_at(int(other.x // TILE_SIZE), int(other.y // TILE_SIZE)) == TILE_SEAT
        )
        available = [seat for seat in _AUDITORIUM_SEATS if seat not in claimed]
        if not available:
            self.seat = None
            return None
        if self.seat not in available:
            occupied = [
                other.seat for other in nearby_npcs or []
                if other is not self and not other.has_left and other.seat is not None
            ]

            def seat_score(seat: tuple[int, int]) -> float:
                col, row = seat
                # Favour the preferred row and the chosen side of the room.
                score = abs(row - self.preferred_row) * 28
                on_preferred_side = (col < 10) == (self.preferred_side < 0)
                score += 0 if on_preferred_side else 16

                # People who want company choose a nearby open chair; the
                # rest leave a little breathing room.  Directly adjacent
                # seats always receive a large penalty so NPC sprites do not
                # overlap and the crowd remains readable.
                if occupied:
                    distances = [abs(col - other_col) + abs(row - other_row)
                                 for other_col, other_row in occupied]
                    nearest = min(distances)
                    if nearest == 1:
                        score += 38
                    elif self.prefers_company:
                        score += abs(nearest - 2) * 7
                    else:
                        score += max(0, 4 - nearest) * 9

                # A small deterministic per-NPC nudge prevents every guest
                # with the same taste from selecting the same-looking seat.
                score += ((col * 7 + row * 11 + self.character_id * 5)
                          % 9) * self._seat_tiebreaker
                return score

            self.seat = min(available, key=seat_score)
        return self.seat

    def _seat_is_clear(self, seat: tuple[int, int] | None,
                       nearby_npcs: list["NPC"] | None) -> bool:
        """Return whether nobody else owns or is still occupying ``seat``."""
        if seat is None:
            return False
        seat_x = seat[0] * TILE_SIZE + TILE_SIZE // 2
        seat_y = seat[1] * TILE_SIZE + TILE_SIZE // 2
        for other in nearby_npcs or []:
            if other is self or other.has_left:
                continue
            if other.seat == seat:
                return False
            if math.hypot(other.x - seat_x, other.y - seat_y) < TILE_SIZE * 0.6:
                return False
        return True

    def _finish_service(self, nearby_npcs: list["NPC"] | None = None):
        if self.state == self.BUYING_TICKET:
            self.has_ticket = True
            # Leave via the gap beside this kiosk before heading to the usher.
            # A direct shortest route can otherwise cut through a neighbouring
            # ticket lane and bunch moving guests on top of queued customers.
            exit_col = self._ticket_exit_gap()
            self._choose_usher_lane(nearby_npcs)
            self._set_state(
                self.USHER_LINE,
                [(exit_col, 18), (exit_col, 16), self._usher_wait_tile()],
            )
        elif self.state == self.CHECKING_TICKET:
            self.ticket_checked = True
            if self.wants_food:
                # Select a counter from the live concession queues, then take
                # one direct route to its queue position.
                self._choose_snack_lane(nearby_npcs)
                self._set_state(self.GOING_TO_SNACK, [self._snack_wait_tile()])
            else:
                self._start_seat_route()
        elif self.state == self.BUYING_SNACK:
            self.has_food = True
            self._start_seat_route()

    def _start_seat_route(self):
        # Column 10 is an auditorium doorway.  A single target lets the
        # breadth-first planner choose the shortest legal route from either
        # concessions or the usher checkpoint.
        self._set_state(self.ENTERING_AUDITORIUM, [(10, 7)])

    def _start_exit_route(self, movie_finished: bool = False):
        """Walk the guest back out while reserving their chair until clear."""
        if self.state in {self.LEAVING, self.LEFT}:
            return
        # Do not release the reservation here. The sprite is still sitting on
        # the chair and another guest must not claim it until this NPC has
        # physically crossed into a different tile.
        if movie_finished:
            self._speech_text = "Movie's over!"
        else:
            self._speech_text = "I'm heading out."
        # The BFS planner handles the centre corridor, checkpoint and lobby
        # in one pass, producing the shortest legal path to the exterior.
        self._set_state(self.LEAVING, [(10, 24)])

    def _is_queue_state(self) -> bool:
        return self.state in {
            self.TICKET_LINE, self.BUYING_TICKET,
            self.USHER_LINE, self.CHECKING_TICKET,
            self.SNACK_LINE, self.BUYING_SNACK,
        }

    @staticmethod
    def _in_auditorium(x: float, y: float) -> bool:
        """Whether a position is in the seating room or its entry corridor."""
        # Row 8 is the corridor immediately below the auditorium doors. NPCs
        # need to pass each other freely here to avoid trapping departures
        # behind guests still choosing a seat.
        return int(y // TILE_SIZE) <= 8

    def _replan_around_npcs(self, nearby_npcs: list["NPC"] | None,
                            allow_queue_recovery: bool = False) -> bool:
        """Rebuild the current travel leg around NPC-occupied tiles."""
        if (not nearby_npcs or (self._is_queue_state() and not allow_queue_recovery)
                or self._detour_cooldown > 0):
            return False
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        goal = (int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        occupied = {
            (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
            for other in nearby_npcs
            if other is not self and not other.has_left and other.spawn_delay <= 0
        }
        blocked = self._gate_blocked_tiles() | occupied

        # If another guest is standing exactly on our current waypoint, wait
        # for it to clear.  Choosing a perpendicular tile here made NPCs take
        # apparent detours unrelated to their destination.
        if goal in occupied:
            return False

        path = _tile_path(start, goal, blocked, self._can_walk)
        if len(path) <= 1:
            return False
        # Keep the waypoints after the blocked leg.  Replacing the whole
        # route here caused an NPC to reach one detour target and incorrectly
        # advance to its next service action.
        remaining_route = list(self._route)
        self._route = path[1:] + remaining_route
        self._advance_route()
        self._detour_cooldown = 0.35
        return True

    def _recover_from_stall(self, nearby_npcs: list["NPC"] | None) -> bool:
        """Try one safe detour when a guest has not moved for too long.

        Queue members keep their existing destination, so recovery cannot let
        them cut a line. If that destination is occupied, waiting remains the
        correct behaviour and the route is left unchanged.
        """
        if (self._stalled_for < 0.9 or self._recovery_cooldown > 0
                or not nearby_npcs):
            return False
        recovered = self._replan_around_npcs(nearby_npcs, allow_queue_recovery=True)
        self._recovery_cooldown = 0.9
        return recovered

    def update(self, dt: float, nearby_npcs: list["NPC"] | None = None,
               movie_finished: bool = False):
        if self.has_left:
            return
        if self.spawn_delay > 0:
            self.spawn_delay -= dt
            self._frame = 0
            return
        if not self._ticket_lane_locked:
            self._choose_ticket_lane(nearby_npcs)
            self._set_route([self._ticket_wait_tile()])
            self._ticket_lane_locked = True
        self._occupied_seat_tiles = {
            other.seat
            for other in nearby_npcs or []
            if other is not self and not other.has_left and other.seat is not None
        }
        self._occupied_seat_tiles.update(
            (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
            for other in nearby_npcs or []
            if other is not self
            and not other.has_left
            and tile_at(int(other.x // TILE_SIZE), int(other.y // TILE_SIZE)) == TILE_SEAT
        )
        if self.state == self.LEAVING and self.seat is not None:
            current_tile = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
            if current_tile != self.seat:
                # The departure has visibly cleared the chair; it is safe for
                # a new guest to consider it in their next seat search.
                self.seat = None
        self._anim_t += dt
        self._detour_cooldown = max(0.0, self._detour_cooldown - dt)
        self._recovery_cooldown = max(0.0, self._recovery_cooldown - dt)
        self._vendor_timer = max(0.0, self._vendor_timer - dt)
        self._collision_debug_target = None

        # When the session ends, clear the whole building—not only the people
        # already seated.  Guests below the usher line can route directly to
        # the exterior doors; checked guests can also leave from concessions.
        if movie_finished and self.state not in {self.LEAVING, self.LEFT}:
            self._start_exit_route(movie_finished=True)
            return

        if self.state == self.SEATED:
            self._watch_time += dt
            if self._watch_time >= self._boredom_limit:
                self._start_exit_route()
                return

        if self._service_timer > 0:
            self._service_timer -= dt
            self._frame = 0
            if self._service_timer <= 0:
                self._finish_service(nearby_npcs)
            return

        # Re-evaluate line positions before collision movement, not only on
        # arrival. This lets a blocked follower immediately take the newly
        # opened slot instead of waiting forever on a stale waypoint.
        self._refresh_queue_target(nearby_npcs)

        dx = self._target_x - self.x
        dy = self._target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 3:
            self.x, self.y = self._target_x, self._target_y
            self._stalled_for = 0.0
            if self._route:
                self._advance_route()
            else:
                self._frame = 0
                self._arrive_at_step(nearby_npcs)
            return

        if abs(dx) > abs(dy):
            self.direction = _DIR_RIGHT if dx > 0 else _DIR_LEFT
        else:
            self.direction = _DIR_DOWN if dy > 0 else _DIR_UP
        step = min(dist, self.speed * dt)
        next_x = self.x + (dx / dist) * step
        next_y = self.y + (dy / dist) * step
        blocked_by_npc = False
        if nearby_npcs:
            for other in nearby_npcs:
                if other is self or other.has_left or other.spawn_delay > 0:
                    continue
                # The seating room is intentionally a soft-collision zone.
                # Seat ownership still blocks a chair, but people may pass
                # through one another in the aisles/doorway so a departing
                # guest cannot deadlock an arriving guest.
                if (self._in_auditorium(self.x, self.y)
                        or self._in_auditorium(other.x, other.y)):
                    continue
                if math.hypot(next_x - other.x, next_y - other.y) < _NPC_COLLISION_RADIUS * 2:
                    # Right-of-way: the NPC closer to its next waypoint moves
                    # first; the one behind waits. This prevents two people
                    # approaching a shared aisle intersection from deadlocking.
                    self_remaining = math.hypot(self._target_x - self.x,
                                                self._target_y - self.y)
                    other_remaining = math.hypot(other._target_x - other.x,
                                                 other._target_y - other.y)
                    if self_remaining > other_remaining + 2 or (
                            abs(self_remaining - other_remaining) <= 2
                            and self.queue_slot > other.queue_slot):
                        blocked_by_npc = True
                        self._collision_debug_target = (other.x, other.y)
                        break
        if blocked_by_npc:
            if self._replan_around_npcs(nearby_npcs):
                self._stalled_for = 0.0
                self._frame = 0
                return
            self._stalled_for += dt
            if self._recover_from_stall(nearby_npcs):
                self._stalled_for = 0.0
            self._frame = 0
            return

        if self._can_walk(int(next_x // TILE_SIZE), int(next_y // TILE_SIZE)):
            self.x, self.y = next_x, next_y
            self._stalled_for = 0.0
            self._frame = int(self._anim_t / 0.2) % _ANIM_FRAMES
        else:
            # Rebuild after a layout change instead of pressing into a wall.
            self._stalled_for += dt
            self._recover_from_stall(nearby_npcs)
            self._frame = 0

    def draw(self, surface: pygame.Surface, camera):
        if self.spawn_delay > 0:
            return
        sx, sy = camera.world_to_screen(self.x, self.y)

        # Get sprite frame
        sprite = _get_npc_frame(self.character_id, self.direction, self._frame)
        sw, sh = sprite.get_size()

        # Draw shadow
        shadow = pygame.Surface((sw - 8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())
        surface.blit(shadow, (int(sx) - sw // 2 + 4, int(sy) - 2))

        # Draw sprite
        surface.blit(sprite, (int(sx) - sw // 2, int(sy) - sh + 4))

        if DEBUG_NPC_COLLISION_RANGE:
            # Each ring is this NPC's own radius.  Collision starts exactly
            # when two rings touch (the combined radius used in update()).
            pygame.draw.circle(surface, (70, 210, 255), (int(sx), int(sy)),
                               _NPC_COLLISION_RADIUS, 1)
            if self._collision_debug_target:
                tx, ty = camera.world_to_screen(*self._collision_debug_target)
                pygame.draw.line(surface, (255, 70, 70), (int(sx), int(sy)),
                                 (int(tx), int(ty)), 2)

        # Dialogue appears only during an actual counter interaction.
        show_status = self._service_timer > 0
        if show_status and self._speech_text and self._speech_timer > 0:
            alpha = min(255, int(255 * min(1.0, self._speech_timer / 0.5)))
            text_surf = self._font.render(self._speech_text, True, (50, 40, 60))
            tw, th = text_surf.get_size()
            bw = tw + 10
            bh = th + 8

            bubble = pygame.Surface((bw, bh + 4), pygame.SRCALPHA)
            pygame.draw.rect(bubble, (255, 255, 255, 220), (0, 0, bw, bh), border_radius=4)
            pygame.draw.rect(bubble, (150, 140, 160), (0, 0, bw, bh), 1, border_radius=4)
            # Tail
            pygame.draw.polygon(bubble, (255, 255, 255, 220),
                                [(bw // 2 - 3, bh), (bw // 2 + 3, bh), (bw // 2, bh + 4)])
            bubble.blit(text_surf, (5, 4))
            bubble.set_alpha(alpha)

            bx = int(sx) - bw // 2
            by = int(sy) - sh - bh - 6
            surface.blit(bubble, (bx, by))

        # Reply from the ticket seller, usher, or concession vendor.  This
        # anchors the second bubble to the stall sprite so the interaction is
        # readable as a conversation rather than a floating status message.
        vendor_tile = self._vendor_tile()
        if show_status and vendor_tile and self._vendor_text and self._vendor_timer > 0:
            vx, vy = camera.world_to_screen(
                vendor_tile[0] * TILE_SIZE + TILE_SIZE // 2,
                vendor_tile[1] * TILE_SIZE + TILE_SIZE // 2,
            )
            text_surf = self._font.render(self._vendor_text, True, (48, 40, 58))
            tw, th = text_surf.get_size()
            bw, bh = tw + 10, th + 8
            bubble = pygame.Surface((bw, bh + 4), pygame.SRCALPHA)
            pygame.draw.rect(bubble, (255, 248, 220, 230), (0, 0, bw, bh), border_radius=4)
            pygame.draw.rect(bubble, (166, 122, 65), (0, 0, bw, bh), 1, border_radius=4)
            pygame.draw.polygon(bubble, (255, 248, 220, 230),
                                [(bw // 2 - 3, bh), (bw // 2 + 3, bh), (bw // 2, bh + 4)])
            bubble.blit(text_surf, (5, 4))
            bubble.set_alpha(min(255, int(255 * min(1.0, self._vendor_timer / 0.5))))
            surface.blit(bubble, (int(vx) - bw // 2, int(vy) - bh - 18))


def build_npcs(count: int = 5, slot_offset: int = 0) -> list[NPC]:
    """Create moviegoers arriving at the lobby entrance for the full journey."""
    npcs = []
    # Pick across all available sheets, keeping the initial crowd varied.
    # Appearance selection intentionally bypasses the reproducible simulation
    # seed: every new game uses a fresh mix from the available character files.
    character_ids = _sprite_rng.sample(
        range(_CHARACTERS_PER_SHEET * len(_NPC_SHEETS)),
        min(count, _CHARACTERS_PER_SHEET * len(_NPC_SHEETS)),
    )

    # Spawn positions — the first frame is at the actual entrance doors, then
    # each NPC walks into the lobby before joining a line.
    spawn_spots = [
        (9, 24), (10, 24), (9, 23), (10, 23),
    ]
    random.shuffle(spawn_spots)
    for i, character_id in enumerate(character_ids):
        col, row = spawn_spots[i % len(spawn_spots)]
        name = _NPC_NAMES[character_id % len(_NPC_NAMES)]
        npc = NPC(
            character_id, col, row, name,
            queue_slot=slot_offset + i,
            spawn_delay=(i * random.uniform(0.35, 0.8)),
        )
        npcs.append(npc)

    return npcs
