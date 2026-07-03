import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import sys
from flower import FlowerSystem

def draw_hud(frame, bloom_factor, fps, bloom_hand_detected, count_hand_detected, num_flowers, min_pinch, max_pinch, current_pinch):
    """Draws a premium glassmorphic HUD on the camera screen."""
    h, w = frame.shape[:2]
    
    # 1. Title Bar (Dark overlay at the top)
    banner_h = 60
    roi = frame[0:banner_h, 0:w]
    overlay = roi.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_h), (15, 15, 20), -1)
    cv2.addWeighted(overlay, 0.65, roi, 0.35, 0, dst=roi)
    
    # Add title text
    title_text = "ANTIGRAVITY LILY BOUQUET SHOWCASE"
    cv2.putText(frame, title_text, (20, 38), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add FPS indicator
    fps_text = f"FPS: {int(fps)}"
    cv2.putText(frame, fps_text, (w - 120, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 255, 120), 1, cv2.LINE_AA)
    
    # 2. Bottom Control Panel / Info
    panel_h = 65
    roi_bottom = frame[h-panel_h:h, 0:w]
    overlay_bottom = roi_bottom.copy()
    cv2.rectangle(overlay_bottom, (0, 0), (w, panel_h), (15, 15, 20), -1)
    cv2.addWeighted(overlay_bottom, 0.65, roi_bottom, 0.35, 0, dst=roi_bottom)
    
    # Instructions
    inst1 = "Right Hand: Position & Pinch Bloom (3D Tracked)"
    inst2 = "Left Hand: Show 1-5 fingers to change Lily Count"
    cv2.putText(frame, inst1, (20, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, inst2, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    
    # Hand tracking indicators (Right / Left)
    bloom_led = (50, 255, 50) if bloom_hand_detected else (50, 50, 200)
    bloom_lbl = "BLOOM HAND [R]: ACTIVE" if bloom_hand_detected else "BLOOM HAND [R]: SEARCHING"
    cv2.circle(frame, (w - 280, h - 43), 5, bloom_led, -1, cv2.LINE_AA)
    cv2.putText(frame, bloom_lbl, (w - 265, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    
    count_led = (255, 150, 50) if count_hand_detected else (50, 50, 200)
    count_lbl = f"COUNT HAND [L]: {num_flowers} LILIES" if count_hand_detected else f"COUNT HAND [L]: DEFAULT ({num_flowers})"
    cv2.circle(frame, (w - 280, h - 23), 5, count_led, -1, cv2.LINE_AA)
    cv2.putText(frame, count_lbl, (w - 265, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Bloom Progress Bar (Vertical indicator on the left side)
    bar_w = 22
    bar_h = 220
    bar_x = 30
    bar_y = (h - bar_h) // 2
    
    # Draw glass background panel for the bar
    panel_pad = 15
    bar_roi = frame[bar_y-panel_pad : bar_y+bar_h+panel_pad, bar_x-panel_pad : bar_x+bar_w+panel_pad]
    bar_overlay = bar_roi.copy()
    cv2.rectangle(bar_overlay, (0, 0), (bar_overlay.shape[1], bar_overlay.shape[0]), (25, 25, 30), -1)
    cv2.addWeighted(bar_overlay, 0.55, bar_roi, 0.45, 0, dst=bar_roi)
    
    # Draw progress track
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), 1, cv2.LINE_AA)
    
    # Draw progress fill
    fill_h = int(bar_h * bloom_factor)
    if fill_h > 0:
        # Peach pink to vibrant rose vertical gradient block
        cv2.rectangle(
            frame, 
            (bar_x + 1, bar_y + bar_h - fill_h), 
            (bar_x + bar_w - 1, bar_y + bar_h - 1), 
            (140, 90, 245), 
            -1
        )
        
    # Text percentage
    pct_text = f"{int(bloom_factor * 100)}%"
    cv2.putText(frame, pct_text, (bar_x - 5, bar_y - 25), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # 3D distance debug readout below the bar
    if bloom_hand_detected:
        dist_cm = current_pinch * 100
        min_cm = min_pinch * 100
        max_cm = max_pinch * 100
        debug_txt = f"{dist_cm:.1f}cm"
        range_txt = f"[{min_cm:.1f}-{max_cm:.1f}]"
        cv2.putText(frame, debug_txt, (bar_x - 12, bar_y + bar_h + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, range_txt, (bar_x - 20, bar_y + bar_h + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1, cv2.LINE_AA)

def count_extended_fingers(landmarks):
    """Counts the number of extended fingers on the hand (0 to 5)."""
    # Helper to compute 2D distance between landmarks
    def get_dist_2d(idx1, idx2):
        p1 = np.array([landmarks[idx1].x, landmarks[idx1].y])
        p2 = np.array([landmarks[idx2].x, landmarks[idx2].y])
        return np.linalg.norm(p1 - p2)
        
    # 1. Thumb: Check if the thumb tip (4) is stretched away from the Index MCP knuckle (5)
    # relative to the thumb joint distance.
    is_thumb_open = get_dist_2d(4, 5) > get_dist_2d(3, 5) * 1.15
    
    # 2. Four Fingers: Check if the tip landmark is higher (lower y-value on screen)
    # than the respective PIP (middle joint) landmark.
    is_index_open = landmarks[8].y < landmarks[6].y
    is_middle_open = landmarks[12].y < landmarks[10].y
    is_ring_open = landmarks[16].y < landmarks[14].y
    is_pinky_open = landmarks[20].y < landmarks[18].y
    
    count = 0
    if is_thumb_open: count += 1
    if is_index_open: count += 1
    if is_middle_open: count += 1
    if is_ring_open: count += 1
    if is_pinky_open: count += 1
    
    return count

def main():
    # Initialize Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        sys.exit(1)
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Initialize MediaPipe Hands using Tasks API
    # We configure it to detect up to 2 hands
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6
    )
    detector = vision.HandLandmarker.create_from_options(options)
    
    # Initialize Flower System
    flower_system = FlowerSystem()
    
    # State tracking
    prev_time = time.time()
    fps = 30.0
    
    # Flower status state machine
    # States: "HIDDEN", "VISIBLE", "FADING"
    flower_state = "HIDDEN"
    flower_opacity = 0.0
    
    # Smoothed positions and factors
    cx_smooth, cy_smooth = 0, 0
    bloom_smooth = 0.0
    
    # 3D Pinch calibration (measured in meters using hand_world_landmarks)
    # Fingers touching: ~1.5cm (0.015m) | Fingers open: ~8.5cm (0.085m)
    min_pinch_3d = 0.02
    max_pinch_3d = 0.08
    current_pinch_3d = 0.02
    
    # Bouquet size tracking and stabilization
    # Left hand finger counts are smoothed using a rolling mode filter
    num_flowers = 1
    finger_history = []
    
    # Spin angle for lily rotation
    spin_angle = 0.0
    
    start_time_ms = int(time.time() * 1000)
    print("Lily Bouquet Application started. Press ESC in the camera box to exit.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image.")
            break
            
        # Flip frame horizontally for natural mirrored feel
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Convert to RGB for MediaPipe Tasks
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Process frame
        elapsed_time_ms = int(time.time() * 1000) - start_time_ms
        results = detector.detect_for_video(mp_image, elapsed_time_ms)
        
        # Flags for hand presence in current frame
        bloom_hand_detected = False
        count_hand_detected = False
        
        if results.hand_landmarks and results.handedness:
            # MediaPipe classifies handedness on the mirrored frame.
            # Due to mirroring:
            # - Physical Right Hand looks like a Left Hand -> classified as "Left"
            # - Physical Left Hand looks like a Right Hand -> classified as "Right"
            bloom_hand_idx = None  # Controls position and 3D pinch bloom (MediaPipe "Left")
            count_hand_idx = None  # Controls flower count (MediaPipe "Right")
            
            for i, hand_handedness in enumerate(results.handedness):
                label = hand_handedness[0].category_name
                if label == "Left":
                    bloom_hand_idx = i
                elif label == "Right":
                    count_hand_idx = i
            
            # 1. Process Left Hand (MediaPipe "Right") -> Finger Count
            if count_hand_idx is not None:
                count_hand_detected = True
                count_landmarks = results.hand_landmarks[count_hand_idx]
                raw_fingers = count_extended_fingers(count_landmarks)
                
                # We default 0 fingers to 1 flower
                target_flowers = max(1, raw_fingers)
                
                # Smooth the count using a rolling filter (last 8 frames)
                finger_history.append(target_flowers)
                if len(finger_history) > 8:
                    finger_history.pop(0)
                
                # Mode filtering to remove flicker
                num_flowers = max(1, max(set(finger_history), key=finger_history.count))
                
            # 2. Process Right Hand (MediaPipe "Left") -> 3D Pinch Bloom & Position
            if bloom_hand_idx is not None:
                bloom_hand_detected = True
                bloom_landmarks = results.hand_landmarks[bloom_hand_idx]
                world_landmarks = results.hand_world_landmarks[bloom_hand_idx]
                
                # Calculate 3D Euclidean distance in meters
                # Landmark 4: Thumb Tip, Landmark 8: Index Tip
                p4 = np.array([world_landmarks[4].x, world_landmarks[4].y, world_landmarks[4].z])
                p8 = np.array([world_landmarks[8].x, world_landmarks[8].y, world_landmarks[8].z])
                dist_3d = np.linalg.norm(p4 - p8)
                current_pinch_3d = dist_3d
                
                # Dynamic calibration to adapt to the user's specific pinch reach
                if dist_3d < min_pinch_3d:
                    min_pinch_3d = 0.95 * min_pinch_3d + 0.05 * dist_3d
                if dist_3d > max_pinch_3d and dist_3d < 0.20:
                    max_pinch_3d = 0.95 * max_pinch_3d + 0.05 * dist_3d
                    
                # Keep minimum spacing between min and max bounds
                if max_pinch_3d - min_pinch_3d < 0.04:
                    max_pinch_3d = min_pinch_3d + 0.04
                    
                # Calculate bloom factor
                raw_bloom = (dist_3d - min_pinch_3d) / (max_pinch_3d - min_pinch_3d)
                raw_bloom = np.clip(raw_bloom, 0.0, 1.0)
                
                # Exponential smoothing
                bloom_smooth = 0.15 * raw_bloom + 0.85 * bloom_smooth
                
                # Bounding box center coordinates (in pixels)
                # Midpoint between Thumb Tip and Index Tip
                p_thumb_pix = np.array([int(bloom_landmarks[4].x * w), int(bloom_landmarks[4].y * h)])
                p_index_pix = np.array([int(bloom_landmarks[8].x * w), int(bloom_landmarks[8].y * h)])
                target_cx = int((p_thumb_pix[0] + p_index_pix[0]) / 2)
                target_cy = int((p_thumb_pix[1] + p_index_pix[1]) / 2)
                
                if flower_state == "HIDDEN":
                    flower_state = "VISIBLE"
                    cx_smooth, cy_smooth = target_cx, target_cy
                elif flower_state == "FADING":
                    flower_state = "VISIBLE"
                    
                # Smooth movement (responsive EMA)
                cx_smooth = int(0.25 * target_cx + 0.75 * cx_smooth)
                cy_smooth = int(0.25 * target_cy + 0.75 * cy_smooth)
                flower_opacity = min(1.0, flower_opacity + 0.1)
                
        # Hand tracking fallback
        if not bloom_hand_detected:
            if flower_state == "VISIBLE":
                flower_state = "FADING"
                
            if flower_state == "FADING":
                flower_opacity -= 0.04
                bloom_smooth = 0.95 * bloom_smooth + 0.05 * 0.0
                cy_smooth += 2 # slowly sink down
                
                if flower_opacity <= 0.0:
                    flower_opacity = 0.0
                    flower_state = "HIDDEN"
                    
        # Rotate petals
        spin_angle += 0.4 + 3.0 * bloom_smooth
        
        # Draw Lily Bouquet
        if flower_state != "HIDDEN":
            flower_system.draw_flower(frame, cx_smooth, cy_smooth, bloom_smooth, spin_angle, num_flowers=num_flowers)
            
        # FPS Calculation
        current_time = time.time()
        dt = current_time - prev_time
        prev_time = current_time
        if dt > 0:
            fps = 0.05 * (1.0 / dt) + 0.95 * fps
            
        # Draw HUD dashboard
        draw_hud(
            frame, 
            bloom_smooth, 
            fps, 
            bloom_hand_detected, 
            count_hand_detected, 
            num_flowers, 
            min_pinch_3d, 
            max_pinch_3d, 
            current_pinch_3d
        )
        
        cv2.imshow("Lily Bouquet Showcase", frame)
        
        # ESC key check
        if cv2.waitKey(1) & 0xFF == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()
    detector.close()

if __name__ == "__main__":
    main()
