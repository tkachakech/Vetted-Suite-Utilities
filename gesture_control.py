#!/usr/bin/env python3
"""
GestureOS — Advanced Webcam-Based PC Control
Controls your PC via hand gestures and micro-facial expressions.
"""

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import json
import os
import sys
import time
import math
import threading
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import pystray
from PIL import Image, ImageDraw
import psutil

# ── Safety ──────────────────────────────────────────────────────────────────
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

CONFIG_PATH = Path.home() / ".gesture_os_config.json"

# ── Default Configuration ────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "camera_index": 0,
    "camera_width": 1280,
    "camera_height": 720,
    "camera_fps": 30,
    "detection_confidence": 0.75,
    "tracking_confidence": 0.75,
    "face_detection_confidence": 0.75,
    "smoothing_factor": 7,
    "gesture_cooldown_ms": 400,
    "show_landmarks": True,
    "show_fps": True,
    "show_gesture_label": True,
    "show_debug_overlay": False,
    "theme": "dark",
    "accent_color": "#00e5ff",
    "cursor_sensitivity": 1.4,
    "scroll_speed": 3,
    "click_dwell_ms": 0,
    "enable_hand_gestures": True,
    "enable_face_gestures": True,
    "font_size": 10,           # NEW — global UI font size (8–16)
    "high_contrast": False,    # NEW — high-contrast mode toggle
    "gesture_bindings": {
        "index_point": "move_cursor",
        "pinch": "left_click",
        "double_pinch": "double_click",
        "fist": "right_click",
        "open_hand": "scroll_mode",
        "peace": "screenshot",
        "thumbs_up": "volume_up",
        "thumbs_down": "volume_down",
        "call_me": "media_play_pause",
        "ok_sign": "middle_click",
        "brow_raise": "switch_window",
        "blink_left": "back",
        "blink_right": "forward",
        "mouth_open": "zoom_in",
        "smile": "zoom_out",
        "squint": "fullscreen",
    },
    "hotkey_mode_trigger": "peace",
    "deadzone_px": 30,
    "monitor_index": 0,
}

# ── Theme Palettes ───────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG":       "#0d0f1a",
        "PANEL":    "#13172b",
        "CARD":     "#1a1f38",
        "ACCENT":   "#00e5ff",
        "ACCENT2":  "#7b61ff",
        "TEXT":     "#e8eaf6",
        "TEXT_DIM": "#6b7db3",
        "SUCCESS":  "#00e676",
        "WARN":     "#ff9800",
        "DANGER":   "#ff4444",
    },
    "high_contrast": {
        "BG":       "#000000",
        "PANEL":    "#1a1a1a",
        "CARD":     "#2a2a2a",
        "ACCENT":   "#ffff00",
        "ACCENT2":  "#ff9900",
        "TEXT":     "#ffffff",
        "TEXT_DIM": "#dddddd",
        "SUCCESS":  "#00ff00",
        "WARN":     "#ff9900",
        "DANGER":   "#ff4444",
    },
}


def get_colors(config: dict) -> dict:
    """Return the active theme color palette."""
    key = "high_contrast" if config.get("high_contrast") else "dark"
    return THEMES[key]


# ── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class GestureEvent:
    name: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    hand: str = "right"  # 'left', 'right', 'face'

@dataclass
class AppState:
    running: bool = False
    paused: bool = False
    current_hand_gesture: str = "none"
    current_face_gesture: str = "none"
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    fps: float = 0.0
    gesture_history: deque = field(default_factory=lambda: deque(maxlen=20))
    scroll_mode: bool = False
    scroll_ref_y: float = 0.0


# ── Model Downloader ─────────────────────────────────────────────────────────
def _get_model(filename: str, url: str) -> str:
    """Get the bundled model file, fallback to downloading if running uncompiled."""
    import sys
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    bundled_path = os.path.join(base_path, filename)

    if os.path.exists(bundled_path):
        return bundled_path

    cache_dir = Path.home() / ".gesture_os_models"
    cache_dir.mkdir(exist_ok=True)
    dest = cache_dir / filename
    if not dest.exists():
        import urllib.request
        print(f"[DEBUG] Downloading {filename} to {dest}...")
        try:
            urllib.request.urlretrieve(url, str(dest))
            print(f"[DEBUG] Download complete for {filename}")
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")
    return str(dest)


HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"


# ── Landmark shim ────────────────────────────────────────────────────────────
class _LM:
    """Tiny shim so landmark coords work as lm[i].x / lm[i].y / lm[i].z"""
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


# ── Gesture Recognizer ───────────────────────────────────────────────────────
class HandGestureRecognizer:
    def __init__(self, config: dict):
        self.config = config
        model_path = _get_model("hand_landmarker.task", HAND_MODEL_URL)

        VisionRunningMode = mp.tasks.vision.RunningMode
        HandLandmarker    = mp.tasks.vision.HandLandmarker
        HandOptions       = mp.tasks.vision.HandLandmarkerOptions
        BaseOptions       = mp.tasks.BaseOptions

        options = HandOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=config["detection_confidence"],
            min_hand_presence_confidence=config["detection_confidence"],
            min_tracking_confidence=config["tracking_confidence"],
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._frame_ts   = 0  # millisecond timestamp counter

        self._POINT_COLOR = (0, 229, 255)
        self._LINE_COLOR  = (100, 180, 255)

        self._CONNECTIONS = [
            (0, 1),  (1, 2),  (2, 3),  (3, 4),
            (0, 5),  (5, 6),  (6, 7),  (7, 8),
            (5, 9),  (9, 10), (10, 11),(11, 12),
            (9, 13), (13, 14),(14, 15),(15, 16),
            (13, 17),(17, 18),(18, 19),(19, 20),(0, 17),
        ]

    def _finger_states(self, lm, handedness):
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        extended = []
        if handedness == "Right":
            extended.append(lm[4].x < lm[3].x)
        else:
            extended.append(lm[4].x > lm[3].x)
        for tip, pip in zip(tips[1:], pips[1:]):
            extended.append(lm[tip].y < lm[pip].y)
        return extended

    def _dist(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def recognize(self, lm, handedness="Right"):
        f = self._finger_states(lm, handedness)
        thumb, idx, mid, ring, pinky = f

        pinch_dist = self._dist(lm[4], lm[8])
        if pinch_dist < 0.05:
            return "pinch"
        if pinch_dist < 0.07 and mid and ring and pinky:
            return "ok_sign"
        if not any(f):
            return "fist"
        if all(f):
            return "open_hand"
        if idx and not mid and not ring and not pinky:
            return "index_point"
        if idx and mid and not ring and not pinky:
            return "peace"
        if thumb and not idx and not mid and not ring and not pinky:
            return "thumbs_up"
        if not thumb and not idx and not mid and not ring and not pinky:
            if lm[4].y > lm[9].y:
                return "thumbs_down"
        if thumb and not idx and not mid and not ring and pinky:
            return "call_me"
        return "none"

    def process(self, frame):
        """Returns (landmarks_list, handedness_list) or (None, None)."""
        self._frame_ts += 33
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_img, self._frame_ts)
        if not result.hand_landmarks:
            return None, None
        all_lm = []
        for hand in result.hand_landmarks:
            all_lm.append([_LM(lp.x, lp.y, lp.z) for lp in hand])
        sides = []
        for h_info in result.handedness:
            sides.append(h_info[0].category_name)
        return all_lm, sides

    def draw(self, frame, lm_list, sides):
        if lm_list is None:
            return
        h, w = frame.shape[:2]
        for lm in lm_list:
            pts = [(int(p.x * w), int(p.y * h)) for p in lm]
            for a, b in self._CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], self._LINE_COLOR, 1, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 4, self._POINT_COLOR, -1, cv2.LINE_AA)


