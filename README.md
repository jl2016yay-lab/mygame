Falling Chickens
=================

A simple Pygame dodging game. Move left/right to avoid falling chickens. Survive to increase your score. Press R to restart after a collision.

Requirements
------------

- Python 3.9+
- Windows, macOS, or Linux

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run
---

```powershell
python game.py
```

Controls
--------

- **Start Screen**: Space or Enter - Start the game
- **In Game**: Left/Right arrows (or A/D) - Move, Space - Jump, J - Clear all chickens & coins, K - Exchange 10 coins for 1 J key
- **Game Over**: R - Restart, Enter - Save high score
- Close window: Quit

Notes
-----

- Chickens can use a sprite if you add an image at `assets/chicken.png`.
  - Recommended square image ~64x64 with transparent background (Minecraft-like look works great).
  - The game scales it to fit. If no image is present, white rectangles are used.
- Player can use a sprite too: add `assets/player.png` (e.g., 64x64). If missing, a blue rectangle is drawn.

Sound
-----

- **Background Music**: Add background music at `assets/background.wav` (any length WAV/MP3/OGG file). Music loops continuously during gameplay.
- **Collision Sound**: Add a collision sound at `assets/hit.wav` (short WAV, < 1s recommended). If missing or audio is unavailable, the game continues silently.

High Scores
-----------

- On Game Over, enter your name and press Enter to save your score.
- Scores are stored in `highscores.json` next to `game.py` and persist across runs.

Special Events
--------------

- **TNT**: Appears every 20s, slides across the bottom. Touch it to lose 1 heart.
- **Angel**: Appears every 30s in the center. Touch it to heal back to 3 hearts.
- Window size: 600 x 800; background: light green.

