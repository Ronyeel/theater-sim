import os
import pygame
import random
import secrets
import math
import heapq
from game.settings import (
    TILE_SIZE, MAP_COLS, SPRITES_DIR, CASHIER_DESK_COLS, USHER_DESK_COLS,
    SNACK_DESK_COLS, SEAT_COLS, SEAT_ROWS, TILE_SEAT,
    USHER_DESK_ROW, USHER_PASSAGE_COLS, DEBUG_NPC_COLLISION_RANGE,
)

from game.core.tilemap import is_walkable, tile_at

_FRAME_W = 18
_FRAME_H = 26
_ANIM_FRAMES = 3
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3


_NPC_SHEETS = (
    "Townspeople_Animations.png",
    "MinersConstruction_Animations.png",
    "ForestNpcs_Animations.png",
)
_CHARACTERS_PER_SHEET = 16

_npc_sheets: dict[int, pygame.Surface | None] = {}
_npc_frame_cache: dict[str, pygame.Surface] = {}
_sprite_rng = secrets.SystemRandom()
_path_cache: dict[tuple, list[tuple[int, int]]] = {}
_shadow_surf: pygame.Surface | None = None
_queue_counter: int = 0


def _next_queue_seq() -> int:
    global _queue_counter
    _queue_counter += 1
    return _queue_counter


