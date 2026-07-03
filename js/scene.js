/**
 * scene.js - Three.js scene setup with bloom post-processing
 */

const SceneModule = (() => {
    let scene = null;
    let camera = null;
    let renderer = null;
    let bloomPass = null;
    let composer = null;
    let flowerMeshes = { left: null, right: null };
    let debugMeshes = { left: { lines: [] }, right: { lines: [] } };

    const canvasWidth = 720;
    const canvasHeight = 1280;

    const init = (containerElement) => {
        // Scene setup
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x000000);

        // Camera - orthographic to match 2D overlay
        camera = new THREE.OrthographicCamera(
            0, canvasWidth,
            0, -canvasHeight,
            0.1, 1000
        );
        camera.position.z = 500;

        // Renderer
        renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            powerPreference: 'high-performance'
        });
        renderer.setSize(canvasWidth, canvasHeight);
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        renderer.setClearColor(0x000000, 0);

        // Find canvas container and append
        const debugOverlay = containerElement.querySelector('#debug-overlay');
        debugOverlay.style.display = 'none';
        debugOverlay.parentElement.appendChild(renderer.domElement);
        renderer.domElement.style.position = 'absolute';
        renderer.domElement.style.top = '0';
        renderer.domElement.style.left = '0';

        // Post-processing with bloom
        composer = new THREE.EffectComposer(renderer);
        const renderPass = new THREE.RenderPass(scene, camera);
        composer.addPass(renderPass);

        bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(canvasWidth, canvasHeight),
            1.5,  // strength
            0.8,  // radius
            0.85  // threshold
        );
        composer.addPass(bloomPass);

        initFlowerMeshes();
    };

    const initFlowerMeshes = () => {
        // Create materials
        const flowerMaterial = new THREE.PointsMaterial({
            size: 6,
            sizeAttenuation: true,
            transparent: true,
            vertexColors: true,
            blending: THREE.AdditiveBlending
        });

        // Create particle geometry for each hand
        ['left', 'right'].forEach(hand => {
            const geometry = new THREE.BufferGeometry();
            
            // Initialize with empty particles
            const positions = new Float32Array(1000 * 3);
            const colors = new Float32Array(1000 * 3);
            
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const points = new THREE.Points(geometry, flowerMaterial);
            scene.add(points);
            
            flowerMeshes[hand] = {
                mesh: points,
                geometry: geometry,
                lastParticleCount: 0
            };
        });
    };

    const updateFlowerMesh = (hand, flowerData, glowStrength) => {
        if (!flowerData || !flowerData.isActive) return;

        const mesh = flowerMeshes[hand].mesh;
        const geometry = flowerMeshes[hand].geometry;
        const particles = flowerData.particles;

        const positions = geometry.attributes.position.array;
        const colors = geometry.attributes.color.array;

        let idx = 0;
        particles.forEach(particle => {
            if (idx >= 1000) return;

            // World position
            const x = flowerData.anchorX + particle.offsetX * (0.3 + flowerData.growCurrent * 0.7);
            const y = flowerData.anchorY + particle.offsetY * (0.3 + flowerData.growCurrent * 0.7);
            const z = particle.offsetZ * flowerData.bloomCurrent;

            positions[idx * 3] = x;
            positions[idx * 3 + 1] = y;
            positions[idx * 3 + 2] = z;

            // Color with intensity and alpha influence
            const intensity = particle.intensity * (0.5 + flowerData.bloomCurrent * 0.5) * glowStrength;
            const alpha = particle.intensity * flowerData.fadeAlpha;

            colors[idx * 3] = particle.color.r * intensity;
            colors[idx * 3 + 1] = particle.color.g * intensity;
            colors[idx * 3 + 2] = particle.color.b * intensity;

            idx++;
        });

        geometry.attributes.position.needsUpdate = true;
        geometry.attributes.color.needsUpdate = true;
        geometry.setDrawRange(0, particles.length);

        mesh.visible = flowerData.isActive;
    };

    const drawDebugOverlay = (handsData) => {
        const canvas = document.getElementById('debug-overlay');
        if (canvas.style.display === 'none') return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvasWidth, canvasHeight);
        ctx.lineWidth = 2;

        Object.keys(handsData).forEach(hand => {
            if (!handsData[hand]) return;

            const data = handsData[hand];
            const color = hand === 'left' ? '#ff00ff' : '#ff00ff';

            // Draw pinch line (thumb to index)
            ctx.strokeStyle = color;
            ctx.beginPath();
            ctx.moveTo(data.thumbScreen.x, data.thumbScreen.y);
            ctx.lineTo(data.indexScreen.x, data.indexScreen.y);
            ctx.stroke();

            // Draw anchor point
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(data.anchorX, data.anchorY, 5, 0, Math.PI * 2);
            ctx.fill();

            // Draw debug text
            const text = `${hand.toUpperCase()}\nPinch: ${(data.pinchNormalized * 100).toFixed(0)}%`;
            ctx.fillStyle = color;
            ctx.font = '11px Courier New';
            ctx.fillText(text, data.anchorX + 15, data.anchorY - 10);
        });
    };

    const updateSettings = (settings) => {
        if (bloomPass) {
            bloomPass.strength = settings.glowStrength;
        }
    };

    const render = (handsData, settings) => {
        // Update flowers
        const flowers = FlowerModule.getFlowers();
        ['left', 'right'].forEach(hand => {
            if (flowers[hand]) {
                const flowerData = FlowerModule.getFlowerData(flowers[hand], canvasWidth, canvasHeight);
                updateFlowerMesh(hand, flowerData, settings.glowStrength);
            }
        });

        // Render scene
        composer.render();

        // Draw debug overlay if enabled
        drawDebugOverlay(handsData);
    };

    const getRenderer = () => renderer;
    const getScene = () => scene;
    const getCamera = () => camera;

    return {
        init,
        render,
        updateSettings,
        getRenderer,
        getScene,
        getCamera
    };
})();