class FaceGestureRecognizer:
    def __init__(self, config: dict):
        self.config = config
        model_path = _get_model("face_landmarker.task", FACE_MODEL_URL)

        VisionRunningMode = mp.tasks.vision.RunningMode
        FaceLandmarker    = mp.tasks.vision.FaceLandmarker
        FaceOptions       = mp.tasks.vision.FaceLandmarkerOptions
        BaseOptions       = mp.tasks.BaseOptions

        options = FaceOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=config["face_detection_confidence"],
            min_face_presence_confidence=config["face_detection_confidence"],
            min_tracking_confidence=config["tracking_confidence"],
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)
        self._frame_ts   = 0

        self._brow_hist      = deque(maxlen=6)
        self._mouth_hist     = deque(maxlen=6)
        self._left_eye_hist  = deque(maxlen=8)
        self._right_eye_hist = deque(maxlen=8)
        self._smile_hist     = deque(maxlen=8)

        self._CONTOUR_COLOR = (80, 200, 120)

        self._FACE_OVAL = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
            397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
            172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10,
        ]

    def _dist(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def _ear(self, lm, eye_indices):
        h  = self._dist(lm[eye_indices[0]], lm[eye_indices[3]])
        v1 = self._dist(lm[eye_indices[1]], lm[eye_indices[5]])
        v2 = self._dist(lm[eye_indices[2]], lm[eye_indices[4]])
        return (v1 + v2) / (2.0 * h) if h else 0

    def recognize(self, lm):
        gestures = []

        left_brow    = lm[105].y
        left_eye_top = lm[159].y
        self._brow_hist.append(left_eye_top - left_brow)
        if len(self._brow_hist) == self._brow_hist.maxlen:
            if sum(self._brow_hist) / len(self._brow_hist) > 0.065:
                gestures.append("brow_raise")

        mouth_open = abs(lm[13].y - lm[14].y)
        self._mouth_hist.append(mouth_open)
        if len(self._mouth_hist) == self._mouth_hist.maxlen:
            if sum(self._mouth_hist) / len(self._mouth_hist) > 0.035:
                gestures.append("mouth_open")

        mw = abs(lm[61].x - lm[291].x)
        mh = abs(lm[61].y - lm[291].y)
        self._smile_hist.append(mw / (mh + 1e-6))
        if len(self._smile_hist) == self._smile_hist.maxlen:
            if sum(self._smile_hist) / len(self._smile_hist) > 3.5 and "mouth_open" not in gestures:
                gestures.append("smile")

        left_ear  = self._ear(lm, [33,  160, 158, 133, 153, 144])
        right_ear = self._ear(lm, [362, 385, 387, 263, 373, 380])
        self._left_eye_hist.append(left_ear)
        self._right_eye_hist.append(right_ear)

        if len(self._left_eye_hist) >= 4:
            if left_ear < 0.18 and sum(self._left_eye_hist) / len(self._left_eye_hist) > 0.22:
                gestures.append("blink_left")
        if len(self._right_eye_hist) >= 4:
            if right_ear < 0.18 and sum(self._right_eye_hist) / len(self._right_eye_hist) > 0.22:
                gestures.append("blink_right")
        if left_ear < 0.22 and right_ear < 0.22 and "blink_left" not in gestures:
            gestures.append("squint")

        return gestures[0] if gestures else "none"

    def process(self, frame):
        """Returns landmark list (shims) or None."""
        self._frame_ts += 33
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_img, self._frame_ts)
        if not result.face_landmarks:
            return None
        return [_LM(lp.x, lp.y, lp.z) for lp in result.face_landmarks[0]]

    def draw(self, frame, lm):
        if lm is None:
            return
        h, w = frame.shape[:2]
        pts = [None] * len(lm)
        for i, p in enumerate(lm):
            pts[i] = (int(p.x * w), int(p.y * h))
        for i in range(len(self._FACE_OVAL) - 1):
            a, b = self._FACE_OVAL[i], self._FACE_OVAL[i + 1]
            if a < len(pts) and b < len(pts):
                cv2.line(frame, pts[a], pts[b], self._CONTOUR_COLOR, 1, cv2.LINE_AA)


