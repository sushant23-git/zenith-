import cv2
import numpy as np
import random
import time

class Particle:
    def __init__(self, x, y, color=None):
        self.x = float(x)
        self.y = float(y)
        # Float upwards with slight horizontal drift
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-3.5, -1.5)
        self.radius = random.uniform(2.5, 6.0)
        self.alpha = 1.0
        self.decay = random.uniform(0.015, 0.035)
        
        # Magical pollen colors: gold, light orange, soft pink, white
        colors = [
            (50, 210, 255),   # Golden Yellow
            (10, 130, 240),   # Light Orange
            (180, 150, 255),  # Soft Pink/Lavender
            (255, 255, 255)   # White Sparkle
        ]
        self.color = color if color is not None else random.choice(colors)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay
        self.radius = max(0.5, self.radius - 0.06)
        return self.alpha > 0

    def draw(self, img):
        h, w = img.shape[:2]
        ix, iy = int(self.x), int(self.y)
        r = int(self.radius)
        
        # Bound check
        if ix - r < 0 or ix + r >= w or iy - r < 0 or iy + r >= h:
            return
            
        # Draw transparent circle
        x1, y1 = max(0, ix - r), max(0, iy - r)
        x2, y2 = min(w, ix + r + 1), min(h, iy + r + 1)
        
        if x2 > x1 and y2 > y1:
            roi = img[y1:y2, x1:x2]
            overlay = roi.copy()
            cv2.circle(overlay, (ix - x1, iy - y1), r, self.color, -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, self.alpha, roi, 1.0 - self.alpha, 0, dst=roi)

