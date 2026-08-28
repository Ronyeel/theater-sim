# CinePlex Dreams — Movie Theater Queuing & Resource Simulation

> **Academic Project & Laboratory Simulation**  
> An integrated discrete-event simulation and interactive 2D graphical visualization modeling customer queuing dynamics, resource allocation, and bottleneck optimization in a multi-stage theater environment.

---

## 1. Executive Summary & Abstract

**CinePlex Dreams** is a computational modeling platform designed to study and optimize service-point staffing within high-throughput entertainment venues. The system models a tandem queuing network where arriving moviegoers progress through three sequential service stages:
1. **Box Office Ticketing** (Cashiers)
2. **Auditorium Access Control** (Ushers)
3. **Concession Stand** (Servers, with Bernoulli trial branching probability)

The simulation engine is built upon **SimPy** (pure Python discrete-event simulation) running concurrently alongside a **Pygame** real-time graphical visualization engine. The primary management objective is to evaluate staffing configurations $(c_{cashier}, c_{usher}, c_{server})$ to minimize customer wait times below a strict **10-minute service level agreement (SLA)** without incurring excess labor expenditure.

---

## 2. Queuing Theory & Mathematical Model

The theater operates as a **tandem multi-server queuing network** ($G/G/c$ queues in series):

```
Arriving Customers (Poisson Stream / Periodic Interval)
        │
        ▼
┌──────────────────┐
│  Cashier Queue   │ ──► [ Cashier Resources (1..4) ] ── (Service Time: 1 to 3 min)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│   Usher Queue    │ ──► [ Usher Resources (1..2) ]   ── (Service Time: 3 sec = 0.05 min)
└──────────────────┘
        │
        ├────────────────────────┐ (1 - p_food)
        ▼ (p_food)               │
┌──────────────────┐             │
│ Concession Queue │             │
└──────────────────┘             │
        │                        │
        ▼                        │
[ Server Resources (1..3) ]      │
(Service Time: 1 to 5 min)       │
        │                        │
        └──────────┬─────────────┘
                   ▼
       [ Auditorium Seating ]
```

### 2.1 Service Distributions
* **Customer Arrival**: 3 initial guests at $t = 0$; subsequent arrivals occur every $\Delta t_{arrival}$ (default: $0.20\text{ min} = 12\text{ seconds}$).
* **Ticketing Service Time**: Discrete uniform distribution $T_{ticket} \sim U(1, 3)\text{ minutes}$.
* **Usher Check Time**: Deterministic $T_{usher} = \frac{3}{60} = 0.05\text{ minutes}$ ($3\text{ seconds}$).
* **Concession Service Time**: Discrete uniform distribution $T_{food} \sim U(1, 5)\text{ minutes}$ with probability $p_{food} \in [0, 1]$.

### 2.2 Performance Metrics
* **Total Journey Duration**: $W_i = t_{\text{seated}, i} - t_{\text{arrival}, i}$
* **Sample Mean Wait Time**: $\bar{W} = \frac{1}{N} \sum_{i=1}^{N} W_i$
* **SLA Compliance Rate**: $P(W \le 10) = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}(W_i \le 10)$
* **Little's Law Validation**: $L = \lambda W$, relating average in-system population ($L$) to arrival rate ($\lambda$) and mean wait time ($W$).

---

## 3. System Architecture & Design Patterns

The codebase is organized into decoupled layers following clean software engineering practices:

```
┌─────────────────────────────────────────────────────────────┐
│                       Entry Points                          │
│               main.py  /  game/__main__.py                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│  Presentation Layer (GUI)   │ │  Simulation Backend (SimPy) │
│       [game/ package]       │ │       [src/ package]        │
│                             │ │                             │
│ • Screen State Machine      │ │ • MovieTheater (Resources)  │
│ • A* Pathfinding NPCs       │ │ • Journey Generators        │
│ • Live HUD & Dialogs        │ │ • Statistical Analysis      │
│ • 2D Tilemap & Camera       │ │                             │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
               ┌───────────────────────────────┐
               │    TheaterSimulationBridge    │
               │    [game/backend_bridge.py]   │
               │ Synchronizes frame dt with    │
               │ SimPy environment execution   │
               └───────────────────────────────┘
```