# ── Action Executor ──────────────────────────────────────────────────────────
class ActionExecutor:
    def __init__(self, config: dict):
        self.config = config
        self._last_action_time: dict = {}

    def _cooldown_ok(self, action: str) -> bool:
        now  = time.time() * 1000
        last = self._last_action_time.get(action, 0)
        if now - last >= self.config["gesture_cooldown_ms"]:
            self._last_action_time[action] = now
            return True
        return False

    def execute(self, action: str, extra=None):
        if not self._cooldown_ok(action):
            return
        try:
            if action == "left_click":
                pyautogui.click()
            elif action == "double_click":
                pyautogui.doubleClick()
            elif action == "right_click":
                pyautogui.rightClick()
            elif action == "middle_click":
                pyautogui.middleClick()
            elif action == "screenshot":
                pyautogui.screenshot(
                    str(Path.home() / "Desktop" / f"gesture_shot_{int(time.time())}.png")
                )
            elif action == "volume_up":
                pyautogui.press("volumeup")
            elif action == "volume_down":
                pyautogui.press("volumedown")
            elif action == "media_play_pause":
                pyautogui.press("playpause")
            elif action == "switch_window":
                pyautogui.hotkey("alt", "tab")
            elif action == "back":
                pyautogui.hotkey("alt", "left")
            elif action == "forward":
                pyautogui.hotkey("alt", "right")
            elif action == "zoom_in":
                pyautogui.hotkey("ctrl", "=")
            elif action == "zoom_out":
                pyautogui.hotkey("ctrl", "-")
            elif action == "fullscreen":
                pyautogui.press("f11")
            elif action == "scroll_up":
                pyautogui.scroll(self.config["scroll_speed"])
            elif action == "scroll_down":
                pyautogui.scroll(-self.config["scroll_speed"])
            elif action == "copy":
                pyautogui.hotkey("ctrl", "c")
            elif action == "paste":
                pyautogui.hotkey("ctrl", "v")
            elif action == "undo":
                pyautogui.hotkey("ctrl", "z")
        except Exception as e:
            print(f"[ActionExecutor] Error: {e}")


# ── Cursor Smoother ──────────────────────────────────────────────────────────
class CursorSmoother:
    def __init__(self, factor: int = 7):
        self.history_x = deque(maxlen=factor)
        self.history_y = deque(maxlen=factor)

    def smooth(self, x: float, y: float):
        self.history_x.append(x)
        self.history_y.append(y)
        return (
            int(sum(self.history_x) / len(self.history_x)),
            int(sum(self.history_y) / len(self.history_y)),
        )