class FlowerSystem:
    def __init__(self):
        self.particles = []
        
        # Static local coordinate offsets for lily petal freckles to avoid frame-to-frame flickering
        self.freckles = [
            (20, 3), (28, -5), (35, 4), (24, -2), (32, 2), (18, -4)
        ]
        
    def add_particles_from_center(self, cx, cy, count=1):
        for _ in range(count):
            self.particles.append(Particle(cx, cy))

    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw_particles(self, img):
        for p in self.particles:
            p.draw(img)

    def draw_bezier_stem(self, img, p0, p1, p2, p3, color=(46, 125, 50), thickness=5):
        """Draws a smooth green stem using a cubic Bezier curve."""
        points = []
        for t in np.linspace(0, 1, 30):
            pt = (
                (1 - t)**3 * np.array(p0) +
                3 * (1 - t)**2 * t * np.array(p1) +
                3 * (1 - t) * t**2 * np.array(p2) +
                t**3 * np.array(p3)
            )
            points.append(pt.astype(int))
            
        points = np.array(points, dtype=np.int32)
        cv2.polylines(img, [points], isClosed=False, color=color, thickness=thickness, lineType=cv2.LINE_AA)
        return points

    def draw_leaf(self, img, center, tangent, size_scale, side="left"):
        """Draws a pointed leaf branching off the stem."""
        angle_rad = np.arctan2(tangent[1], tangent[0])
        angle_deg = np.degrees(angle_rad)
        
        offset = -50 if side == "left" else 50
        leaf_angle = angle_deg + offset
        
        length = int((20 + 20 * size_scale))
        width = int((8 + 6 * size_scale))
        
        dist = length // 2
        lc_x = int(center[0] + dist * np.cos(np.radians(leaf_angle)))
        lc_y = int(center[1] + dist * np.sin(np.radians(leaf_angle)))
        
        # Forest green leaf
        leaf_color = (46, 115, 45)
        
        h_img, w_img = img.shape[:2]
        r_max = max(length, width) + 10
        x1, y1 = max(0, lc_x - r_max), max(0, lc_y - r_max)
        x2, y2 = min(w_img, lc_x + r_max), min(h_img, lc_y + r_max)
        
        if x2 > x1 and y2 > y1:
            roi = img[y1:y2, x1:x2]
            overlay = roi.copy()
            
            # Pointed leaf polygon (similar to lily petals but green)
            local_pts = self.get_pointed_shape_points(length, width)
            rotated_pts = self.rotate_and_translate(local_pts, leaf_angle, lc_x - x1, lc_y - y1)
            
            cv2.fillPoly(overlay, [rotated_pts], leaf_color, cv2.LINE_AA)
            
            # Central vein
            vein_color = (25, 80, 25)
            tip_x = lc_x + length * np.cos(np.radians(leaf_angle))
            tip_y = lc_y + length * np.sin(np.radians(leaf_angle))
            cv2.line(
                overlay, 
                (int(center[0] - x1), int(center[1] - y1)), 
                (int(tip_x - x1), int(tip_y - y1)), 
                vein_color, 
                1, 
                cv2.LINE_AA
            )
            
            cv2.addWeighted(overlay, 0.85, roi, 0.15, 0, dst=roi)

    def get_pointed_shape_points(self, length, width):
        """Generates local coordinate points for a pointed Lily petal/leaf."""
        points = []
        num_samples = 12
        # Upper edge: starts at base (0,0), curves out to width, tapers sharply to tip (length, 0)
        for t in np.linspace(0, 1, num_samples):
            x = t * length
            # Lily shape: widest around t=0.35, then tapering sharply using power of (1-t)
            y = width * np.sin(np.pi * t) * (1.0 - t)**0.28
            points.append([x, y])
        # Lower edge: from tip back to base
        for t in np.linspace(1, 0, num_samples):
            x = t * length
            y = -width * np.sin(np.pi * t) * (1.0 - t)**0.28
            points.append([x, y])
        return np.array(points, dtype=np.float32)

    def rotate_and_translate(self, points, angle_deg, cx, cy):
        """Rotates points by angle_deg and translates to (cx, cy)."""
        rad = np.radians(angle_deg)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        R = np.array([[cos_a, -sin_a],
                      [sin_a, cos_a]])
        rotated = np.dot(points, R.T)
        translated = rotated + np.array([cx, cy])
        return translated.astype(np.int32)

    def draw_single_lily(self, img, cx, cy, bloom, spin_angle):
        """Draws a single high-fidelity Lily flower at (cx, cy)."""
        h_img, w_img = img.shape[:2]
        
        # Set max dimensions
        max_petal_length = 75
        max_petal_width = 24
        
        # Sizing based on bloom
        petal_length = int(15 + (max_petal_length - 15) * bloom)
        petal_width = int(6 + (max_petal_width - 6) * bloom)
        
        # ROI bounding box for localized blending
        r_bloom = max_petal_length + 30
        x1, y1 = max(0, cx - r_bloom), max(0, cy - r_bloom)
        x2, y2 = min(w_img, cx + r_bloom), min(h_img, cy + r_bloom)
        
        if x2 > x1 and y2 > y1:
            roi = img[y1:y2, x1:x2]
            overlay = roi.copy()
            
            # Local coordinates of the flower center
            lcx, lcy = cx - x1, cy - y1
            
            # Lilies have 6 petals: arranged in 2 layers of 3 (outer/inner), spaced 60 degrees apart
            # Base color: soft white/light cream-pink BGR: (235, 240, 255)
            # Center blush color: deep rose BGR: (120, 60, 240)
            base_color = (235, 240, 255)
            blush_color = (130, 70, 245)
            freckle_color = (60, 20, 150) # Dark magenta spots
            
            # Petal shape polygon in local space
            petal_shape = self.get_pointed_shape_points(petal_length, petal_width)
            # Blush shape (narrower and shorter)
            blush_shape = self.get_pointed_shape_points(int(petal_length * 0.85), int(petal_width * 0.3))
            
            # Draw the 6 petals
            for i in range(6):
                angle = spin_angle + i * 60.0
                
                # 1. Draw base white petal
                rotated_petal = self.rotate_and_translate(petal_shape, angle, lcx, lcy)
                cv2.fillPoly(overlay, [rotated_petal], base_color, cv2.LINE_AA)
                cv2.polylines(overlay, [rotated_petal], True, (210, 215, 230), 1, cv2.LINE_AA) # subtle outline
                
                # 2. Draw pink central stripe (blush)
                rotated_blush = self.rotate_and_translate(blush_shape, angle, lcx, lcy)
                cv2.fillPoly(overlay, [rotated_blush], blush_color, cv2.LINE_AA)
                
                # 3. Draw freckle dots (only if bloomed enough to expose center)
                if bloom > 0.3:
                    spots_scale = (bloom - 0.3) / 0.7
                    for fx, fy in self.freckles:
                        # Scale coordinates of freckles with bloom
                        sfx, sfy = fx * bloom, fy * bloom
                        # Rotate and translate individual freckle coordinates
                        rad = np.radians(angle)
                        rx = sfx * np.cos(rad) - sfy * np.sin(rad)
                        ry = sfx * np.sin(rad) + sfy * np.cos(rad)
                        cv2.circle(
                            overlay, 
                            (int(lcx + rx), int(lcy + ry)), 
                            int(1 + 1 * spots_scale), 
                            freckle_color, 
                            -1, 
                            cv2.LINE_AA
                        )
            
            # 4. Draw Stamens (6 curved filaments extending outward)
            # Only grow stamens when bloom > 0.4
            if bloom > 0.4:
                stamen_bloom = (bloom - 0.4) / 0.6
                stamen_len = int(25 + 30 * stamen_bloom)
                
                # Filament color: pale yellow-green BGR: (180, 240, 200)
                filament_color = (180, 240, 200)
                # Anther color: large reddish-brown pollen sacs BGR: (15, 55, 105)
                anther_color = (15, 55, 105)
                
                for i in range(6):
                    # Align stamens offset between the petals
                    angle = spin_angle + i * 60.0 + 30.0
                    rad = np.radians(angle)
                    
                    # Curved filament coordinates using a simple bow offset
                    mid_ang = np.radians(angle - 15 * (1.0 - stamen_bloom))
                    
                    # Points along the filament curve
                    p_start = (lcx, lcy)
                    p_mid = (
                        int(lcx + (stamen_len * 0.55) * np.cos(mid_ang)),
                        int(lcy + (stamen_len * 0.55) * np.sin(mid_ang))
                    )
                    p_end = (
                        int(lcx + stamen_len * np.cos(rad)),
                        int(lcy + stamen_len * np.sin(rad))
                    )
                    
                    # Draw filament as curve (polylines)
                    fil_pts = np.array([p_start, p_mid, p_end], dtype=np.int32)
                    cv2.polylines(overlay, [fil_pts], False, filament_color, 2, cv2.LINE_AA)
                    
                    # Draw large T-shaped Lily Anther at the tip
                    # We draw a small rectangle/ellipse perpendicular to the stamen angle
                    anther_w = int(3 + 3 * stamen_bloom)
                    anther_h = int(8 + 8 * stamen_bloom)
                    cv2.ellipse(
                        overlay, 
                        p_end, 
                        (anther_h // 2, anther_w // 2), 
                        angle + 90.0, 
                        0, 360, 
                        anther_color, 
                        -1, 
                        cv2.LINE_AA
                    )
                    
            # 5. Center Pistil (Green, 3-lobed stigma in the very middle)
            pistil_color = (50, 160, 60) # Bright green BGR
            pistil_rad = int(3 + 5 * bloom)
            cv2.circle(overlay, (lcx, lcy), pistil_rad, pistil_color, -1, cv2.LINE_AA)
            if bloom > 0.5:
                # 3 small lobes
                stigma_bloom = (bloom - 0.5) / 0.5
                for a in [0, 120, 240]:
                    lx = int(lcx + (pistil_rad + 3 * stigma_bloom) * np.cos(np.radians(a + spin_angle * 0.5)))
                    ly = int(lcy + (pistil_rad + 3 * stigma_bloom) * np.sin(np.radians(a + spin_angle * 0.5)))
                    cv2.circle(overlay, (lx, ly), int(2 * stigma_bloom), (70, 190, 80), -1, cv2.LINE_AA)

            # Alpha blend the lily flower
            alpha = 0.82 + 0.13 * bloom
            cv2.addWeighted(overlay, alpha, roi, 1.0 - alpha, 0, dst=roi)

    def draw_flower(self, img, cx, cy, bloom, spin_angle, num_flowers=1):
        """Draws a bouquet of Lily flowers at the right hand location."""
        h_img, w_img = img.shape[:2]
        
        # 1. Calculate positions for N flowers in a bouquet arrangement
        # We place them in a fan-shaped cluster above the hand midpoint (cx, cy)
        flower_positions = []
        if num_flowers <= 1:
            flower_positions = [(cx, cy)]
        elif num_flowers == 2:
            flower_positions = [(cx - 35, cy - 20), (cx + 35, cy - 20)]
        elif num_flowers == 3:
            flower_positions = [(cx - 45, cy - 10), (cx, cy - 40), (cx + 45, cy - 10)]
        elif num_flowers == 4:
            flower_positions = [(cx - 55, cy + 5), (cx - 20, cy - 35), (cx + 20, cy - 35), (cx + 55, cy + 5)]
        else: # 5 flowers
            flower_positions = [(cx - 65, cy + 15), (cx - 35, cy - 25), (cx, cy - 50), (cx + 35, cy - 25), (cx + 65, cy + 15)]
            
        # 2. Draw stems for all flowers
        # All stems root at the bottom center of the screen (cx, h_img) and merge together,
        # branching out to their respective flower centers.
        p0 = (cx, h_img)
        screen_center_x = w_img // 2
        bend_factor = (cx - screen_center_x) * 0.45
        
        # Shared intermediate control points to make them bundle together near the hand
        p1 = (int(cx - bend_factor), int(cy + (h_img - cy) * 0.65))
        p2 = (int(cx + bend_factor * 0.5), int(cy + (h_img - cy) * 0.35))
        
        for i, (fcx, fcy) in enumerate(flower_positions):
            # Draw individual stems branching out to each lily
            # We vary the thickness: middle stems are slightly thicker
            thickness = 5 if i == (num_flowers // 2) else 4
            stem_pts = self.draw_bezier_stem(img, p0, p1, p2, (fcx, fcy), color=(46, 125, 50), thickness=thickness)
            
            # Draw leaves on the stems
            if len(stem_pts) >= 30:
                # Leaf 1 (Left branch)
                idx1 = 12
                self.draw_leaf(img, stem_pts[idx1], stem_pts[idx1+1] - stem_pts[idx1-1], bloom, side="left")
                # Leaf 2 (Right branch, higher up)
                idx2 = 21
                self.draw_leaf(img, stem_pts[idx2], stem_pts[idx2+1] - stem_pts[idx2-1], bloom, side="right")

        # 3. Draw the Lilies on top of the stems
        # Draw from outer/lower to inner/higher to ensure proper overlapping layering
        sorted_flowers = sorted(enumerate(flower_positions), key=lambda x: x[1][1], reverse=True)
        for idx, (fcx, fcy) in sorted_flowers:
            # Add slight individual spin offset to make each flower look unique
            indiv_spin = spin_angle + idx * 45.0
            self.draw_single_lily(img, fcx, fcy, bloom, indiv_spin)
            
        # 4. Generate particles from all bloomed flower centers
        if bloom > 0.75:
            spawn_chance = (bloom - 0.75) / 0.25
            for fcx, fcy in flower_positions:
                if random.random() < spawn_chance * 0.25:
                    self.add_particles_from_center(fcx, fcy, count=1)
                    
        # Update and draw active particles
        self.update_particles()
        self.draw_particles(img)
