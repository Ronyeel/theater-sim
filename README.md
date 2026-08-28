# RR-EL — Theater Management Simulation

**Camarines Norte State College**  
**College of Computing and Multimedia Studies (CCMS)**  

A Python discrete-event simulation modeling movie theater queuing operations, staffing resource allocation, and auditorium seating logistics with a 2D graphical visualization.

---

## Features

- **Discrete-Event Simulation (SimPy):** Simulates customer arrivals, cashier ticketing (1–3 min), usher ticket verification (3s), and concession purchases (1–5 min, 50% probability).
- **2D Graphical Simulation (Pygame):** Real-time pixel-art visualization of customer lines, staff counters, walking pathfinding, and auditorium seating.
- **Operations Summary Report:** Performance analytics dashboard featuring wait time distribution histograms, efficiency metrics, and timeline progression curves.
- **Live In-Game Controls:** Real-time speed adjustments (1x, 2x, 5x, 10x), pause/resume, camera pan/zoom, and live staffing configuration (`[F1]`).

---

## Installation & Setup

1. **Clone or download the repository:**
   ```bash
   git clone https://github.com/your-username/theater-sim.git
   cd theater-sim
   ```

2. **Set up a Python virtual environment (recommended):**
   ```bash
   python -m venv .venv
   ```
   - **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
   - **Windows Command Prompt:** `.venv\Scripts\activate.bat`
   - **macOS / Linux:** `source .venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run

### Graphical Simulation (Interactive GUI)
```bash
python main.py
```

**Controls:**
- `Click & Drag` / `WASD` / `Arrow Keys`: Pan camera around the theater
- `Mouse Wheel` / `+` / `-`: Zoom in / Zoom out
- `Spacebar`: Pause / Resume simulation
- `F`: Toggle fast-forward speeds (1x, 2x, 5x, 10x)
- `F1`: Open Simulation Parameters & Staffing configuration
- `R` / `Tab`: Reset simulation
- `Esc`: Return to title screen / Exit

---

## Project Structure

```
theater-sim/
├── main.py                  # Primary application launcher (Pygame GUI)
├── requirements.txt         # Project dependencies (pygame-ce, simpy)
├── README.md                # Project documentation
├── src/                     # Core backend simulation logic
│   ├── theater.py           # Theater resources (Cashiers, Ushers, Servers)
│   ├── simulation.py        # SimPy customer journey & arrival process
│   ├── stats.py             # Wait time calculations and formatting
│   └── seating.py           # 2D list seating chart data structures
└── game/                    # Pygame 2D graphical frontend
    ├── settings.py          # Configuration constants and color palettes
    ├── backend_bridge.py    # Bridge between SimPy events and Pygame frames
    ├── core/                # Tilemap, camera, particle engine, lighting system, assets
    ├── entities/            # NPC moviegoers and staff sprites
    ├── screens/             # Main menu, setup, game spectator, results report
    ├── ui/                  # HUD bar, simulation settings panel, modal dialogs, buttons
    └── world/               # Spatial zones and layout interactions
```