### 3.1 Design Patterns Implemented
1. **Bridge Pattern (`TheaterSimulationBridge`)**: Decouples the mathematical SimPy discrete-event scheduler from the Pygame real-time rendering loop.
2. **State Pattern (`App` & `Stage`)**: Manages screen state transitions (`MainMenu` $\rightarrow$ `SetupScreen` $\rightarrow$ `ExteriorScreen` $\rightarrow$ `GameScreen` $\rightarrow$ `ResultsScreen`) and individual player/NPC customer stages.
3. **Component Pattern (`game/ui/`)**: Encapsulates reusable UI elements (`Button`, `Slider`, `HUD`, `DialogMenu`, `SimulationPanel`, `SpeechBubble`).
4. **A* Grid Search Pathfinding (`game/entities/npc.py`)**: Computes optimal 4-directional obstacle-avoiding paths through the theater tilemap for autonomous NPC agents.

---

## 4. Directory & File Structure

```
theater-sim/
├── src/                          # Pure Discrete-Event Simulation Engine (SimPy)
│   ├── __init__.py               # Top-level backend exports
│   ├── theater.py                # SimPy resource pools and transaction delays
│   ├── simulation.py             # Customer journey processes and arrival generator
│   └── stats.py                  # Statistical metrics, mean wait, and formatting
├── game/                         # Interactive Pygame Engine & Visual Assets
│   ├── __init__.py               # Game package metadata
│   ├── __main__.py               # Application controller & state machine
│   ├── settings.py               # Global constants, colors, grid sizes, presets
│   ├── backend_bridge.py         # Pygame-SimPy time synchronization bridge
│   ├── assets/                   # Pixel art sprites, tiles, and backgrounds
│   │   ├── backgrounds/          # Exterior cinema and marquee backgrounds
│   │   ├── sprites/              # NPC and player animation sheets
│   │   ├── tiles/                # Cinema tileset assets
│   │   └── ui/                   # UI graphic elements
│   ├── core/                     # Graphics & Engine Subsystems
│   │   ├── __init__.py           # Subsystem exports
│   │   ├── asset_loader.py       # Sprite slicer and fallback generators
│   │   ├── camera.py             # 2D smooth lerp camera with zoom clamping
│   │   ├── particles.py          # Lightweight particle effects system
│   │   └── tilemap.py            # 20×25 cinema interior tilemap definition
│   ├── entities/                 # Game World Actors
│   │   ├── __init__.py           # Entity exports
│   │   ├── player.py             # Controllable player character controller
│   │   ├── npc.py                # Autonomous moviegoer agents with A* routing
│   │   └── staff.py              # Visual staff positioning and animations
│   ├── screens/                  # Application Screens
│   │   ├── __init__.py           # Screen exports
│   │   ├── main_menu.py          # Title screen with animated starfield
│   │   ├── setup_screen.py       # Interactive parameter sliders & scenario picker
│   │   ├── exterior_screen.py    # Cinema forecourt walk-in scene
│   │   ├── game_screen.py        # Main playable simulation theater world
│   │   └── results_screen.py     # Evaluation scorecard with grade & recommendations
│   ├── ui/                       # User Interface Widgets
│   │   ├── __init__.py           # UI exports
│   │   ├── button.py             # Button and Slider interactive widgets
│   │   ├── dialog_menu.py        # Interactive modal popups (ticket, food, usher)
│   │   ├── hud.py                # Pixel-styled live telemetry HUD dashboard
│   │   ├── simulation_panel.py   # [F1] In-game parameter and preset modifier
│   │   └── speech_bubble.py      # Pop-in dialogue bubbles and interact prompts
│   └── world/                    # Spatial Systems
│       ├── __init__.py           # World exports
│       └── interactions.py       # Interactive trigger volumes and spatial queries
├── tests/                        # Automated Unit Test Suite
│   ├── __init__.py               # Test package
│   ├── test_simulation.py        # SimPy process validation & deterministic runs
│   ├── test_theater.py           # Resource constraints and delay verification
│   ├── test_stats.py             # Metric calculations and time formatting
│   ├── test_bridge.py            # Bridge synchronization and speed scaling
│   └── test_interactions.py      # Trigger zone proximity and map boundaries
├── main.py                       # Unified Dual-Mode CLI/GUI Application Launcher
├── requirements.txt              # Pinned project dependencies
└── README.md                     # Academic documentation & manual
```

