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
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 720 },
                    height: { ideal: 1280 },
                    facingMode: 'user'
                }
            });

            videoElement.srcObject = stream;
            
            return new Promise((resolve) => {
                videoElement.onloadedmetadata = () => {
                    videoElement.play();
                    updateStatus('🌸 Camera ready. Initializing hand tracking...', false);
                    resolve();
                };
            });
        } catch (err) {
            updateStatus(`❌ Camera access denied: ${err.message}`, true);
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
