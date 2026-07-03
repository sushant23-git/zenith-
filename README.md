# 🌺 Hand-Tracking Flower Bloomer 🌺

A premium, interactive Python application using **OpenCV** and **MediaPipe Hands** that generates a procedural, blooming flower on the screen, controlled dynamically by your hand's pinch distance.

## Features

- **Procedural Flower Drawing**:
  - Multi-layered, vibrant petals (pink outer layers, peach inner layers) rotating over time.
  - A golden central pistil and growing pollen-topped stamens.
  - Dynamic forest green Bezier stem that curves and sways to follow your hand's movements.
  - Growing green leaves aligned with the stem curvature.
- **Dynamic Pinch Detection**:
  - Distance measured between the **thumb tip** and **index finger tip**.
  - Normalization by wrist-to-knuckle distance to make the calibration invariant to hand distance from the camera.
  - Auto-calibrating range which adapts to the user's specific hand size and open/pinch range.
- **Particle System**:
  - Magical glowing sparkles (gold, pink, and cyan) float upwards and fade out when the flower is fully bloomed ($>75\%$).
- **Organic State Transitions**:
  - If tracking is lost, the flower does not instantly vanish. It slowly fades out, closes its petals, and gently drifts down.
- **Glassmorphic HUD Dashboard**:
  - A modern screen overlay displaying tracking state, dynamic bloom percentage indicator, and real-time FPS.

---

## Installation & Setup

Ensure you have Python installed (Python 3.8+ recommended).

1. Clone or download this repository.
2. Open a terminal in this directory.
3. Install the dependencies using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Launch the application using:
```bash
python main.py
```

### Controls & Interaction

- **Positioning**: Move your hand in front of your webcam. The flower center will snap to the midpoint of your thumb and index tips. The stem automatically roots itself to the bottom of the screen.
- **Bloom**:
  - **Pinch**: Touch your thumb tip and index finger tip together. The flower will shrink and close into a bud.
  - **Spread**: Open your fingers wide. The flower will grow, bloom, and begin emitting magical sparkles.
- **Exit**: Click on the camera window and press the **`ESC`** key to close.

---

## Code Architecture

- [main.py](file:///C:/Users/sushant%20gajbhiye/Documents/antigravity/bold-nobel/main.py): Sets up OpenCV webcam capture, handles the MediaPipe hand tracking pipeline, processes coordinate systems, applies smoothing (EMA), manages state machine transitions, and renders the dashboard HUD.
- [flower.py](file:///C:/Users/sushant%20gajbhiye/Documents/antigravity/bold-nobel/flower.py): Encapsulates all drawing logic including the Bezier curve calculation, leaves, petals, stamens, and particle system.
- [requirements.txt](file:///C:/Users/sushant%20gajbhiye/Documents/antigravity/bold-nobel/requirements.txt): Declares required packages.