---

## 5. Installation & Setup

### 5.1 Prerequisites
* **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.14)
* **pip** package manager

### 5.2 Environment Setup
```bash
# 1. Clone or navigate to the project directory
cd theater-sim

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

---

## 6. How to Run

### 6.1 Graphical User Interface (GUI Mode)
Launch the full interactive 2D simulation experience:
```bash
python main.py
# or explicitly:
python main.py --gui
# or via module:
python -m game
```

### 6.2 Command-Line Interface (CLI Mode)
Run discrete-event simulations directly in the terminal for batch testing and analysis:
```bash
# Basic run with defaults (1 cashier, 1 usher, 1 server, 90 minutes)
python main.py --cli

# Optimized staffing scenario (3 cashiers, 2 ushers, 2 servers for 120 minutes)
python main.py --cli --cashiers 3 --ushers 2 --servers 2 --runtime 120

# Interactive terminal prompt
python main.py --cli --interactive
```

#### CLI Command-Line Arguments:
| Flag | Description | Default |
| :--- | :--- | :--- |
| `--cli` | Enable Command-Line Interface simulation mode | `False` |
| `--gui` | Enable Graphical User Interface mode | `True` |
| `-c`, `--cashiers` | Number of box-office cashiers | `1` |
| `-u`, `--ushers` | Number of ticket-checking ushers | `1` |
| `-s`, `--servers` | Number of concession stand servers | `1` |
| `-r`, `--runtime` | Total simulation runtime in minutes | `90.0` |
| `-a`, `--arrival-interval` | Interval between guest arrivals (minutes) | `0.20` |
| `-f`, `--food-prob` | Probability a guest visits concessions | `0.50` |
| `--seed` | Random number generator seed | `42` |
| `-i`, `--interactive` | Prompt interactively in console for staffing counts | `False` |

---

## 7. Interactive Controls & Features

### 7.1 In-Game Keybindings
| Key | Action |
| :--- | :--- |
| **W, A, S, D** / **Arrow Keys** | Move player character |
| **E** / **Space** / **Enter** | Interact with nearest service zone / select menu option |
| **F1** | Open in-game Simulation Configuration Panel |
| **1** | Toggle collision geometry debug overlay |
| **+** / **-** or **Mouse Wheel** | Adjust camera zoom level ($0.55\times$ to $1.35\times$) |
| **ESC** | Return to Main Menu / Cancel dialog |

### 7.2 Pre-Configured Scenarios
The in-game configuration panel (`[F1]`) and setup screen provide preset theater scenarios:
1. **🌙 Normal Night**: Standard operational flow ($12\text{s}$ arrival gap, $50\%$ food demand, $90\text{ min}$).
2. **🔥 Friday Night**: Elevated rush ($7.8\text{s}$ arrival gap, $55\%$ food demand, $90\text{ min}$).
3. **⭐ Blockbuster Premiere**: Extreme peak demand ($4.8\text{s}$ arrival gap, $60\%$ food demand, $120\text{ min}$).
4. **👨‍👩‍👧 Family Night**: High concession volume ($10.8\text{s}$ arrival gap, $80\%$ food demand, $90\text{ min}$).
5. **🌃 Late Show**: Low-density off-peak show ($15\text{s}$ arrival gap, $40\%$ food demand, $60\text{ min}$).

---

## 8. Verification & Automated Test Suite

The project includes an automated unit test suite built with Python's standard `unittest` framework.

### 8.1 Running All Unit Tests
Execute the full test suite from the repository root:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 8.2 Test Coverage Summary
* **`tests/test_simulation.py`**: Validates SimPy environment process execution, deterministic reproducibility with random seeds, input validation exceptions, and arrival callback tracking.
* **`tests/test_theater.py`**: Verifies `MovieTheater` resource capacity boundaries, zero-capacity availability flags, and service transaction delay ranges.
* **`tests/test_stats.py`**: Tests mean wait calculations, empty-dataset edge cases, and fractional time conversion algorithms.
* **`tests/test_bridge.py`**: Tests `TheaterSimulationBridge` state resets, pause/resume mechanisms, speed multipliers, and runtime limits.
* **`tests/test_interactions.py`**: Tests spatial trigger proximity queries, zone generation counts, and tilemap collision boundaries.
