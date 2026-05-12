# GestureOS — Webcam Gesture PC Control

Control your entire PC with hand gestures and micro-facial expressions via your webcam.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch
python gesture_control.py

# OR use the auto-installer
python setup_and_run.py
```

---

## Features

### ✋ Hand Gestures
| Gesture | Action | How |
|---|---|---|
| **Index Point** | Move cursor | Extend only your index finger |
| **Pinch** | Left click | Bring thumb + index tip together |
| **Double Pinch** | Double click | Pinch twice quickly |
| **Fist** | Right click | Close all fingers |
| **Open Hand** | Scroll mode | All 5 fingers extended; move hand up/down to scroll |
| **Peace ✌️** | Screenshot | Index + middle extended |
| **Thumbs Up** | Volume up | Only thumb extended, pointing up |
| **Thumbs Down** | Volume down | Thumb pointing down |
| **Call Me 🤙** | Play/Pause | Thumb + pinky extended |
| **OK Sign** | Middle click | Thumb + index form a circle |

### 😊 Micro-Facial Gestures
| Gesture | Action |
|---|---|
| **Raise Eyebrows** | Alt+Tab (switch windows) |
| **Blink Left Eye** | Browser Back |
| **Blink Right Eye** | Browser Forward |
| **Open Mouth Wide** | Zoom In (Ctrl+=) |
| **Smile** | Zoom Out (Ctrl+-) |
| **Squint Both Eyes** | Fullscreen (F11) |

---

## Settings

All settings are saved to `~/.gesture_os_config.json` and loaded on next launch.

### Quick Settings (Sidebar)
- Toggle hand / face gestures on or off
- Show/hide landmarks overlay
- Enable debug overlay
- Cursor sensitivity slider

### Advanced Tab
- Camera index (if you have multiple webcams)
- MediaPipe detection & tracking confidence
- Smoothing factor (higher = smoother but laggier cursor)
- Gesture cooldown (prevents accidental repeat triggers)
- Scroll speed

### Bindings Tab
Remap any gesture to any action. Available actions:
`move_cursor`, `left_click`, `double_click`, `right_click`, `middle_click`,
`scroll_mode`, `screenshot`, `volume_up`, `volume_down`, `media_play_pause`,
`switch_window`, `back`, `forward`, `zoom_in`, `zoom_out`, `fullscreen`,
`copy`, `paste`, `undo`, `none`

---

## Tips

1. **Lighting matters** — ensure your face and hands are well-lit from the front
2. **Distance** — sit ~50–80cm from the camera for best detection
3. **Adjust sensitivity** — if the cursor feels jittery, increase smoothing factor; if sluggish, reduce it
4. **Reduce false positives** — raise the detection confidence threshold in Advanced settings
5. **Pause quickly** — click PAUSE in the sidebar any time; the camera feed freezes

---

## Platform Notes

### Linux
```bash
sudo apt install python3-tk libxcb-xinerama0 scrot xdotool
```

### macOS
```bash
brew install python-tk
# Then grant Accessibility permissions:
# System Preferences → Security & Privacy → Accessibility → add Terminal/Python
```

### Windows
No extra dependencies. Run as normal user (not admin).

---

## Architecture

```
gesture_control.py
├── HandGestureRecognizer   — MediaPipe Hands, 10 gesture types
├── FaceGestureRecognizer   — MediaPipe FaceMesh, 6 micro-expression types
├── ActionExecutor          — pyautogui actions with cooldown
├── CursorSmoother          — Rolling average cursor smoothing
├── GestureEngine           — Main loop, threading, frame rendering
└── GestureOSApp            — Tkinter GUI, live preview, settings
```

Config is stored in `~/.gesture_os_config.json`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Camera not found | Change camera index in Advanced settings (try 0, 1, 2) |
| Cursor jitter | Increase smoothing factor (8–12) |
| Gestures not detected | Lower detection confidence (0.5–0.65) |
| False triggers | Increase gesture cooldown (600–800ms) |
| Black preview | Check camera index; ensure no other app is using the camera |
| pyautogui FAILSAFE | Move mouse to top-left corner rapidly to emergency stop |
