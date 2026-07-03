/**
 * flower.js - Flower particle system and animation
 */

const FlowerModule = (() => {
    const flowers = {
        left: null,
        right: null
    };

    // Easing functions
    const easeOutElastic = (t) => {
        const c5 = (2 * Math.PI) / 4.5;
        return t === 0 ? 0 : t === 1 ? 1 : 
            Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c5) + 1;
    };

    const easeOutQuad = (t) => 1 - (1 - t) * (1 - t);

    // Curl noise for organic wobble
    const curlNoise = (x, y, z, time) => {
        // Simplified Perlin-like noise
        const n = Math.sin(x * 12.9898 + y * 78.233 + z * 45.164 + time * 0.5) * 43758.5453;
        return n - Math.floor(n);
    };

    // Create a flower object
    const createFlower = (handKey) => {
        return {
            handKey: handKey,
            anchorX: 0,
            anchorY: 0,
            growTarget: 0,
            growCurrent: 0,
            bloomTarget: 0,
            bloomCurrent: 0,
            particles: [],
            isActive: true,
            fadeOutTime: 0,
            maxFadeOutDuration: 1.5, // seconds
            createdAt: Date.now()
        };
    };

    // Generate petal particles
    const generatePetalParticles = (flower, petalCount, stemLength, bloomInfluence) => {
        flower.particles = [];
        const baseRadius = 8;

        // Stem particles
        const stemSegments = Math.floor(stemLength / 5);
        for (let i = 0; i < stemSegments; i++) {
            const t = i / stemSegments;
            const wobble = curlNoise(i, 0, t, Date.now() / 1000) * 8;
            flower.particles.push({
                type: 'stem',
                offsetX: wobble,
                offsetY: -t * stemLength,
                offsetZ: 0,
                color: { r: 0.8, g: 0.4, b: 0.1 },
                intensity: 0.6,
                size: 3
            });
        }

        // Petals arranged in a circle
        for (let i = 0; i < petalCount; i++) {
            const angle = (i / petalCount) * Math.PI * 2;
            const petalLength = baseRadius * (0.5 + bloomInfluence * 0.8);
            const wobble = curlNoise(angle, i, bloomInfluence, Date.now() / 1000) * 4;

            // Petal curve control points
            const numPetalParticles = 6;
            for (let p = 0; p < numPetalParticles; p++) {
                const t = p / numPetalParticles;
                const dist = petalLength * easeOutQuad(t);
                const spreadAngle = angle + (Math.random() - 0.5) * 0.3;

                const x = Math.cos(spreadAngle) * dist + wobble;
                const y = -stemLength + Math.sin(spreadAngle) * dist * 0.5;
                const z = (Math.random() - 0.5) * 8;

                // Color gradient: deep orange → yellow/white
                const colorT = t;
                const r = 0.9 + colorT * 0.1;
                const g = 0.4 + colorT * 0.6;
                const b = 0.1 + colorT * 0.8;

                flower.particles.push({
                    type: 'petal',
                    offsetX: x,
                    offsetY: y,
                    offsetZ: z,
                    color: { r, g, b },
                    intensity: 0.8 + t * 0.4,
                    size: 4 + t * 2
                });
            }
        }
    };

    const updateFlower = (flower, handData, settings, deltaTime) => {
        if (!handData) {
            // Hand lost - fade out
            flower.isActive = false;
            flower.fadeOutTime += deltaTime;
            
            if (flower.fadeOutTime >= flower.maxFadeOutDuration) {
                return false; // Remove flower
            }

            flower.growTarget = 0;
            flower.bloomTarget = 0;
        } else {
            flower.isActive = true;
            flower.fadeOutTime = 0;
            flower.anchorX = handData.anchorX;
            flower.anchorY = handData.anchorY;

            // Map pinch to grow/bloom parameters
            const params = HandTrackingModule.mapPinchToParams(
                handData.pinchNormalized,
                settings.pinchSensitivity
            );

            flower.growTarget = params.grow;
            flower.bloomTarget = params.bloom;
        }

        // Smoothly animate grow and bloom
        const bloomSpeed = settings.bloomSpeed;
        flower.growCurrent += (flower.growTarget - flower.growCurrent) * bloomSpeed * 0.5;
        flower.bloomCurrent += (flower.bloomTarget - flower.bloomCurrent) * bloomSpeed;

        // Regenerate petals if bloom changed significantly
        const petalCount = Math.round(settings.petalCount);
        if (!flower.particles.length || flower.particles.length === 0) {
            generatePetalParticles(flower, petalCount, settings.stemLength, flower.bloomCurrent);
        }

        return true; // Keep flower alive
    };

    const getFlowerData = (flower, sceneWidth, sceneHeight) => {
        if (!flower) return null;

        const fadeAlpha = flower.isActive ? 1 : 1 - (flower.fadeOutTime / flower.maxFadeOutDuration);
        
        return {
            anchorX: flower.anchorX,
            anchorY: flower.anchorY,
            growCurrent: flower.growCurrent,
            bloomCurrent: flower.bloomCurrent,
            particles: flower.particles,
            fadeAlpha: fadeAlpha,
            isActive: flower.isActive || flower.fadeOutTime < flower.maxFadeOutDuration
        };
    };

    const initFlowers = () => {
        flowers.left = createFlower('left');
        flowers.right = createFlower('right');
    };

    const updateFlowers = (handsData, settings, deltaTime) => {
        flowers.left = updateFlower(flowers.left, handsData.left, settings, deltaTime) ? flowers.left : null;
        flowers.right = updateFlower(flowers.right, handsData.right, settings, deltaTime) ? flowers.right : null;
    };

    const getFlowers = () => flowers;

    return {
        initFlowers,
        updateFlowers,
        getFlowers,
        getFlowerData,
        generatePetalParticles
    };
})();
