# Blue Max — Pygame Recreation

A faithful recreation of the 1983 Commodore 64 classic by Synapse Software, built in Python/Pygame.

## Screenshot / Gameplay

Diagonal isometric view. Fly a WWI Sopwith Camel over enemy territory, strafe tank columns, bomb bridges and ships, and survive long enough to land at a friendly airstrip.

## Requirements

- Python 3.11+
- Pygame 2.5+

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move left/right · Climb/Dive |
| SPACE | Machine gun |
| LCTRL / Z / X | Drop bomb |
| ESC | Quit to menu |

## Game Mechanics

### Altitude (0–3)
- **0** — Ground (crash!)
- **1** — Low / strafing altitude (brown HUD bar; can strafe tanks with gun)
- **2** — Normal bombing altitude
- **3** — High altitude (safer from flak, harder to aim bombs)

### Bombing
Your plane's **shadow** shows the bomb's landing spot. Time your drops to hit bridges and ships as you fly over them. Bombing causes a slight altitude loss — climb before releasing for best results.

### Damage System
Each enemy hit causes one of four impairments:
- **GUNS** — reduced fire rate
- **BMBS** — bomb gear damaged
- **FUEL** — increased fuel leak
- **MNVR** — reduced maneuverability

Five hits destroy the plane.

### Landing
When you near the end of the sector a **LAND NOW** message flashes. Descend to altitude 0 over the sandy airstrip to land. A successful landing refuels, repairs, and restocks bombs.

### Scoring & Ranks

| Points | Rank |
|--------|------|
| 0 | Private |
| 500 | Corporal |
| 1 500 | Sergeant |
| 3 000 | Lieutenant |
| 6 000 | Captain |
| 10 000 | Major |
| 16 000 | Colonel |
| 25 000 | General |

### Difficulty

| Level | Enemy fire | Flak | Spawns |
|-------|-----------|------|--------|
| Easy | 50 % | 30 % | 40 % |
| Normal | 100 % | 60 % | 70 % |
| Hard | 180 % | 100 % | 100 % |

## Project Structure

```
main.py        — game loop, state machine (Menu / Flying / Landing / GameOver)
constants.py   — all tunable constants and C64 colour palette
world.py       — procedural river-sector map, Target entities
camera.py      — isometric projection (world ↔ screen)
player.py      — player plane: input, physics, damage
entities.py    — Bullet, Bomb, EnemyPlane with basic AI
renderer.py    — all pygame drawing (terrain, sprites, explosions)
hud.py         — HUD bar: score, rank, altitude, fuel, damage
```

## Roadmap (post-MVP)

- [ ] Sprite sheets / pixel art assets
- [ ] Sound effects and C64-style music
- [ ] Multiple sectors (towns, forests, open fields)
- [ ] Formation enemies with wingman AI
- [ ] High-score table with persistence
- [ ] Joystick / gamepad support