def _get_shadow_surf() -> pygame.Surface:

    global _shadow_surf
    if _shadow_surf is None:
        _shadow_surf = pygame.Surface((_NPC_DRAW_W - 8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(_shadow_surf, (0, 0, 0, 40), _shadow_surf.get_rect())
    return _shadow_surf

_NPC_DRAW_W = 42
_NPC_DRAW_H = 58
_NPC_COLLISION_RADIUS = 6


_AUDITORIUM_SEATS = tuple(
    (col, row)
    for row in SEAT_ROWS
    for col in SEAT_COLS
    if tile_at(col, row) == TILE_SEAT
)

_LEFT_LOUNGE_TILES = (
    (2, 20), (1, 20), (1, 21),
    (2, 21), (2, 22), (1, 22),
    (4, 22), (5, 22), (6, 22),
    (2, 19), (1, 19), (4, 20),
)

_RIGHT_LOUNGE_TILES = (
    (17, 20), (18, 20), (18, 21),
    (17, 21), (17, 22), (18, 22),
    (14, 22), (13, 22), (12, 22),
    (17, 19), (18, 19), (14, 20),
)


def _inside_npc_service_area(col: int, row: int) -> bool:
    if 10 <= row <= 14:
        return 2 <= col <= 17
    if 15 <= row <= 17:
        return 2 <= col <= 17
    if 18 <= row <= 24:
        return 1 <= col <= 18
    return True


def _tile_path(start: tuple[int, int], goal: tuple[int, int],
               blocked: set[tuple[int, int]] | None = None,
               can_walk=None) -> list[tuple[int, int]]:
    blocked = blocked or set()
    can_walk = can_walk or is_walkable
    if start == goal and start not in blocked:
        return [start]
    if goal in blocked or not can_walk(*start) or not can_walk(*goal):
        return []

    cache_key = None
    if can_walk is is_walkable:
        cache_key = (start, goal, tuple(sorted(blocked)) if blocked else ())
        if cache_key in _path_cache:
            return list(_path_cache[cache_key])

    def neighbours(col: int, row: int):
        dx = goal[0] - col
        dy = goal[1] - row
        horizontal = (1 if dx > 0 else -1, 0) if dx else None
        vertical = (0, 1 if dy > 0 else -1) if dy else None
        preferred = [horizontal, vertical] if abs(dx) >= abs(dy) else [vertical, horizontal]
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if direction not in preferred:
                preferred.append(direction)
        for step in preferred:
            if step is not None:
                yield col + step[0], row + step[1]

    def distance(tile: tuple[int, int]) -> int:
        return abs(goal[0] - tile[0]) + abs(goal[1] - tile[1])

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
                res = list(reversed(path))
                if cache_key is not None:
                    _path_cache[cache_key] = res
                return list(res)
            insertion_order += 1
            heapq.heappush(
                frontier,
                (next_cost + distance(nxt), next_cost, insertion_order, nxt),
            )
    return []


def _load_npc_sheet(sheet_idx: int) -> pygame.Surface | None:
    if sheet_idx in _npc_sheets:
        return _npc_sheets[sheet_idx]

    path = os.path.join(SPRITES_DIR, _NPC_SHEETS[sheet_idx])
    if os.path.exists(path):
        _npc_sheets[sheet_idx] = pygame.image.load(path).convert_alpha()
    else:
        _npc_sheets[sheet_idx] = None
    return _npc_sheets[sheet_idx]


def _get_npc_frame(character_id: int, direction: int, frame: int) -> pygame.Surface:
    sheet_idx = (character_id // _CHARACTERS_PER_SHEET) % len(_NPC_SHEETS)
    char_idx = character_id % _CHARACTERS_PER_SHEET
    key = f"npc_{sheet_idx}_{char_idx}_{direction}_{frame}"
    if key in _npc_frame_cache:
        return _npc_frame_cache[key]

    sheet = _load_npc_sheet(sheet_idx)
    if sheet is None:
        s = pygame.Surface((_NPC_DRAW_W, _NPC_DRAW_H), pygame.SRCALPHA)
        pygame.draw.rect(s, (200, 100, 100), (4, 4, _NPC_DRAW_W-8, _NPC_DRAW_H-8), border_radius=6)
        _npc_frame_cache[key] = s
        return s

    row_group = char_idx // 4
    col_group = char_idx % 4
    source = pygame.Rect(
        col_group * _ANIM_FRAMES * _FRAME_W + (frame % _ANIM_FRAMES) * _FRAME_W,
        row_group * 4 * _FRAME_H + (direction % 4) * _FRAME_H,
        _FRAME_W,
        _FRAME_H,
    )
    if not sheet.get_rect().contains(source):
        raise ValueError(f"NPC sprite source rect is outside {_NPC_SHEETS[sheet_idx]}: {source}")

    s = sheet.subsurface(source).copy()
    s = pygame.transform.scale(s, (_NPC_DRAW_W, _NPC_DRAW_H))
    _npc_frame_cache[key] = s
    return s


def moviegoer_sprite(character_id: int, frame: int = 0,
                     direction: int = _DIR_DOWN) -> pygame.Surface:
    return _get_npc_frame(character_id, direction, frame)


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
        self.ticket_lane = queue_slot % len(CASHIER_DESK_COLS)
        self.usher_lane = 0 if self.ticket_lane < 2 else 1
        self.snack_lane = 0 if self.usher_lane == 0 else 2
        self._ticket_lane_locked = False
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
        self.preferred_row = random.choice(SEAT_ROWS)
        self.preferred_side = random.choice((-1, 1))
        self.prefers_company = random.random() < 0.42
        self._seat_tiebreaker = random.uniform(0.0, 1.4)
        self.seat = seat
        self.spawn_delay = max(0.0, spawn_delay)

        self.x = float(start_col * TILE_SIZE + TILE_SIZE // 2)
        self.y = float(start_row * TILE_SIZE + TILE_SIZE // 2)

        self.state = self.TICKET_LINE
        self.ticket_seq = _next_queue_seq()
        self.usher_seq = 0
        self.snack_seq = 0
        self.direction = _DIR_DOWN
        self.speed = random.uniform(40, 65)
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
        self._wait_patience = random.uniform(120.0, 240.0)
        self._time_waiting = 0.0
        self._patience_extended = False
        self._stalled_for = 0.0
        self._recovery_cooldown = 0.0
        self._watch_time = 0.0

        self._boredom_limit = random.uniform(24.0, 52.0)
        self.has_left = False
        self._set_route([self._ticket_wait_tile()])

        self._anim_t = random.uniform(0, 3)
        self._frame = 0

        self._speech_text = self._STATUS[self.state]
        self._speech_timer = 9999.0
        try:
            self._font = pygame.font.SysFont("consolas", 11)
        except Exception:
            self._font = pygame.font.Font(None, 11)

    def _cashier_col(self) -> int:
        return CASHIER_DESK_COLS[self.ticket_lane]

    def set_service_capacity(self, cashiers: int, ushers: int, servers: int):
        self.cashier_capacity = max(0, min(len(CASHIER_DESK_COLS), cashiers))
        self.usher_capacity = max(0, min(len(USHER_DESK_COLS), ushers))
        self.server_capacity = max(0, min(len(SNACK_DESK_COLS), servers))

        if self.cashier_capacity == 0 and self.state in (self.TICKET_LINE, self.BUYING_TICKET):
            self._speech_text = "Theater is closed!"
            self._speech_timer = 2.5
            self._start_exit_route()
        elif self.usher_capacity == 0 and self.state in (self.USHER_LINE, self.CHECKING_TICKET):
            self._speech_text = "No ushers on duty!"
            self._speech_timer = 2.5
            self._start_exit_route()
        elif self.server_capacity == 0 and self.state in (self.SNACK_LINE, self.BUYING_SNACK):
            if self.ticket_checked:
                self._start_seat_route()
            else:
                self._speech_text = "Concessions closed!"
                self._speech_timer = 2.0
                self._start_exit_route()

    def _choose_ticket_lane(self, nearby_npcs: list["NPC"] | None):
        if self.cashier_capacity <= 0:
            self._speech_text = "Theater is closed!"
            self._speech_timer = 2.5
            self._start_exit_route()
            return

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
            target = self._calc_ticket_wait_tile(col, depth)
            route = _tile_path(start, target, self._gate_blocked_tiles(), self._can_walk)
            if route:
                choices.append((len(occupants), len(route), lane, depth))
        if not choices:
            self._speech_text = "No open ticket lanes!"
            self._speech_timer = 2.5
            self._start_exit_route()
            return
        _, _, lane, depth = min(choices, key=lambda choice: choice[:3])

        self.ticket_lane = lane
        self.ticket_line_depth = depth
        self.usher_lane = 0 if lane < 2 else 1

    @staticmethod
    def _line_depth(slot: int, line: str, lane: int) -> int:
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
        return {
            4: 5,
            7: 8,
            10: 11,
            13: 12,
        }.get(self._cashier_col(), 11)

    @staticmethod
    def _calc_ticket_wait_tile(col: int, depth: int) -> tuple[int, int]:
        if depth == 0:
            return col, 19
        if depth == 1:
            return col, 20
        if depth == 2:
            return col, 22

        if col < 10:
            tiles = _LEFT_LOUNGE_TILES
        else:
            tiles = _RIGHT_LOUNGE_TILES

        idx = depth - 3
        if idx < len(tiles):
            return tiles[idx]
        return tiles[idx % len(tiles)]


    def _ticket_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        col = self._cashier_col()
        depth = self.ticket_line_depth if depth is None else depth
        return self._calc_ticket_wait_tile(col, depth)

    def _ticket_follow_tile(self, depth: int) -> tuple[int, int]:
        return self._ticket_wait_tile(depth)

    def _snack_col(self) -> int:
        return SNACK_DESK_COLS[self.snack_lane]

    def _choose_snack_lane(self, nearby_npcs: list["NPC"] | None):
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
            choices.append((len(occupants), len(route), lane, occupants))
        if not choices:
            return
        _, _, lane, occupants = min(choices, key=lambda choice: choice[:3])
        self.snack_lane = lane
        self.snack_line_depth = len(occupants)

    def _service_approach_tile(self) -> tuple[int, int] | None:
        if self.state == self.BUYING_TICKET:
            return self._cashier_col(), 18
        if self.state == self.CHECKING_TICKET:
            return self._usher_col(), 15
        if self.state == self.BUYING_SNACK:
            return self._snack_col(), 11
        return None

    def _can_walk(self, col: int, row: int) -> bool:
        if not _inside_npc_service_area(col, row):
            return False
        if tile_at(col, row) == TILE_SEAT and (col, row) in self._occupied_seat_tiles:
            return False
        if row == USHER_DESK_ROW:
            return (self.ticket_checked or self.state == self.LEAVING) and col in USHER_PASSAGE_COLS
        return is_walkable(col, row)

    def _gate_blocked_tiles(self) -> set[tuple[int, int]]:
        if not self.ticket_checked and self.state != self.LEAVING:
            return {(col, USHER_DESK_ROW) for col in range(1, 19)}
        return {
            (col, USHER_DESK_ROW) for col in range(1, 19)
            if col not in USHER_PASSAGE_COLS
        }

    def _snack_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        col = self._snack_col()
        depth = self.snack_line_depth if depth is None else depth
        if depth == 0:
            return col, 12
        direction = -1 if col < 10 else 1
        if depth <= 4:
            return max(1, min(18, col + direction * depth)), 12
        return max(1, min(18, col + direction * (depth - 4))), 13

    @staticmethod
    def _calc_usher_wait_tile(usher_col: int, depth: int) -> tuple[int, int]:
        direction = -1 if usher_col < 10 else 1
        if depth == 0:
            return usher_col, 15
        if depth <= 6:
            col = usher_col + direction * depth
            return max(1, min(18, col)), 15
        col = (usher_col + direction * 6) - direction * (depth - 6)
        return max(1, min(18, col)), 16

    def _usher_wait_tile(self, depth: int | None = None) -> tuple[int, int]:
        queue_position = self.usher_line_depth if depth is None else depth
        return self._calc_usher_wait_tile(self._usher_col(), queue_position)

    def _choose_usher_lane(self, nearby_npcs: list["NPC"] | None):
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
            target = self._calc_usher_wait_tile(col, depth)
            route = _tile_path(start, target, self._gate_blocked_tiles(), self._can_walk)
            if route:
                choices.append((len(occupants), len(route), lane, depth))
        if not choices:
            return
        _, _, lane, depth = min(choices, key=lambda choice: choice[:3])
        self.usher_lane = lane
        self.usher_line_depth = depth


    def _usher_wait_route(self) -> list[tuple[int, int]]:
        return [self._usher_wait_tile()]

    def _usher_service_route(self) -> list[tuple[int, int]]:
        return [(self._usher_col(), 15)]

    def _near_service_point(self) -> bool:
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
        return math.hypot(self.x - px, self.y - py) <= TILE_SIZE * 1.02

    def _begin_service(self):
        self._service_timer = self._service_duration
        self._speech_text = random.choice(self._ACTION_LINES[self.state])
        self._speech_timer = self._service_duration
        self._vendor_text = random.choice(self._VENDOR_LINES[self.state])
        self._vendor_timer = self._service_duration

    def _vendor_tile(self) -> tuple[int, int] | None:
        if self.state == self.BUYING_TICKET:
            return self._cashier_col(), 17
        if self.state == self.CHECKING_TICKET:
            return self._usher_col(), USHER_DESK_ROW
        if self.state == self.BUYING_SNACK:
            return self._snack_col(), 10
        return None

    def _set_route(self, tiles: list[tuple[int, int]]):
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        expanded: list[tuple[int, int]] = []
        for goal in tiles:
            segment = _tile_path(start, goal, self._gate_blocked_tiles(), self._can_walk)
            if not segment:
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

    def _orient_for_queue(self):
        if self.state in (self.BUYING_TICKET, self.BUYING_SNACK, self.CHECKING_TICKET):
            self.direction = _DIR_UP
        elif self.state == self.TICKET_LINE:
            if self.ticket_line_depth <= 3:
                self.direction = _DIR_UP
            else:
                self.direction = _DIR_LEFT if self._cashier_col() >= 10 else _DIR_RIGHT
        elif self.state == self.USHER_LINE:
            if self.usher_line_depth <= 6:
                self.direction = _DIR_RIGHT if self._usher_col() < 10 else _DIR_LEFT
            else:
                self.direction = _DIR_LEFT if self._usher_col() < 10 else _DIR_RIGHT
        elif self.state == self.SNACK_LINE:
            self.direction = _DIR_UP

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
        return bool(self._queue_leaders(nearby_npcs, lane_count, active_states))

    def _queue_leaders(self, nearby_npcs: list["NPC"] | None,
                       lane_count: int, active_states: set[str]) -> list["NPC"]:
        if not nearby_npcs:
            return []
        if lane_count == len(USHER_DESK_COLS):
            lane = self.usher_lane
            def is_leader(other):
                if other.state not in active_states or other.usher_lane != lane:
                    return False
                if self.y <= 15.5 * TILE_SIZE and other.y >= 19.5 * TILE_SIZE:
                    return False
                return (other.usher_seq, other.queue_slot) < (self.usher_seq, self.queue_slot)

        elif lane_count == len(SNACK_DESK_COLS):
            lane = self.snack_lane
            def is_leader(other):
                if other.state not in active_states or other.snack_lane != lane:
                    return False
                return (other.snack_seq, other.queue_slot) < (self.snack_seq, self.queue_slot)
        else:
            lane = self.ticket_lane
            is_leader = lambda other: (other.ticket_seq, other.queue_slot) < (self.ticket_seq, self.queue_slot)

        return [
            other
            for other in nearby_npcs
            if other is not self
            and other.spawn_delay <= 0
            and is_leader(other)
            and (
                (other.usher_lane if lane_count == len(USHER_DESK_COLS)
                 else other.snack_lane if lane_count == len(SNACK_DESK_COLS)
                 else other.ticket_lane) == lane
            )
            and other.state in active_states
        ]


    def _arrive_at_step(self, nearby_npcs: list["NPC"] | None = None):
        if self.state == self.TICKET_LINE:
            if self.cashier_capacity <= 0:
                self._speech_text = "Waiting for cashier..."
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(CASHIER_DESK_COLS),
                {self.TICKET_LINE, self.BUYING_TICKET})
            if leaders:
                target = self._ticket_follow_tile(max(0, len(leaders) - 1))
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            self._set_state(self.BUYING_TICKET,
                            [(self._cashier_col(), 18)],
                            1.0 + self.ticket_line_depth * 0.35)
        elif self.state == self.USHER_LINE:
            if self.usher_capacity <= 0:
                self._speech_text = "Waiting for usher..."
                return
            desk_occupied = any(
                other is not self and not other.has_left
                and other.state == self.CHECKING_TICKET
                and other.usher_lane == self.usher_lane
                for other in nearby_npcs or []
            )
            leaders = self._queue_leaders(
                nearby_npcs, len(USHER_DESK_COLS),
                {self.USHER_LINE, self.CHECKING_TICKET})
            if leaders or desk_occupied:
                depth = len(leaders)
                target = self._usher_wait_tile(depth)
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            self._set_state(self.CHECKING_TICKET,
                            self._usher_service_route(), 0.75)

        elif self.state == self.GOING_TO_SNACK:
            self._set_state(self.SNACK_LINE)
        elif self.state == self.SNACK_LINE:
            if self.server_capacity <= 0:
                self._speech_text = "Waiting for server..."
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(SNACK_DESK_COLS),
                {self.SNACK_LINE})
            if leaders:
                waiting = sum(other.state == self.SNACK_LINE for other in leaders)
                target = self._snack_wait_tile(waiting)
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            desk_occupied = any(
                other is not self and not other.has_left
                and other.state == self.BUYING_SNACK
                and other.snack_lane == self.snack_lane
                for other in nearby_npcs or []
            )
            if desk_occupied:
                target = self._snack_wait_tile(1)
                current = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
                if current != target:
                    self._set_route([target])
                return
            self._set_state(self.BUYING_SNACK,
                            [(self._snack_col(), 11)], 1.1)
        elif self.state in (self.BUYING_TICKET, self.CHECKING_TICKET, self.BUYING_SNACK):
            if self._near_service_point():
                self._begin_service()
            else:
                self._set_route([self._service_approach_tile()])
        elif self.state == self.FINDING_SEAT:
            if self._seat_is_clear(self.seat, nearby_npcs):
                self._set_state(self.SEATED)
                self.direction = _DIR_UP
                self._frame = 0
            else:
                self.seat = None
                replacement = self._claim_available_seat(nearby_npcs)
                if replacement is not None:
                    self._set_route([replacement])
                else:
                    self._start_exit_route()
        elif self.state == self.LEAVING:
            current_tile = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
            if current_tile in ((9, 24), (10, 24)) or current_tile[1] >= 24:
                self._set_state(self.LEFT)
                self.has_left = True
            else:
                door_col = 9 if self.x < (MAP_COLS * TILE_SIZE / 2) else 10
                self._set_route([(door_col, 22), (door_col, 24)])

        elif self.state == self.ENTERING_AUDITORIUM:
            seat = self._claim_available_seat(nearby_npcs)
            if seat is not None:
                self._set_state(self.FINDING_SEAT, [seat])
            else:
                self._speech_text = "No seats left!"
                self._speech_timer = 2.5
                self._start_exit_route()

    def _refresh_queue_target(self, nearby_npcs: list["NPC"] | None):
        if self.state == self.TICKET_LINE:
            leaders = self._queue_leaders(
                nearby_npcs, len(CASHIER_DESK_COLS),
                {self.TICKET_LINE, self.BUYING_TICKET})
            target = self._ticket_follow_tile(max(0, len(leaders) - 1))
        elif self.state == self.USHER_LINE:
            if int(self.y // TILE_SIZE) >= 17 and len(self._route) > 1:
                return
            leaders = self._queue_leaders(
                nearby_npcs, len(USHER_DESK_COLS),
                {self.USHER_LINE, self.CHECKING_TICKET})
            target = self._usher_wait_tile(len(leaders))
        elif self.state == self.SNACK_LINE:

            leaders = self._queue_leaders(
                nearby_npcs, len(SNACK_DESK_COLS),
                {self.SNACK_LINE})
            target = self._snack_wait_tile(
                sum(other.state == self.SNACK_LINE for other in leaders))

        else:
            return

        current_goal = self._route[-1] if self._route else (
            int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        if target != current_goal:
            self._set_route([target])


    def _claim_available_seat(self, nearby_npcs: list["NPC"] | None) -> tuple[int, int] | None:
        claimed = {
            other.seat
            for other in nearby_npcs or []
            if other is not self
            and not other.has_left
            and other.seat is not None
        }
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
                score = abs(row - self.preferred_row) * 28
                on_preferred_side = (col < 10) == (self.preferred_side < 0)
                score += 0 if on_preferred_side else 16

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

                score += ((col * 7 + row * 11 + self.character_id * 5)
                          % 9) * self._seat_tiebreaker
                return score

            self.seat = min(available, key=seat_score)
        return self.seat

    def _seat_is_clear(self, seat: tuple[int, int] | None,
                       nearby_npcs: list["NPC"] | None) -> bool:
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
            if self.cashier_capacity <= 0:
                self.state = self.TICKET_LINE
                self._speech_text = "Waiting for cashier..."
                return
            self.has_ticket = True
            exit_col = self._ticket_exit_gap()
            self._choose_usher_lane(nearby_npcs)
            self.usher_seq = _next_queue_seq()
            self._set_state(
                self.USHER_LINE,
                [(exit_col, 18), (exit_col, 16), self._usher_wait_tile()],
            )
        elif self.state == self.CHECKING_TICKET:
            if self.usher_capacity <= 0:
                self.state = self.USHER_LINE
                self._speech_text = "Waiting for usher..."
                return
            self.ticket_checked = True
            if self.wants_food:
                self._choose_snack_lane(nearby_npcs)
                self.snack_seq = _next_queue_seq()
                self._set_state(self.GOING_TO_SNACK, [self._snack_wait_tile()])
            else:
                self._start_seat_route()
        elif self.state == self.BUYING_SNACK:
            if self.server_capacity <= 0:
                self.state = self.SNACK_LINE
                self._speech_text = "Waiting for server..."
                return
            self.has_food = True
            self._start_seat_route()


    def _start_seat_route(self):
        self._set_state(self.ENTERING_AUDITORIUM, [(10, 7)])

    def _start_exit_route(self, movie_finished: bool = False):
        if self.state in {self.LEAVING, self.LEFT}:
            return
        if movie_finished:
            self._speech_text = "Movie's over!"
            self._speech_timer = 2.5
        elif not self._speech_text:
            self._speech_text = "Heading out."
            self._speech_timer = 2.0

        door_col = 9 if self.x < (MAP_COLS * TILE_SIZE / 2) else 10
        cur_row = int(self.y // TILE_SIZE)
        if cur_row <= 7:
            waypoints = [(door_col, 7), (door_col, 15), (door_col, 22), (door_col, 24)]
        elif cur_row <= 14:
            waypoints = [(door_col, 15), (door_col, 22), (door_col, 24)]
        else:
            waypoints = [(door_col, 22), (door_col, 24)]

        self._set_state(self.LEAVING, waypoints)


    def _is_queue_state(self) -> bool:
        return self.state in {
            self.TICKET_LINE, self.BUYING_TICKET,
            self.USHER_LINE, self.CHECKING_TICKET,
            self.SNACK_LINE, self.BUYING_SNACK,
        }

    @staticmethod
    def _in_auditorium(x: float, y: float) -> bool:
        return int(y // TILE_SIZE) <= 8

    def _replan_around_npcs(self, nearby_npcs: list["NPC"] | None,
                            allow_queue_recovery: bool = False) -> bool:
        if self._detour_cooldown > 0:
            return False
        if self._is_queue_state() and not allow_queue_recovery:
            return False
        if not nearby_npcs:
            return False
        start = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        goal = (int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        if start == goal:
            return False
        occupied = {
            (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
            for other in nearby_npcs
            if other is not self and not other.has_left and other.spawn_delay <= 0
        }
        blocked = self._gate_blocked_tiles() | occupied

        if goal in occupied:
            return False

        path = _tile_path(start, goal, blocked, self._can_walk)
        if len(path) <= 1:
            return False
        remaining_route = list(self._route)
        self._route = path[1:] + remaining_route
        self._advance_route()
        self._detour_cooldown = 0.25
        return True

    def _hard_unstick(self, nearby_npcs: list["NPC"] | None) -> bool:
        if self._is_queue_state() or self.state == self.SEATED:
            return False
        cur_col = int(self.x // TILE_SIZE)
        cur_row = int(self.y // TILE_SIZE)
        goal = (int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
        occupied = set()
        if nearby_npcs:
            occupied = {
                (int(other.x // TILE_SIZE), int(other.y // TILE_SIZE))
                for other in nearby_npcs
                if other is not self and not other.has_left and other.spawn_delay <= 0
            }
        for dcol, drow in ((0, 1), (0, -1), (1, 0), (-1, 0),
                            (1, 1), (-1, 1), (1, -1), (-1, -1)):
            nc, nr = cur_col + dcol, cur_row + drow
            if (nc, nr) in occupied:
                continue
            if not self._can_walk(nc, nr):
                continue
            self.x = float(nc * TILE_SIZE + TILE_SIZE // 2)
            self.y = float(nr * TILE_SIZE + TILE_SIZE // 2)
            self._target_x, self._target_y = self.x, self.y
            self._route = []
            if goal != (nc, nr):
                blocked = self._gate_blocked_tiles() | occupied
                path = _tile_path((nc, nr), goal, blocked, self._can_walk)
                if len(path) > 1:
                    self._route = path[1:]
                    self._advance_route()
            self._stalled_for = 0.0
            self._recovery_cooldown = 1.0
            self._detour_cooldown = 0.4
            return True
        return False

    def _recover_from_stall(self, nearby_npcs: list["NPC"] | None) -> bool:
        if self._is_queue_state() or self.state == self.SEATED:
            self._stalled_for = 0.0
            return False
        if self._recovery_cooldown > 0:
            return False

        if self._stalled_for >= 6.0 and self.state not in (self.LEAVING, self.LEFT):
            self._speech_text = "Excuse me, coming through!"
            self._start_exit_route()
            self._stalled_for = 0.0
            self._recovery_cooldown = 2.0
            return True

        if self._stalled_for >= 3.0:
            if self._hard_unstick(nearby_npcs):
                return True
            self._recovery_cooldown = 0.5
            return False

        if self._stalled_for >= 1.2:
            recovered = self._replan_around_npcs(nearby_npcs, allow_queue_recovery=True)
            self._recovery_cooldown = 0.6
            return recovered

        if self._stalled_for >= 0.35:
            recovered = self._replan_around_npcs(nearby_npcs, allow_queue_recovery=False)
            self._recovery_cooldown = 0.35
            return recovered

        return False

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
            if self.state == self.LEAVING:
                self._ticket_lane_locked = True
                return
            cur_col = int(self.x // TILE_SIZE)
            cur_row = int(self.y // TILE_SIZE)
            if cur_row >= 23:
                self._set_route([(cur_col, 22), self._ticket_wait_tile()])
            else:
                self._set_route([self._ticket_wait_tile()])
            self._ticket_lane_locked = True
        if self.state == self.LEAVING:
            cur_col = int(self.x // TILE_SIZE)
            cur_row = int(self.y // TILE_SIZE)
            if (cur_col in (9, 10) and cur_row >= 24) or self.y >= 24.0 * TILE_SIZE:
                self._set_state(self.LEFT)
                self.has_left = True
                return
            if self.seat is not None and (cur_col, cur_row) != self.seat:
                self.seat = None

        self._anim_t += dt
        self._detour_cooldown = max(0.0, self._detour_cooldown - dt)
        self._recovery_cooldown = max(0.0, self._recovery_cooldown - dt)
        self._vendor_timer = max(0.0, self._vendor_timer - dt)
        self._collision_debug_target = None

        if movie_finished and self.state not in {self.LEAVING, self.LEFT}:
            self._start_exit_route(movie_finished=True)
            return

        if self.state in (self.TICKET_LINE, self.USHER_LINE, self.SNACK_LINE):
            self._time_waiting += dt
            if self._time_waiting >= self._wait_patience:
                is_closed = (
                    (self.state == self.TICKET_LINE and self.cashier_capacity <= 0) or
                    (self.state == self.USHER_LINE and self.usher_capacity <= 0) or
                    (self.state == self.SNACK_LINE and self.server_capacity <= 0)
                )
                if is_closed:
                    self._speech_text = random.choice([
                        "Counters are closed, I'm leaving.",
                        "No staff on duty, heading home.",
                        "Waited too long, nothing is open.",
                    ])
                    self._speech_timer = 2.5
                    self._start_exit_route()
                    return
                else:
                    if not self._patience_extended and random.random() < 0.50:
                        self._patience_extended = True
                        self._time_waiting = 0.0
                        self._wait_patience = 180.0
                        self._speech_text = random.choice([
                            "Line is packed, but I'll wait 3 more mins...",
                            "Super crowded... I'll give it 3 more mins.",
                            "Huge line! Sticking around for 3 mins.",
                        ])
                        self._speech_timer = 3.0
                    else:
                        self._speech_text = random.choice([
                            "Line is way too congested, I'm leaving.",
                            "Can't wait any longer, heading out.",
                            "Too packed today, I'll catch another show.",
                        ])
                        self._speech_timer = 2.5
                        if self.state == self.SNACK_LINE and self.ticket_checked:
                            self._start_seat_route()
                        else:
                            self._start_exit_route()
                        return

        if self.state == self.SEATED:
            self._watch_time += dt
            self.direction = _DIR_UP
            self._frame = 0
            if self._watch_time >= self._boredom_limit:
                self._start_exit_route()
                return
            return


        if self._service_timer > 0:
            self._service_timer -= dt
            self._frame = 0
            if self._service_timer <= 0:
                self._finish_service(nearby_npcs)
            return


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
                self._orient_for_queue()
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
        blocked_other: "NPC | None" = None
        if nearby_npcs:
            for other in nearby_npcs:
                if other is self or other.has_left or other.spawn_delay > 0:
                    continue
                if abs(next_x - other.x) > 20 or abs(next_y - other.y) > 20:
                    continue
                if (self._in_auditorium(self.x, self.y)
                        or self._in_auditorium(other.x, other.y)):
                    continue
                if self.y >= 22.0 * TILE_SIZE or other.y >= 22.0 * TILE_SIZE:
                    continue
                if self.state == self.LEAVING or other.state == self.LEAVING:
                    continue
                if math.hypot(next_x - other.x, next_y - other.y) < _NPC_COLLISION_RADIUS * 2:

                    self_priority = (self.queue_slot, self.character_id)
                    other_priority = (other.queue_slot, other.character_id)
                    if self_priority > other_priority:
                        blocked_by_npc = True
                        blocked_other = other
                        self._collision_debug_target = (other.x, other.y)
                        break

        if blocked_by_npc:
            if self._is_queue_state() and dist < TILE_SIZE * 0.75:
                target_occupied = any(
                    other is not self and not other.has_left and other.spawn_delay <= 0
                    and abs(other.x - self._target_x) < 14 and abs(other.y - self._target_y) < 14
                    for other in nearby_npcs or []
                )
                if not target_occupied:
                    self.x, self.y = self._target_x, self._target_y
                    self._stalled_for = 0.0
                    if not self._route:
                        self._orient_for_queue()
                        self._arrive_at_step(nearby_npcs)
                    self._frame = 0
                    if self._is_queue_state():
                        self._orient_for_queue()
                    return

            if self._detour_cooldown <= 0 and blocked_other is not None:
                goal = (int(self._target_x // TILE_SIZE), int(self._target_y // TILE_SIZE))
                other_tile = (int(blocked_other.x // TILE_SIZE),
                              int(blocked_other.y // TILE_SIZE))
                if goal != other_tile:
                    if self._replan_around_npcs(nearby_npcs):
                        self._stalled_for = 0.0
                        self._frame = 0
                        return

            self._stalled_for += dt
            if self._recover_from_stall(nearby_npcs):
                self._stalled_for = 0.0
            self._frame = 0
            if self._is_queue_state():
                self._orient_for_queue()
            return

        if self._can_walk(int(next_x // TILE_SIZE), int(next_y // TILE_SIZE)):
            self.x, self.y = next_x, next_y
            self._stalled_for = 0.0
            self._frame = int(self._anim_t / 0.2) % _ANIM_FRAMES
        else:
            self._stalled_for += dt
            self._recover_from_stall(nearby_npcs)
            self._frame = 0


    def draw(self, surface: pygame.Surface, camera):
        if self.spawn_delay > 0:
            return
        sx, sy = camera.world_to_screen(self.x, self.y)

        sw, sh = _NPC_DRAW_W, _NPC_DRAW_H
        if sx < -sw or sx > surface.get_width() + sw or sy < -sh or sy > surface.get_height() + sh:
            return

        dir_to_use = _DIR_UP if self.state == self.SEATED else self.direction
        frame_to_use = 0 if self.state == self.SEATED else self._frame
        sprite = _get_npc_frame(self.character_id, dir_to_use, frame_to_use)
        sw, sh = sprite.get_size()

        if self.state != self.SEATED:
            surface.blit(_get_shadow_surf(), (int(sx) - sw // 2 + 4, int(sy) - 2))

        if self.state == self.SEATED:
            head_h = 22
            head_surf = sprite.subsurface(pygame.Rect(0, 0, sw, head_h))
            surface.blit(head_surf, (int(sx) - sw // 2, int(sy) - 34))
        else:
            surface.blit(sprite, (int(sx) - sw // 2, int(sy) - sh + 4))


        if DEBUG_NPC_COLLISION_RANGE:
            pygame.draw.circle(surface, (70, 210, 255), (int(sx), int(sy)),
                               _NPC_COLLISION_RADIUS, 1)
            if self._collision_debug_target:
                tx, ty = camera.world_to_screen(*self._collision_debug_target)
                pygame.draw.line(surface, (255, 70, 70), (int(sx), int(sy)),
                                 (int(tx), int(ty)), 2)

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
            pygame.draw.polygon(bubble, (255, 255, 255, 220),
                                [(bw // 2 - 3, bh), (bw // 2 + 3, bh), (bw // 2, bh + 4)])
            bubble.blit(text_surf, (5, 4))
            bubble.set_alpha(alpha)

            bx = int(sx) - bw // 2
            by = int(sy) - sh - bh - 6
            surface.blit(bubble, (bx, by))

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
            surface.blit(bubble, (int(vx) - bw // 2, int(vy) - bh - 40))


def build_npcs(count: int = 5, slot_offset: int = 0) -> list[NPC]:
    npcs = []
    character_ids = _sprite_rng.sample(
        range(_CHARACTERS_PER_SHEET * len(_NPC_SHEETS)),
        min(count, _CHARACTERS_PER_SHEET * len(_NPC_SHEETS)),
    )

    spawn_spots = [
        (9, 24), (10, 24),
    ]
    for i, character_id in enumerate(character_ids):
        col, row = spawn_spots[(slot_offset + i) % len(spawn_spots)]
        name = _NPC_NAMES[character_id % len(_NPC_NAMES)]
        npc = NPC(
            character_id, col, row, name,
            queue_slot=slot_offset + i,
            spawn_delay=(i * random.uniform(0.35, 0.8)),
        )
        npcs.append(npc)


    return npcs
