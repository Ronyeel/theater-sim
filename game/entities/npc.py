"""
CinePlex Dreams — NPC Entities
Ambient townspeople that wander around the cinema lobby, making the world feel alive.
Uses a mix of the character animation sheets in assets/sprites/.
"""
import os
import pygame
import random
import math
from collections import deque
from game.settings import (
    TILE_SIZE, SPRITES_DIR, CASHIER_DESK_COLS, USHER_DESK_COLS,
    SNACK_DESK_COLS, SEAT_COLS, SEAT_ROWS, TILE_SEAT,
    USHER_DESK_ROW, USHER_PASSAGE_COLS,
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

# Scale target for NPC sprites (match player roughly)
_NPC_DRAW_W = 42
_NPC_DRAW_H = 58
_NPC_COLLISION_RADIUS = 15

# Only use the tiles that are actually cinema seats.  SEAT_COLS also spans
# the centre aisle, so filtering the map prevents NPCs from sitting there.
_AUDITORIUM_SEATS = tuple(
    (col, row)
    for row in SEAT_ROWS
    for col in SEAT_COLS
    if tile_at(col, row) == TILE_SEAT
)


def _tile_path(start: tuple[int, int], goal: tuple[int, int],
               blocked: set[tuple[int, int]] | None = None) -> list[tuple[int, int]]:
    """Find a 4-direction path over walkable map tiles."""
    blocked = blocked or set()
    if start == goal:
        return [start]
    frontier = deque([start])
    came_from = {start: None}
    while frontier:
        col, row = frontier.popleft()
        for nxt in ((col + 1, row), (col - 1, row),
                    (col, row + 1), (col, row - 1)):
            if nxt in came_from or nxt in blocked or not is_walkable(*nxt):
                continue
            came_from[nxt] = (col, row)
            if nxt == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(came_from[path[-1]])
                return list(reversed(path))
            frontier.append(nxt)
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
        self._queue_wait_timer = 0.0
        self._queue_wait_started = False
        self._detour_cooldown = 0.0
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

    def _ticket_wait_tile(self) -> tuple[int, int]:
        """Return a unique walkable slot for this ticket-line depth."""
        col = self._cashier_col()
        depth = self.ticket_line_depth
        if depth <= 2:
            return col, 20 + depth
        direction = -1 if col < 10 else 1
        return max(1, min(18, col + direction * (depth - 2))), 22

    def _snack_col(self) -> int:
        return SNACK_DESK_COLS[self.snack_lane]

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
        if row == USHER_DESK_ROW:
            return self.ticket_checked and col in USHER_PASSAGE_COLS
        return is_walkable(col, row)

    def _gate_blocked_tiles(self) -> set[tuple[int, int]]:
        """Tiles excluded from a route by the usher checkpoint rule."""
        if not self.ticket_checked:
            return {(col, USHER_DESK_ROW) for col in range(1, 19)}
        return {
            (col, USHER_DESK_ROW) for col in range(1, 19)
            if col not in USHER_PASSAGE_COLS
        }

    def _snack_wait_tile(self) -> tuple[int, int]:
        """Spread concession customers along the open row behind the counter."""
        col = self._snack_col()
        if self.snack_line_depth == 0:
            return col, 12
        direction = -1 if col < 10 else 1
        return max(1, min(18, col + direction * self.snack_line_depth)), 12

    def _usher_wait_tile(self) -> tuple[int, int]:
        """Return a walkable staging tile for this NPC's usher queue position."""
        queue_position = self.queue_slot // len(USHER_DESK_COLS)
        usher_col = self._usher_col()
        if queue_position == 0:
            return usher_col, 15
        # Row 17 contains cashier desks, so the usher queue expands sideways
        # on row 16 instead of trying to line up through those solid tiles.
        direction = -1 if usher_col < 10 else 1
        return max(1, min(18, usher_col + direction * (queue_position - 1))), 16

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

    def _set_route(self, tiles: list[tuple[int, int]]):
        """Expand waypoints into a collision-safe 4-direction tile route."""
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        expanded: list[tuple[int, int]] = []
        for goal in tiles:
            segment = _tile_path(start, goal, self._gate_blocked_tiles())
            if segment:
                expanded.extend(segment[1:])
            else:
                # Keep the behavior recoverable if a future map edit blocks a
                # waypoint; the movement loop will retry the direct tile.
                expanded.append(goal)
            start = goal
        self._route = expanded
        self._advance_route()

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
        if state in (self.TICKET_LINE, self.USHER_LINE, self.SNACK_LINE):
            self._queue_wait_started = False
            self._queue_wait_timer = 0.0
        self._service_timer = 0.0
        self._service_duration = service_time
        if route is not None:
            self._set_route(route)

    def _has_queue_leader(self, nearby_npcs: list["NPC"] | None,
                          lane_count: int, active_states: set[str]) -> bool:
        """Whether a lower queue slot is still occupying this service lane."""
        if not nearby_npcs:
            return False
        if lane_count == len(USHER_DESK_COLS):
            lane = self.usher_lane
        elif lane_count == len(SNACK_DESK_COLS):
            lane = self.snack_lane
        else:
            lane = self.ticket_lane
        return any(
            other is not self
            and other.spawn_delay <= 0
            and other.queue_slot < self.queue_slot
            and (
                (other.usher_lane if lane_count == len(USHER_DESK_COLS)
                 else other.snack_lane if lane_count == len(SNACK_DESK_COLS)
                 else other.ticket_lane) == lane
            )
            and other.state in active_states
            for other in nearby_npcs
        )

    def _arrive_at_step(self, nearby_npcs: list["NPC"] | None = None):
        """Advance only after reaching the front of each line or destination."""
        if self.state == self.TICKET_LINE:
            if (self.ticket_line_depth and not self._queue_wait_started
                    and self._has_queue_leader(
                        nearby_npcs, len(CASHIER_DESK_COLS),
                        {self.TICKET_LINE, self.BUYING_TICKET})):
                self._queue_wait_started = True
                self._queue_wait_timer = 1.2 * self.ticket_line_depth
                return
            self._set_state(self.BUYING_TICKET,
                            [(self._cashier_col(), 18)],
                            1.0 + self.ticket_line_depth * 0.35)
        elif self.state == self.USHER_LINE:
            if (self.usher_line_depth and not self._queue_wait_started
                    and self._has_queue_leader(
                        nearby_npcs, len(USHER_DESK_COLS),
                        {self.USHER_LINE, self.CHECKING_TICKET})):
                self._queue_wait_started = True
                self._queue_wait_timer = 0.8 * self.usher_line_depth
                return
            self._set_state(self.CHECKING_TICKET,
                            self._usher_service_route(), 0.75)
        elif self.state == self.GOING_TO_SNACK:
            # The walk to the concession area is complete; now take the
            # reserved queue position rather than using the aisle as a line.
            self._set_state(self.SNACK_LINE)
        elif self.state == self.SNACK_LINE:
            if (self.snack_line_depth and not self._queue_wait_started
                    and self._has_queue_leader(
                        nearby_npcs, len(SNACK_DESK_COLS),
                        {self.SNACK_LINE, self.BUYING_SNACK})):
                self._queue_wait_started = True
                self._queue_wait_timer = 1.0 * self.snack_line_depth
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
            self._set_state(self.SEATED)
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
            and other.seat is not None
            and other.state in {self.FINDING_SEAT, self.SEATED}
        }
        available = [seat for seat in _AUDITORIUM_SEATS if seat not in claimed]
        if not available:
            self.seat = None
            return None
        if self.seat not in available:
            occupied = [
                other.seat for other in nearby_npcs or []
                if other is not self and other.seat is not None
                and other.state in {self.FINDING_SEAT, self.SEATED}
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

    def _finish_service(self):
        if self.state == self.BUYING_TICKET:
            self.has_ticket = True
            # Stop below the checkpoint, then join the usher line.
            self._set_state(self.USHER_LINE, self._usher_wait_route())
        elif self.state == self.CHECKING_TICKET:
            self.ticket_checked = True
            if self.wants_food:
                # One goal-focused path from the usher to the assigned snack
                # queue slot.  This can dynamically replan around aisle traffic.
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
        """Release the chair and walk the guest back out through the doors."""
        if self.state in {self.LEAVING, self.LEFT}:
            return
        self.seat = None
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

    def _replan_around_npcs(self, nearby_npcs: list["NPC"] | None) -> bool:
        """Rebuild the current travel leg around NPC-occupied tiles."""
        if (not nearby_npcs or self._is_queue_state()
                or self._detour_cooldown > 0):
            return False
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        goal = (int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        occupied = {
            (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
            for other in nearby_npcs
            if other is not self and other.spawn_delay <= 0
        }
        blocked = self._gate_blocked_tiles() | occupied

        # If another guest is standing exactly on our current waypoint, an
        # A* route to that tile cannot exist.  Take an open perpendicular
        # tile first, then retry the original route from the new direction.
        if goal in occupied:
            candidates = []
            for col, row in (
                (start[0] + 1, start[1]), (start[0] - 1, start[1]),
                (start[0], start[1] + 1), (start[0], start[1] - 1),
            ):
                tile = (col, row)
                if tile in blocked or not self._can_walk(col, row):
                    continue
                # Prefer a side-step that still points generally toward the
                # goal, but leave room around other people.
                crowd_distance = min(
                    (abs(col - ox) + abs(row - oy) for ox, oy in occupied),
                    default=4,
                )
                score = abs(col - goal[0]) + abs(row - goal[1]) - crowd_distance * 0.35
                candidates.append((score, tile))
            if not candidates:
                return False
            _, detour = min(candidates, key=lambda item: item[0])
            route_to_detour = _tile_path(start, detour, blocked)
            if len(route_to_detour) <= 1:
                return False
            # Keep the original target and any later waypoints. Once clear,
            # the NPC resumes its intended journey without skipping a step.
            self._route = route_to_detour[1:] + [goal] + list(self._route)
            self._advance_route()
            self._detour_cooldown = 0.35
            return True

        path = _tile_path(start, goal, blocked)
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

    def update(self, dt: float, nearby_npcs: list["NPC"] | None = None,
               movie_finished: bool = False):
        if self.has_left:
            return
        if self.spawn_delay > 0:
            self.spawn_delay -= dt
            self._frame = 0
            return
        self._anim_t += dt
        self._detour_cooldown = max(0.0, self._detour_cooldown - dt)

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

        if self._queue_wait_timer > 0:
            self._queue_wait_timer -= dt
            self._frame = 0
            return

        if self._service_timer > 0:
            self._service_timer -= dt
            self._frame = 0
            if self._service_timer <= 0:
                self._finish_service()
            return

        dx = self._target_x - self.x
        dy = self._target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 3:
            self.x, self.y = self._target_x, self._target_y
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
                if other is self or other.spawn_delay > 0:
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
                        break
        if blocked_by_npc and self._replan_around_npcs(nearby_npcs):
            self._frame = 0
            return

        if not blocked_by_npc and self._can_walk(
                int(next_x // TILE_SIZE), int(next_y // TILE_SIZE)):
            self.x, self.y = next_x, next_y
            self._frame = int(self._anim_t / 0.2) % _ANIM_FRAMES
        else:
            # All routes use walkable waypoints; a blocked step simply retries.
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


def build_npcs(count: int = 5, slot_offset: int = 0) -> list[NPC]:
    """Create moviegoers arriving at the lobby entrance for the full journey."""
    npcs = []
    # Pick across all available sheets, keeping the initial crowd varied.
    character_ids = random.sample(
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
