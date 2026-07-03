/**
 * camera.js - Webcam setup and video feed management
 */

const CameraModule = (() => {
    let videoElement = null;
    let stream = null;
    let canvasWidth = 720;
    let canvasHeight = 1280;

    const init = async () => {
        videoElement = document.getElementById('video-feed');

        try {
            // Request camera access with proper constraints
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: false
            };

            stream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = stream;

            return new Promise((resolve) => {
                const checkVideo = setInterval(() => {
                    if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                        clearInterval(checkVideo);
                        canvasWidth = videoElement.videoWidth;
                        canvasHeight = videoElement.videoHeight;
                        updateStatus('✅ Camera ready. Initializing hand tracking...', false);
                        resolve();
                    }
                }, 100);

                setTimeout(() => {
                    clearInterval(checkVideo);
                    if (videoElement.readyState >= videoElement.HAVE_CURRENT_DATA) {
                        canvasWidth = videoElement.videoWidth;
                        canvasHeight = videoElement.videoHeight;
                        updateStatus('✅ Camera ready. Initializing hand tracking...', false);
                        resolve();
                    }
                }, 3000);
            });
        } catch (err) {
            console.error('Camera error:', err);
            updateStatus(`❌ Camera denied: ${err.name}. Check browser settings.`, true);
            throw err;
        }
    };

    const updateStatus = (message, isError = false) => {
        const statusEl = document.getElementById('status');
        if (statusEl) {
            statusEl.innerHTML = `<span>${message}</span>`;
            statusEl.classList.toggle('error', isError);
            statusEl.classList.toggle('loading', !isError && message.includes('...'));
        }
    };

    const getVideoElement = () => videoElement;
    const getStream = () => stream;
    const getCanvasWidth = () => canvasWidth;
    const getCanvasHeight = () => canvasHeight;

    const stop = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    };

    return {
        init,
        getVideoElement,
        getStream,
        getCanvasWidth,
        getCanvasHeight,
        stop,
        updateStatus
    };
})();
