/**
 * handTracking.js - MediaPipe hand landmark tracking with smoothing
 */

const HandTrackingModule = (() => {
    let handLandmarker = null;
    let lastResults = null;
    let smoothedLandmarks = { left: {}, right: {} };
    let smoothingFactor = 0.6; // 0-1, lower = more smoothing

    // Initialize MediaPipe HandLandmarker
    const init = async () => {
        const vision = await window.Vision;
        
        const runningMode = 'VIDEO';
        handLandmarker = await vision.HandLandmarker.createFromOptions(
            { 
                baseOptions: {
                    modelAssetPath: `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm`
                },
                runningMode: runningMode,
                numHands: 2 
            }
        );

        CameraModule.updateStatus('✅ Hand tracking ready. Allow camera & move hands!', false);
    };

    // Smooth landmark position with exponential smoothing
    const smoothLandmark = (current, previous, factor = smoothingFactor) => {
        if (!previous) return current;
        return {
            x: previous.x + (current.x - previous.x) * factor,
            y: previous.y + (current.y - previous.y) * factor,
            z: previous.z + (current.z - previous.z) * factor
        };
    };

    // Process video frame and detect hand landmarks
    const detectHands = (videoElement) => {
        if (!handLandmarker) return { left: null, right: null };

        try {
            const results = handLandmarker.detectForVideo(
                videoElement,
                performance.now()
            );

            lastResults = results;
            return processResults(results, videoElement);
        } catch (err) {
            console.warn('Hand detection error:', err);
            return { left: null, right: null };
        }
    };

    // Process raw MediaPipe results
    const processResults = (results, videoElement) => {
        const processed = { left: null, right: null };
        const videoWidth = videoElement.videoWidth;
        const videoHeight = videoElement.videoHeight;

        if (!results.landmarks || results.landmarks.length === 0) {
            return processed;
        }

        results.landmarks.forEach((landmarks, idx) => {
            const handedness = results.handedness[idx].displayName; // "Left" or "Right"
            const handKey = handedness === 'Left' ? 'left' : 'right';

            // Extract key landmarks
            const thumb = landmarks[4];
            const indexTip = landmarks[8];
            const indexKnuckle = landmarks[5];
            const wrist = landmarks[0];
            const middleKnuckle = landmarks[9];

            // Convert to screen space (normalized to 0-1, then scale)
            const thumbScreen = {
                x: thumb.x * videoWidth,
                y: thumb.y * videoHeight
            };
            const indexScreen = {
                x: indexTip.x * videoWidth,
                y: indexTip.y * videoHeight
            };

            // Calculate pinch distance (normalized)
            const pinchRaw = Math.hypot(
                indexTip.x - thumb.x,
                indexTip.y - thumb.y
            );
            
            // Normalize by hand size (wrist to middle knuckle)
            const handSizeRaw = Math.hypot(
                middleKnuckle.x - wrist.x,
                middleKnuckle.y - wrist.y
            );
            const pinchNormalized = handSizeRaw > 0 ? Math.min(1, pinchRaw / handSizeRaw) : 0;

            // Anchor point: midpoint between thumb and index
            const anchorX = (thumb.x + indexTip.x) / 2 * videoWidth;
            const anchorY = (thumb.y + indexTip.y) / 2 * videoHeight;

            // Smooth the data
            if (!smoothedLandmarks[handKey].anchorX) {
                smoothedLandmarks[handKey] = {
                    anchorX: anchorX,
                    anchorY: anchorY,
                    pinchNormalized: pinchNormalized,
                    thumbScreen: thumbScreen,
                    indexScreen: indexScreen
                };
            } else {
                smoothedLandmarks[handKey].anchorX = 
                    smoothedLandmarks[handKey].anchorX + (anchorX - smoothedLandmarks[handKey].anchorX) * 0.5;
                smoothedLandmarks[handKey].anchorY = 
                    smoothedLandmarks[handKey].anchorY + (anchorY - smoothedLandmarks[handKey].anchorY) * 0.5;
                smoothedLandmarks[handKey].pinchNormalized = 
                    smoothedLandmarks[handKey].pinchNormalized + (pinchNormalized - smoothedLandmarks[handKey].pinchNormalized) * 0.4;
                smoothedLandmarks[handKey].thumbScreen = thumbScreen;
                smoothedLandmarks[handKey].indexScreen = indexScreen;
            }

            processed[handKey] = smoothedLandmarks[handKey];
        });

        return processed;
    };

    // Map normalized pinch distance (0-1) to animation parameters
    const mapPinchToParams = (pinchNormalized, sensitivity = 1.0) => {
        // Grow: increases as pinch opens (0 closed → 1 wide open)
        const grow = Math.pow(Math.max(0, pinchNormalized * sensitivity), 0.8);
        
        // Bloom: inverse - fully open when pinch is wide, closed when pinched tight
        const bloom = Math.pow(Math.max(0, 1 - pinchNormalized * 0.5), 1.2);

        return { grow, bloom };
    };

    const getSmoothedLandmarks = () => smoothedLandmarks;
    const setSmoothingFactor = (factor) => {
        smoothingFactor = Math.max(0, Math.min(1, factor));
    };

    return {
        init,
        detectHands,
        mapPinchToParams,
        getSmoothedLandmarks,
        setSmoothingFactor
    };
})();