# ── Main Engine ──────────────────────────────────────────────────────────────
class GestureEngine:
    def __init__(self, config: dict, state: AppState, log_cb: Callable = None):
        self.config   = config
        self.state    = state
        self.log_cb   = log_cb or (lambda msg: None)
        self.hand_rec = HandGestureRecognizer(config)
        self.face_rec = FaceGestureRecognizer(config)
        self.executor = ActionExecutor(config)
        self.smoother = CursorSmoother(config["smoothing_factor"])
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture]    = None
        self._preview_frame = None
        self._preview_lock  = threading.Lock()

        sw, sh = pyautogui.size()
        self.screen_w = sw
        self.screen_h = sh

        self._last_gesture_time = 0.0
        self._prev_hand_gesture = "none"
        self._prev_face_gesture = "none"

    def get_preview_frame(self):
        with self._preview_lock:
            return self._preview_frame.copy() if self._preview_frame is not None else None

    def start(self):
        if self.state.running:
            return
        self.state.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log_cb("Engine started ✓")

    def stop(self):
        self.state.running = False
        if self._cap:
            self._cap.release()
        self.log_cb("Engine stopped.")

    def _map_cursor(self, nx: float, ny: float):
        sens = self.config["cursor_sensitivity"]
        half = 0.5 / sens
        lo, hi = 0.5 - half, 0.5 + half
        rx = np.clip((nx - lo) / (hi - lo), 0.0, 1.0)
        ry = np.clip((ny - lo) / (hi - lo), 0.0, 1.0)
        return int(rx * self.screen_w), int(ry * self.screen_h)

    def _dispatch(self, gesture: str, hand: str = "hand"):
        bindings = self.config["gesture_bindings"]
        action   = bindings.get(gesture, "none")
        self.state.gesture_history.appendleft(
            f"[{hand.upper()}] {gesture} → {action}"
        )
        self.log_cb(f"Gesture: {gesture} → {action}")
        if action and action not in ("move_cursor", "none", "scroll_mode"):
            self.executor.execute(action)

    def _loop(self):
        import platform
        idx = self.config["camera_index"]
        if platform.system() == "Windows":
            self._cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(idx)

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        if not self._cap.isOpened():
            self.log_cb("ERROR: Cannot open camera! Check index in Advanced settings.")
            self.state.running = False
            return

        fps_timer   = time.time()
        frame_count = 0

        while self.state.running:
            ret, frame = self._cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame_count += 1

            now = time.time()
            if now - fps_timer >= 1.0:
                self.state.fps = frame_count / (now - fps_timer)
                frame_count    = 0
                fps_timer      = now

            if self.state.paused:
                self._overlay_paused(frame)
                with self._preview_lock:
                    self._preview_frame = frame
                continue

            # ── Hand processing ──────────────────────────────
            hand_gesture = "none"
            if self.config["enable_hand_gestures"]:
                lm_list, sides = self.hand_rec.process(frame)
                if self.config["show_landmarks"]:
                    self.hand_rec.draw(frame, lm_list, sides)

                if lm_list:
                    lm   = lm_list[0]
                    side = sides[0] if sides else "Right"
                    hand_gesture = self.hand_rec.recognize(lm, side)

                    if hand_gesture == "index_point":
                        nx, ny = lm[8].x, lm[8].y
                        sx, sy = self._map_cursor(nx, ny)
                        sx, sy = self.smoother.smooth(sx, sy)
                        pyautogui.moveTo(sx, sy, _pause=False)
                        self.state.cursor_x = sx
                        self.state.cursor_y = sy

                    elif hand_gesture == "open_hand":
                        if not self.state.scroll_mode:
                            self.state.scroll_mode  = True
                            self.state.scroll_ref_y = lm[9].y
                        else:
                            dy = lm[9].y - self.state.scroll_ref_y
                            if abs(dy) > 0.03:
                                self.executor.execute("scroll_down" if dy > 0 else "scroll_up")
                    else:
                        self.state.scroll_mode = False

                    if hand_gesture != "none" and hand_gesture != self._prev_hand_gesture:
                        self._dispatch(hand_gesture, "hand")
                    self._prev_hand_gesture = hand_gesture
                else:
                    self._prev_hand_gesture = "none"
                    self.state.scroll_mode  = False

            # ── Face processing ──────────────────────────────
            face_gesture = "none"
            if self.config["enable_face_gestures"]:
                lm_face = self.face_rec.process(frame)
                if self.config["show_landmarks"]:
                    self.face_rec.draw(frame, lm_face)

                if lm_face:
                    face_gesture = self.face_rec.recognize(lm_face)
                    if face_gesture != self._prev_face_gesture and face_gesture != "none":
                        self._dispatch(face_gesture, "face")
                    self._prev_face_gesture = face_gesture
                else:
                    self._prev_face_gesture = "none"

            self.state.current_hand_gesture = hand_gesture
            self.state.current_face_gesture = face_gesture

            self._draw_overlay(frame, hand_gesture, face_gesture)

            with self._preview_lock:
                self._preview_frame = frame

        self._cap.release()

    def _draw_overlay(self, frame, hand_g, face_g):
        h, w = frame.shape[:2]
        cfg  = self.config

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 80), (w, h), (10, 10, 20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        accent = (0, 229, 255)

        if cfg["show_gesture_label"]:
            label = f"Hand: {hand_g}  |  Face: {face_g}"
            cv2.putText(frame, label, (20, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, accent, 2, cv2.LINE_AA)

        if cfg["show_fps"]:
            cv2.putText(frame, f"{self.state.fps:.1f} FPS",
                        (w - 110, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 255, 180), 2, cv2.LINE_AA)

        if cfg["show_debug_overlay"]:
            cv2.putText(frame,
                        f"Cursor: ({int(self.state.cursor_x)}, {int(self.state.cursor_y)})",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            cv2.putText(frame, f"Scroll Mode: {self.state.scroll_mode}",
                        (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        if hand_g != "none" and hand_g != "index_point":
            cv2.putText(frame, f"◉ {hand_g.upper()}", (20, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, accent, 2, cv2.LINE_AA)

    def _overlay_paused(self, frame):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.putText(frame, "PAUSED", (w // 2 - 80, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 229, 255), 4, cv2.LINE_AA)


# ── Config Manager ───────────────────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                stored = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(stored)
            cfg["gesture_bindings"] = {
                **DEFAULT_CONFIG["gesture_bindings"],
                **stored.get("gesture_bindings", {}),
            }
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


# ── GUI ──────────────────────────────────────────────────────────────────────
class GestureOSApp:
    def __init__(self, root: tk.Tk):
        self.root   = root
        self.config = load_config()
        self.state  = AppState()
        self.engine: Optional[GestureEngine] = None
        self._log_lines = []

        # Derive initial theme colors
        self._colors = get_colors(self.config)

        self._setup_root()
        self._build_ui()
        self._start_ui_refresh()

    # ── Colors shortcut properties ────────────────────────────
    @property
    def C(self) -> dict:
        """Return current color palette (updated on theme toggle)."""
        return self._colors

    # ── Root Setup ────────────────────────────────────────────
    def _setup_root(self):
        self.root.title("GestureOS — Webcam PC Control")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        self.root.configure(bg=self.C["BG"])

        # App icon (PyInstaller / Nuitka compatible)
        try:
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                print(f"Could not find internal icon at: {icon_path}")
        except Exception as e:
            print(f"Icon Load Failed: {e}")

        # ttk Styles
        style = ttk.Style()
        style.theme_use("clam")
        self._apply_ttk_style(style)

    def _apply_ttk_style(self, style: ttk.Style = None):
        """Apply (or re-apply) ttk styles using the current color palette."""
        if style is None:
            style = ttk.Style()
        C = self.C
        style.configure(".",
                         background=C["BG"], foreground=C["TEXT"],
                         fieldbackground=C["CARD"], troughcolor=C["CARD"],
                         bordercolor=C["CARD"], relief="flat")
        style.configure("TNotebook", background=C["BG"], borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=C["CARD"], foreground=C["TEXT_DIM"],
                         padding=[16, 8], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", C["PANEL"])],
                  foreground=[("selected", C["ACCENT"])])
        style.configure("TFrame", background=C["BG"])
        style.configure("TLabelframe",
                         background=C["PANEL"], foreground=C["ACCENT"],
                         bordercolor=C["CARD"], relief="groove", borderwidth=1)
        style.configure("TLabelframe.Label",
                         background=C["PANEL"], foreground=C["ACCENT"],
                         font=("Consolas", 9, "bold"))
        style.configure("TScrollbar",
                         background=C["CARD"], troughcolor=C["BG"],
                         arrowcolor=C["TEXT_DIM"], borderwidth=0)
        style.configure("Horizontal.TProgressbar",
                         background=C["ACCENT"], troughcolor=C["CARD"])
        style.configure("TCombobox",
                         selectbackground=C["CARD"], selectforeground=C["TEXT"])
        style.configure("TCheckbutton", background=C["PANEL"], foreground=C["TEXT"])
        style.map("TCheckbutton", background=[("active", C["PANEL"])])
        style.configure("TScale", background=C["PANEL"], troughcolor=C["CARD"])

    # ── Font helpers ──────────────────────────────────────────
    def _fs(self, delta: int = 0) -> int:
        """Return current font size + delta."""
        return int(self.config.get("font_size", 10)) + delta

    def _font(self, family: str = "Segoe UI", delta: int = 0, bold: bool = False) -> tuple:
        style = "bold" if bold else "normal"
        return (family, self._fs(delta), style)

    def _mono(self, delta: int = 0, bold: bool = False) -> tuple:
        return self._font("Consolas", delta, bold)

    # ── Widget factories ──────────────────────────────────────
    def _btn(self, parent, text, cmd, color=None, width=14, font_size_delta=0):
        C = self.C
        if color is None:
            color = C["ACCENT"]
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=C["CARD"], fg=color,
            activebackground=color, activeforeground=C["BG"],
            relief="flat", bd=0,
            font=self._mono(font_size_delta, bold=True),
            width=width, cursor="hand2", padx=8, pady=6,
        )
        b.bind("<Enter>", lambda e: b.configure(bg=color, fg=C["BG"]))
        b.bind("<Leave>", lambda e: b.configure(bg=C["CARD"], fg=color))
        return b

    def _label(self, parent, text, fg=None, delta=0, bold=False, bg=None):
        C = self.C
        return tk.Label(
            parent, text=text,
            fg=fg or C["TEXT"],
            bg=bg or C["BG"],
            font=self._font(delta=delta, bold=bold),
        )

    # ── UI Build ──────────────────────────────────────────────
    def _build_ui(self):
        C = self.C

        # ── Header ────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=C["PANEL"], height=64)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="◈ GestureOS", fg=C["ACCENT"], bg=C["PANEL"],
                 font=self._mono(delta=8, bold=True)).pack(side="left", padx=20, pady=14)
        tk.Label(hdr, text="Webcam Gesture Control", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._font()).pack(side="left", pady=18)

        # High-Contrast toggle button (always visible in header)
        self._hc_btn = tk.Button(
            hdr,
            text="◑ High Contrast",
            command=self._toggle_high_contrast,
            bg=C["CARD"], fg=C["ACCENT2"],
            activebackground=C["ACCENT2"], activeforeground=C["BG"],
            relief="flat", bd=0,
            font=self._mono(bold=True),
            cursor="hand2", padx=10, pady=6,
        )
        self._hc_btn.pack(side="right", padx=10, pady=12)
        self._hc_btn.bind("<Enter>",
                          lambda e: self._hc_btn.configure(bg=C["ACCENT2"], fg=C["BG"]))
        self._hc_btn.bind("<Leave>",
                          lambda e: self._hc_btn.configure(bg=C["CARD"], fg=C["ACCENT2"]))

        # Status pill
        self.status_var = tk.StringVar(value="● IDLE")
        self.status_lbl = tk.Label(
            hdr, textvariable=self.status_var,
            fg=C["TEXT_DIM"], bg=C["PANEL"],
            font=self._mono(bold=True),
        )
        self.status_lbl.pack(side="right", padx=12)

        # ── Main Layout ───────────────────────────────────────
        main = tk.Frame(self.root, bg=C["BG"])
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=C["PANEL"], width=220)
        left.pack(side="left", fill="y", padx=(8, 0), pady=8)
        left.pack_propagate(False)
        self._build_sidebar(left)

        right = tk.Frame(main, bg=C["BG"])
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self._build_tabs(right)

        # ── Status Bar ────────────────────────────────────────
        sbar = tk.Frame(self.root, bg=C["CARD"], height=28)
        sbar.pack(fill="x", side="bottom")
        sbar.pack_propagate(False)

        self.fps_var = tk.StringVar(value="FPS: —")
        tk.Label(sbar, textvariable=self.fps_var, fg=C["TEXT_DIM"], bg=C["CARD"],
                 font=self._mono(delta=-2)).pack(side="left", padx=12, pady=4)

        self.cpu_var = tk.StringVar(value="CPU: —%")
        tk.Label(sbar, textvariable=self.cpu_var, fg=C["TEXT_DIM"], bg=C["CARD"],
                 font=self._mono(delta=-2)).pack(side="left", padx=12)

        self.hand_var = tk.StringVar(value="Hand: —")
        tk.Label(sbar, textvariable=self.hand_var, fg=C["ACCENT"], bg=C["CARD"],
                 font=self._mono(delta=-2, bold=True)).pack(side="left", padx=12)

        self.face_var = tk.StringVar(value="Face: —")
        tk.Label(sbar, textvariable=self.face_var, fg=C["ACCENT2"], bg=C["CARD"],
                 font=self._mono(delta=-2, bold=True)).pack(side="left", padx=12)

    def _build_sidebar(self, parent):
        C = self.C

        tk.Label(parent, text="CONTROLS", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._mono(delta=-2, bold=True)).pack(pady=(18, 6), padx=12, anchor="w")

        self._btn(parent, "▶  START ENGINE", self._start, C["SUCCESS"], width=22).pack(
            padx=12, pady=4, fill="x")
        self._btn(parent, "■  STOP", self._stop, C["DANGER"], width=22).pack(
            padx=12, pady=4, fill="x")
        self._btn(parent, "⏸  PAUSE / RESUME", self._pause, C["WARN"], width=22).pack(
            padx=12, pady=4, fill="x")

        tk.Frame(parent, bg=C["CARD"], height=1).pack(fill="x", padx=12, pady=10)

        # Quick toggles
        tk.Label(parent, text="QUICK SETTINGS", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._mono(delta=-2, bold=True)).pack(padx=12, anchor="w", pady=(4, 6))

        self._hand_var      = tk.BooleanVar(value=self.config["enable_hand_gestures"])
        self._face_var      = tk.BooleanVar(value=self.config["enable_face_gestures"])
        self._landmarks_var = tk.BooleanVar(value=self.config["show_landmarks"])
        self._debug_var     = tk.BooleanVar(value=self.config["show_debug_overlay"])

        for label, var, key in [
            ("Hand Gestures",  self._hand_var,      "enable_hand_gestures"),
            ("Face Gestures",  self._face_var,      "enable_face_gestures"),
            ("Show Landmarks", self._landmarks_var, "show_landmarks"),
            ("Debug Overlay",  self._debug_var,     "show_debug_overlay"),
        ]:
            f = tk.Frame(parent, bg=C["PANEL"])
            f.pack(fill="x", padx=12, pady=2)
            tk.Checkbutton(
                f, text=label, variable=var,
                bg=C["PANEL"], fg=C["TEXT"],
                selectcolor=C["CARD"],
                activebackground=C["PANEL"], activeforeground=C["ACCENT"],
                font=self._font(),
                command=lambda k=key, v=var: self._quick_toggle(k, v),
            ).pack(side="left")

        tk.Frame(parent, bg=C["CARD"], height=1).pack(fill="x", padx=12, pady=10)

        # Cursor sensitivity slider
        tk.Label(parent, text="CURSOR SENSITIVITY", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._mono(delta=-2, bold=True)).pack(padx=12, anchor="w")
        self._sens_var = tk.DoubleVar(value=self.config["cursor_sensitivity"])
        tk.Scale(
            parent, from_=0.5, to=3.0, resolution=0.1,
            orient="horizontal", variable=self._sens_var,
            bg=C["PANEL"], fg=C["TEXT"], troughcolor=C["CARD"],
            highlightthickness=0, sliderrelief="flat",
            command=lambda v: self._update_config("cursor_sensitivity", float(v)),
        ).pack(padx=12, fill="x")

        tk.Frame(parent, bg=C["CARD"], height=1).pack(fill="x", padx=12, pady=10)

        # ── Font Size Slider ───────────────────────────────────
        tk.Label(parent, text="UI FONT SIZE", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._mono(delta=-2, bold=True)).pack(padx=12, anchor="w")

        self._font_size_var = tk.IntVar(value=self.config.get("font_size", 10))
        font_row = tk.Frame(parent, bg=C["PANEL"])
        font_row.pack(fill="x", padx=12, pady=(0, 4))

        tk.Label(font_row, text="A", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Scale(
            font_row, from_=8, to=16, resolution=1,
            orient="horizontal", variable=self._font_size_var,
            bg=C["PANEL"], fg=C["TEXT"], troughcolor=C["CARD"],
            highlightthickness=0, sliderrelief="flat",
            command=self._on_font_size_change,
        ).pack(side="left", fill="x", expand=True)
        tk.Label(font_row, text="A", fg=C["TEXT"], bg=C["PANEL"],
                 font=("Segoe UI", 14)).pack(side="left")

        tk.Frame(parent, bg=C["CARD"], height=1).pack(fill="x", padx=12, pady=10)

        self._btn(parent, "💾  Save Config", self._save_config, C["ACCENT2"], width=22).pack(
            padx=12, pady=4, fill="x")
        self._btn(parent, "↺  Reset Defaults", self._reset_defaults, C["TEXT_DIM"], width=22).pack(
            padx=12, pady=4, fill="x")

    def _build_tabs(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tabs = {}
        for name in ["Preview", "Gestures", "Bindings", "Advanced", "Log"]:
            f = tk.Frame(nb, bg=self.C["BG"])
            nb.add(f, text=f"  {name}  ")
            tabs[name] = f

        self._build_preview_tab(tabs["Preview"])
        self._build_gestures_tab(tabs["Gestures"])
        self._build_bindings_tab(tabs["Bindings"])
        self._build_advanced_tab(tabs["Advanced"])
        self._build_log_tab(tabs["Log"])

    # ── Preview Tab ───────────────────────────────────────────
    def _build_preview_tab(self, parent):
        C = self.C
        parent.configure(bg=C["BG"])

        info = tk.Frame(parent, bg=C["BG"])
        info.pack(fill="x", padx=8, pady=4)
        tk.Label(info, text="Live Camera Preview  (updates while engine runs)",
                 fg=C["TEXT_DIM"], bg=C["BG"], font=self._font()).pack(side="left")

        self.preview_label = tk.Label(
            parent, bg="#000000",
            text="Engine not running\nPress START to begin",
            fg=C["TEXT_DIM"], font=self._mono(delta=2),
        )
        self.preview_label.pack(fill="both", expand=True, padx=8, pady=4)

    # ── Gestures Tab ─────────────────────────────────────────
    def _build_gestures_tab(self, parent):
        C = self.C
        canvas = tk.Canvas(parent, bg=C["BG"], highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        frame = tk.Frame(canvas, bg=C["BG"])
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Live gesture display
        card = tk.LabelFrame(frame, text=" LIVE DETECTION ",
                              bg=C["PANEL"], fg=C["ACCENT"],
                              font=self._mono(bold=True), relief="groove", bd=1)
        card.pack(fill="x", padx=16, pady=12)

        f1 = tk.Frame(card, bg=C["PANEL"])
        f1.pack(fill="x", padx=12, pady=8)

        tk.Label(f1, text="Hand:", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._font()).grid(row=0, column=0, sticky="w", padx=4)
        self.live_hand_lbl = tk.Label(f1, text="—", fg=C["ACCENT"], bg=C["PANEL"],
                                      font=self._mono(delta=4, bold=True))
        self.live_hand_lbl.grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(f1, text="Face:", fg=C["TEXT_DIM"], bg=C["PANEL"],
                 font=self._font()).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.live_face_lbl = tk.Label(f1, text="—", fg=C["ACCENT2"], bg=C["PANEL"],
                                      font=self._mono(delta=4, bold=True))
        self.live_face_lbl.grid(row=1, column=1, sticky="w", padx=8)

        # History
        hist_card = tk.LabelFrame(frame, text=" GESTURE HISTORY ",
                                  bg=C["PANEL"], fg=C["ACCENT"],
                                  font=self._mono(bold=True), relief="groove", bd=1)
        hist_card.pack(fill="x", padx=16, pady=8)

        self.hist_text = tk.Text(
            hist_card, height=10, bg=C["CARD"], fg=C["TEXT"],
            font=self._mono(), relief="flat", bd=0,
            state="disabled", cursor="arrow",
        )
        self.hist_text.pack(fill="x", padx=8, pady=8)

        # Reference card
        ref_card = tk.LabelFrame(frame, text=" GESTURE REFERENCE ",
                                 bg=C["PANEL"], fg=C["ACCENT2"],
                                 font=self._mono(bold=True), relief="groove", bd=1)
        ref_card.pack(fill="x", padx=16, pady=8, ipadx=8, ipady=8)

        gestures = [
            ("✋ Hand Gestures", [
                ("index_point",  "Move cursor — point with index finger"),
                ("pinch",        "Left click — touch thumb to index"),
                ("double_pinch", "Double click — quick double pinch"),
                ("fist",         "Right click — close all fingers"),
                ("open_hand",    "Scroll mode — open palm, move up/down"),
                ("peace",        "Screenshot — index + middle extended"),
                ("thumbs_up",    "Volume up"),
                ("thumbs_down",  "Volume down"),
                ("call_me",      "Play/pause — thumb + pinky extended"),
                ("ok_sign",      "Middle click — thumb + index circle"),
            ]),
            ("😊 Face Gestures", [
                ("brow_raise",  "Alt+Tab (switch window)"),
                ("blink_left",  "Browser back"),
                ("blink_right", "Browser forward"),
                ("mouth_open",  "Zoom in (Ctrl+=)"),
                ("smile",       "Zoom out (Ctrl+-)"),
                ("squint",      "Fullscreen (F11)"),
            ]),
        ]

        for section, items in gestures:
            tk.Label(ref_card, text=section, fg=C["ACCENT"], bg=C["PANEL"],
                     font=self._font(bold=True)).pack(anchor="w", padx=12, pady=(8, 4))
            for name, desc in items:
                row = tk.Frame(ref_card, bg=C["PANEL"])
                row.pack(fill="x", padx=20, pady=2)
                tk.Label(row, text=f"  {name}", fg=C["ACCENT"], bg=C["PANEL"],
                         font=self._mono(bold=True), width=18, anchor="w").pack(side="left")
                tk.Label(row, text=desc, fg=C["TEXT_DIM"], bg=C["PANEL"],
                         font=self._font()).pack(side="left")

    # ── Bindings Tab ─────────────────────────────────────────
    def _build_bindings_tab(self, parent):
        C = self.C
        tk.Label(parent, text="Customize what each gesture does:",
                 fg=C["TEXT_DIM"], bg=C["BG"], font=self._font()).pack(
            pady=(12, 6), padx=16, anchor="w")

        canvas = tk.Canvas(parent, bg=C["BG"], highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        frame = tk.Frame(canvas, bg=C["BG"])
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        actions = [
            "move_cursor", "left_click", "double_click", "right_click", "middle_click",
            "scroll_mode", "screenshot", "volume_up", "volume_down", "media_play_pause",
            "switch_window", "back", "forward", "zoom_in", "zoom_out", "fullscreen",
            "copy", "paste", "undo", "none",
        ]

        self._binding_vars = {}
        bindings = self.config["gesture_bindings"]

        for gesture, action in bindings.items():
            row = tk.Frame(frame, bg=C["PANEL"], relief="flat")
            row.pack(fill="x", padx=16, pady=3, ipady=4)

            tk.Label(row, text=gesture, fg=C["ACCENT"], bg=C["PANEL"],
                     font=self._mono(bold=True), width=20, anchor="w").pack(side="left", padx=12)

            var = tk.StringVar(value=action)
            self._binding_vars[gesture] = var
            cb = ttk.Combobox(row, textvariable=var, values=actions,
                              width=22, state="readonly", font=self._font())
            cb.pack(side="left", padx=4)
            cb.bind("<<ComboboxSelected>>",
                    lambda e, g=gesture, v=var: self._update_binding(g, v.get()))

        self._btn(frame, "💾  Apply Bindings", self._save_config, C["ACCENT"], width=22).pack(
            pady=12, padx=16, anchor="w")

    # ── Advanced Tab ─────────────────────────────────────────
    def _build_advanced_tab(self, parent):
        C = self.C
        canvas = tk.Canvas(parent, bg=C["BG"], highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        frame = tk.Frame(canvas, bg=C["BG"])
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def section(title):
            return tk.LabelFrame(
                frame, text=f" {title} ",
                bg=C["PANEL"], fg=C["ACCENT"],
                font=self._mono(bold=True), relief="groove", bd=1,
            )

        def slider_row(parent, label, key, from_, to, resolution=1):
            r = tk.Frame(parent, bg=C["PANEL"])
            r.pack(fill="x", padx=8, pady=4)
            tk.Label(r, text=label, fg=C["TEXT"], bg=C["PANEL"],
                     font=self._font(), width=28, anchor="w").pack(side="left")
            var = tk.DoubleVar(value=self.config[key])
            tk.Scale(
                r, from_=from_, to=to, resolution=resolution,
                orient="horizontal", variable=var,
                bg=C["PANEL"], fg=C["TEXT"], troughcolor=C["CARD"],
                highlightthickness=0, sliderrelief="flat", length=180,
                command=lambda v, k=key: self._update_config(k, float(v)),
            ).pack(side="left", padx=8)

        # Camera
        cam = section("CAMERA")
        cam.pack(fill="x", padx=16, pady=8, ipadx=8, ipady=8)
        r = tk.Frame(cam, bg=C["PANEL"])
        r.pack(fill="x", padx=8, pady=4)
        tk.Label(r, text="Camera Index", fg=C["TEXT"], bg=C["PANEL"],
                 font=self._font(), width=28, anchor="w").pack(side="left")
        self._cam_idx_var = tk.IntVar(value=self.config["camera_index"])
        for i in range(4):
            tk.Radiobutton(
                r, text=str(i), variable=self._cam_idx_var, value=i,
                bg=C["PANEL"], fg=C["TEXT"], selectcolor=C["CARD"],
                activebackground=C["PANEL"],
                command=lambda: self._update_config("camera_index", self._cam_idx_var.get()),
            ).pack(side="left", padx=6)

        # Detection
        det = section("DETECTION CONFIDENCE")
        det.pack(fill="x", padx=16, pady=8, ipadx=8, ipady=8)
        slider_row(det, "Detection Confidence",      "detection_confidence",      0.3, 1.0, 0.05)
        slider_row(det, "Tracking Confidence",       "tracking_confidence",       0.3, 1.0, 0.05)
        slider_row(det, "Face Detection Confidence", "face_detection_confidence", 0.3, 1.0, 0.05)

        # Performance
        perf = section("PERFORMANCE")
        perf.pack(fill="x", padx=16, pady=8, ipadx=8, ipady=8)
        slider_row(perf, "Smoothing Factor (frames)", "smoothing_factor",    1,   20,   1)
        slider_row(perf, "Gesture Cooldown (ms)",     "gesture_cooldown_ms", 100, 2000, 50)
        slider_row(perf, "Scroll Speed",              "scroll_speed",        1,   15,   1)
        slider_row(perf, "Cursor Sensitivity",        "cursor_sensitivity",  0.5, 3.0,  0.1)

        # Display
        disp = section("DISPLAY")
        disp.pack(fill="x", padx=16, pady=8, ipadx=8, ipady=8)
        bools = [
            ("show_landmarks",    "Show Hand/Face Landmarks"),
            ("show_fps",          "Show FPS Counter"),
            ("show_gesture_label","Show Gesture Labels"),
            ("show_debug_overlay","Show Debug Overlay"),
        ]
        for key, label in bools:
            v = tk.BooleanVar(value=self.config[key])
            tk.Checkbutton(
                disp, text=label, variable=v,
                bg=C["PANEL"], fg=C["TEXT"], selectcolor=C["CARD"],
                activebackground=C["PANEL"], activeforeground=C["ACCENT"],
                font=self._font(),
                command=lambda k=key, vr=v: self._update_config(k, vr.get()),
            ).pack(anchor="w", padx=8, pady=2)

    # ── Log Tab ───────────────────────────────────────────────
    def _build_log_tab(self, parent):
        C = self.C
        f = tk.Frame(parent, bg=C["BG"])
        f.pack(fill="both", expand=True)

        ctrl = tk.Frame(f, bg=C["BG"])
        ctrl.pack(fill="x", padx=8, pady=4)
        self._btn(ctrl, "Clear Log", self._clear_log, C["TEXT_DIM"], width=12).pack(side="right")

        self.log_text = tk.Text(
            f, bg=C["CARD"], fg=C["TEXT"],
            font=self._mono(), relief="flat", bd=0,
            state="disabled", wrap="word",
        )
        sb = ttk.Scrollbar(f, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.log_text.tag_configure("info",   foreground=C["TEXT"])
        self.log_text.tag_configure("accent", foreground=C["ACCENT"])
        self.log_text.tag_configure("warn",   foreground=C["WARN"])
        self.log_text.tag_configure("error",  foreground=C["DANGER"])

    # ── Actions ───────────────────────────────────────────────
    def _start(self):
        if self.state.running:
            self._log("Engine already running", "warn")
            return
        self.engine = GestureEngine(self.config, self.state, self._log)
        self.engine.start()
        self.status_var.set("● RUNNING")
        self.status_lbl.configure(fg=self.C["SUCCESS"])

    def _stop(self):
        if self.engine:
            self.engine.stop()
        self.state.running = False
        self.state.paused  = False
        self.status_var.set("● STOPPED")
        self.status_lbl.configure(fg=self.C["DANGER"])
        self.preview_label.configure(image="",
                                     text="Engine stopped\nPress START to begin")

    def _pause(self):
        if not self.state.running:
            return
        self.state.paused = not self.state.paused
        if self.state.paused:
            self.status_var.set("⏸ PAUSED")
            self.status_lbl.configure(fg=self.C["WARN"])
        else:
            self.status_var.set("● RUNNING")
            self.status_lbl.configure(fg=self.C["SUCCESS"])

    def _quick_toggle(self, key, var):
        self.config[key] = var.get()
        if self.engine:
            self.engine.config[key] = var.get()

    def _update_config(self, key, value):
        self.config[key] = value
        if self.engine:
            self.engine.config[key] = value

    def _update_binding(self, gesture, action):
        self.config["gesture_bindings"][gesture] = action
        if self.engine:
            self.engine.config["gesture_bindings"][gesture] = action

    def _save_config(self):
        for gesture, var in self._binding_vars.items():
            self.config["gesture_bindings"][gesture] = var.get()
        save_config(self.config)
        self._log("Configuration saved ✓", "accent")

    def _reset_defaults(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.config = DEFAULT_CONFIG.copy()
            save_config(self.config)
            self._log("Reset to defaults.", "warn")
            messagebox.showinfo("Reset", "Please restart GestureOS to apply defaults.")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _log(self, msg: str, tag: str = "info"):
        ts   = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ── Font Size Adjustment ──────────────────────────────────
    def _on_font_size_change(self, value):
        """Called when the font-size slider moves. Persists + rebuilds the UI."""
        new_size = int(float(value))
        if new_size == self.config.get("font_size", 10):
            return
        self._update_config("font_size", new_size)
        self._rebuild_ui()

    # ── High-Contrast Toggle ──────────────────────────────────
    def _toggle_high_contrast(self):
        """Switch between dark and high-contrast theme, then rebuild UI."""
        self.config["high_contrast"] = not self.config.get("high_contrast", False)
        self._colors = get_colors(self.config)
        self._apply_ttk_style()
        self._rebuild_ui()
        self._log(
            f"High contrast {'ON' if self.config['high_contrast'] else 'OFF'}", "accent"
        )

    # ── Full UI Rebuild (theme / font change) ─────────────────
    def _rebuild_ui(self):
        """Tear down and reconstruct the entire UI with updated colors/fonts."""
        # Preserve log content
        self.log_text.configure(state="normal")
        log_content = self.log_text.get("1.0", "end")
        self.log_text.configure(state="disabled")

        # Destroy all children of root
        for widget in self.root.winfo_children():
            widget.destroy()

        # Re-apply ttk style
        self._apply_ttk_style()

        # Rebuild
        self.root.configure(bg=self.C["BG"])
        self._build_ui()

        # Restore log
        self.log_text.configure(state="normal")
        self.log_text.insert("end", log_content)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

        # Restore binding dropdowns to current config values
        for gesture, var in self._binding_vars.items():
            var.set(self.config["gesture_bindings"].get(gesture, "none"))

    # ── UI Refresh Loop ───────────────────────────────────────
    def _start_ui_refresh(self):
        self._refresh()

    def _refresh(self):
        try:
            self._update_status_bar()
            self._update_live_gestures()
            self._update_gesture_history()
            self._update_preview()
        except Exception:
            pass
        self.root.after(80, self._refresh)  # ~12 fps UI

    def _update_status_bar(self):
        self.fps_var.set(f"FPS: {self.state.fps:.1f}")
        try:
            cpu = psutil.cpu_percent(interval=None)
            self.cpu_var.set(f"CPU: {cpu:.0f}%")
        except Exception:
            pass
        self.hand_var.set(f"Hand: {self.state.current_hand_gesture}")
        self.face_var.set(f"Face: {self.state.current_face_gesture}")

    def _update_live_gestures(self):
        C = self.C
        h = self.state.current_hand_gesture
        f = self.state.current_face_gesture
        self.live_hand_lbl.configure(
            text=h or "—",
            fg=C["ACCENT"] if h and h != "none" else C["TEXT_DIM"],
        )
        self.live_face_lbl.configure(
            text=f or "—",
            fg=C["ACCENT2"] if f and f != "none" else C["TEXT_DIM"],
        )

    def _update_gesture_history(self):
        history = list(self.state.gesture_history)
        self.hist_text.configure(state="normal")
        self.hist_text.delete("1.0", "end")
        for item in history:
            self.hist_text.insert("end", f"  {item}\n")
        self.hist_text.configure(state="disabled")

    def _update_preview(self):
        if not self.state.running or self.engine is None:
            return
        frame = self.engine.get_preview_frame()
        if frame is None:
            return
        try:
            from PIL import Image as PILImage, ImageTk
            h, w   = frame.shape[:2]
            lw     = self.preview_label.winfo_width()
            lh     = self.preview_label.winfo_height()
            if lw < 10 or lh < 10:
                return
            scale  = min(lw / w, lh / h)
            nw, nh = int(w * scale), int(h * scale)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img    = PILImage.fromarray(frame_rgb).resize((nw, nh), PILImage.LANCZOS)
            photo  = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label._photo = photo  # prevent GC
        except ImportError:
            self.preview_label.configure(text="Install Pillow for live preview")
        except Exception:
            pass

    def on_close(self):
        self._stop()
        self.root.destroy()


# ── Entry Point ──────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app  = GestureOSApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
