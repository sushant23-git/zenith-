# 🌸 Hand-Tracked Generative Flowers

A real-time web-based generative art experience that lets you grow glowing, hand-controlled flowers by making a pinch gesture with your fingers. Built entirely in the browser using MediaPipe hand tracking, Three.js WebGL rendering, and modern web APIs.

## Features

✨ **Real-Time Hand Tracking**
- MediaPipe HandLandmarker detects both hands independently
- Smooth landmark tracking with exponential smoothing for jitter reduction
- Normalized pinch distance calculation for consistent gesture control

🌼 **Dynamic Flower Generation**
- Flowers bloom from your fingertips based on pinch gesture
- Petal count, color gradients, and stem length all configurable
- Smooth growth/bloom animations with spring easing
- Graceful wilting when hands leave frame or pinch closes

🎨 **Glowing Particle Rendering**
- GPU-accelerated particle system with Three.js and WebGL
- Additive blending for realistic light mixing
- Unreal Bloom post-processing for bloom glow effect
- Warm orange-to-white petal color gradient

🎮 **Interactive Controls**
- Real-time settings adjustments
- Debug overlay showing hand landmarks and parameters
- Collapsible settings panel
- Keyboard shortcut (D) to toggle debug mode

📱 **Responsive Design**
- 720x1280 portrait canvas (9:16 aspect ratio)
- Mobile-friendly UI with touch support
- Adapts to browser window size

## Quick Start

1. **Clone or open in browser:**
   ```bash
   git clone https://github.com/sushant23-git/zenith-.git
   cd zenith-
   open index.html
   ```

2. **Grant camera permission** when prompted

3. **Move your hands** toward the camera and make a pinch gesture (thumb and index finger together) to grow flowers

4. **Adjust settings** using the controls panel in the bottom-right corner

5. **Toggle debug mode** by pressing 'D' to see hand landmarks and live values

## How It Works

### Hand Tracking
- MediaPipe detects 21 landmarks per hand
- Key measurements: thumb tip to index tip distance (pinch), normalized by hand size
- Landmarks smoothed frame-to-frame to reduce jitter

### Flower Animation
- **Grow parameter**: Increases as pinch opens (fingers spread apart)
- **Bloom parameter**: Increases as petals unfurl (inverse of pinch tightness)
- Particles generated in a circular petal fan from a central stem
- Organic wobble added via Perlin-like noise for natural movement

### Rendering
- Particle geometry rendered with Three.js PointsMaterial
- Additive blending creates realistic light mixing
- UnrealBloomPass post-processing adds glow halo effect
- Video feed rendered as background layer beneath particles

## Architecture

```
index.html          - Main HTML structure & UI
js/
  camera.js         - getUserMedia & video element management
  handTracking.js   - MediaPipe HandLandmarker setup & landmark smoothing
  flower.js         - Flower particle system & animation state
  scene.js          - Three.js scene, rendering, & post-processing
  main.js           - App initialization & game loop
```

## Settings

| Setting | Range | Description |
|---------|-------|-------------|
| Pinch Sensitivity | 0.5–2.0 | How responsive the grow/bloom is to hand position |
| Bloom Speed | 0.1–1.0 | Animation speed for petal unfurling |
| Stem Length | 40–200 px | Maximum height of flower stem |
| Glow Strength | 0.5–3.0 | Intensity of bloom post-processing effect |
| Petal Count | 3–12 | Number of petals per flower |

## Browser Support

- Chrome/Edge 90+ (WebGL2, getUserMedia)
- Firefox 88+ (WebGL2, getUserMedia)
- Safari 15+ (WebGL2, getUserMedia)
- Mobile browsers with camera support

## Performance

- Target: 30–60 FPS on modern laptops
- Optimized for 2-hand tracking with 100+ particles per flower
- GPU-accelerated rendering with Three.js

## Controls

| Key | Action |
|-----|--------|
| D | Toggle debug overlay |
| Sliders | Adjust settings in real time |
| Click ⚙ Settings | Expand/collapse settings panel |

## API Dependencies

- **Three.js** - WebGL 3D rendering
- **MediaPipe** - Hand landmark detection
- **EffectComposer** - Post-processing pipeline
- **UnrealBloomPass** - Bloom glow effect

All loaded via CDN for zero build setup.

## Future Enhancements

- [ ] Multi-hand collision detection (flowers merge/interact)
- [ ] Custom petal shapes (roses, daisies, etc.)
- [ ] Sound reactivity (audio visualizer mode)
- [ ] Animation recording/export as video
- [ ] Physics simulation (gravity, wind, particle trails)
- [ ] Mobile gesture calibration
- [ ] WebXR for AR mode on compatible devices

## License

MIT - Feel free to use, modify, and distribute.

---

**Grow something beautiful with your hands.** 🌸✨
