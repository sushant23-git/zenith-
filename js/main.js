/**
 * main.js - Application entry point and main loop
 */

const App = (() => {
    let isRunning = false;
    let lastFrameTime = 0;
    let debugMode = false;

    // Settings with defaults
    const settings = {
        pinchSensitivity: 1.0,
        bloomSpeed: 0.3,
        stemLength: 100,
        glowStrength: 1.5,
        petalCount: 7
    };

    const init = async () => {
        try {
            // Initialize camera
            console.log('Initializing camera...');
            await CameraModule.init();

            // Initialize hand tracking
            console.log('Initializing hand tracking...');
            await HandTrackingModule.init();

            // Initialize flower system
            FlowerModule.initFlowers();

            // Initialize Three.js scene
            console.log('Initializing Three.js scene...');
            SceneModule.init(document.getElementById('canvas-container'));

            // Setup UI
            setupUI();

            // Update status
            CameraModule.updateStatus('✅ Ready! Move your hands to grow flowers.', false);

            isRunning = true;
            lastFrameTime = performance.now();
            gameLoop();
        } catch (err) {
            console.error('Initialization error:', err);
            CameraModule.updateStatus(`❌ Error: ${err.message}`, true);
        }
    };

    const gameLoop = () => {
        if (!isRunning) return;

        const now = performance.now();
        const deltaTime = (now - lastFrameTime) / 1000;
        lastFrameTime = now;

        try {
            // Detect hands
            const video = CameraModule.getVideoElement();
            const handsData = HandTrackingModule.detectHands(video);

            // Update flowers
            FlowerModule.updateFlowers(handsData, settings, deltaTime);

            // Render Three.js scene
            SceneModule.render(handsData, settings);

            // Update HUD if debug mode
            if (debugMode) {
                updateDebugHUD(handsData);
            }
        } catch (err) {
            console.error('Game loop error:', err);
        }

        requestAnimationFrame(gameLoop);
    };

    const setupUI = () => {
        // Debug toggle
        const debugToggle = document.getElementById('debug-toggle');
        debugToggle.addEventListener('click', () => {
            debugMode = !debugMode;
            debugToggle.classList.toggle('active', debugMode);
            debugToggle.textContent = debugMode ? 'DEBUG ON' : 'DEBUG OFF';
            document.getElementById('debug-overlay').style.display = debugMode ? 'block' : 'none';
        });

        // Keyboard shortcut for debug (D key)
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 'd') {
                debugToggle.click();
            }
        });

        // Settings panel
        const settingsPanel = document.getElementById('settings-panel');
        const collapseToggle = document.getElementById('collapse-toggle');

        collapseToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsPanel.classList.toggle('collapsed');
            collapseToggle.textContent = settingsPanel.classList.contains('collapsed') ? '+' : '−';
        });

        // Control sliders
        const controls = [
            { id: 'pinch-sensitivity', key: 'pinchSensitivity', min: 0.5, max: 2 },
            { id: 'bloom-speed', key: 'bloomSpeed', min: 0.1, max: 1 },
            { id: 'stem-length', key: 'stemLength', min: 40, max: 200 },
            { id: 'glow-strength', key: 'glowStrength', min: 0.5, max: 3 },
            { id: 'petal-count', key: 'petalCount', min: 3, max: 12 }
        ];

        controls.forEach(control => {
            const slider = document.getElementById(control.id);
            const valueDisplay = document.getElementById(`${control.id}-value`);

            slider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                settings[control.key] = value;

                // Update display
                if (control.key === 'petalCount' || control.key === 'stemLength') {
                    valueDisplay.textContent = Math.round(value);
                } else {
                    valueDisplay.textContent = value.toFixed(2);
                }

                // Update scene if needed
                if (control.key === 'glowStrength') {
                    SceneModule.updateSettings(settings);
                }
            });

            // Initialize display
            valueDisplay.textContent = control.key === 'petalCount' || control.key === 'stemLength' 
                ? Math.round(settings[control.key]) 
                : settings[control.key].toFixed(2);
        });
    };

    const updateDebugHUD = (handsData) => {
        const overlay = document.getElementById('ui-overlay');
        overlay.innerHTML = '';

        Object.keys(handsData).forEach((hand, idx) => {
            const data = handsData[hand];
            if (!data) return;

            const hud = document.createElement('div');
            hud.className = 'hud';
            hud.style.left = `${data.anchorX + 20}px`;
            hud.style.top = `${data.anchorY + 20}px`;

            const params = HandTrackingModule.mapPinchToParams(data.pinchNormalized, settings.pinchSensitivity);

            hud.innerHTML = `
                <div style="color: ${hand === 'left' ? '#0f0' : '#ff0'};">
                    ${hand.toUpperCase()}<br>
                    Grow: ${(params.grow * 100).toFixed(0)}%<br>
                    Bloom: ${(params.bloom * 100).toFixed(0)}%<br>
                    Pinch: ${(data.pinchNormalized * 100).toFixed(0)}%
                </div>
            `;

            overlay.appendChild(hud);
        });
    };

    const stop = () => {
        isRunning = false;
        CameraModule.stop();
    };

    window.addEventListener('beforeunload', stop);

    return {
        init
    };
})();

// Start app when page loads
window.addEventListener('load', () => {
    // Load Three.js effects (UnrealBloomPass)
    const bloomScript = document.createElement('script');
    bloomScript.src = 'https://cdn.jsdelivr.net/npm/three@r128/examples/js/postprocessing/EffectComposer.js';
    document.head.appendChild(bloomScript);

    bloomScript.onload = () => {
        const renderPassScript = document.createElement('script');
        renderPassScript.src = 'https://cdn.jsdelivr.net/npm/three@r128/examples/js/postprocessing/RenderPass.js';
        document.head.appendChild(renderPassScript);

        renderPassScript.onload = () => {
            const bloomScript2 = document.createElement('script');
            bloomScript2.src = 'https://cdn.jsdelivr.net/npm/three@r128/examples/js/postprocessing/UnrealBloomPass.js';
            document.head.appendChild(bloomScript2);

            bloomScript2.onload = () => {
                App.init();
            };
        };
    };
});
