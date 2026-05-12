#!/usr/bin/env python3
"""
GestureOS Setup & Launcher
Run this first to install dependencies, then launch the app.
"""

import subprocess
import sys
import os

PACKAGES = [
    "mediapipe",
    "opencv-python",
    "pyautogui",
    "numpy",
    "Pillow",
    "psutil",
    "pystray",
]

def check_and_install():
    print("=" * 55)
    print("  GestureOS — Dependency Setup")
    print("=" * 55)

    missing = []
    import importlib
    pkg_map = {
        "mediapipe": "mediapipe",
        "opencv-python": "cv2",
        "pyautogui": "pyautogui",
        "numpy": "numpy",
        "Pillow": "PIL",
        "psutil": "psutil",
        "pystray": "pystray",
    }
    for pkg, mod in pkg_map.items():
        try:
            importlib.import_module(mod)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg}  (will install)")
            missing.append(pkg)

    if missing:
        print(f"\nInstalling {len(missing)} missing package(s)...")
        for pkg in missing:
            print(f"  → {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        print("\nAll packages installed ✓")
    else:
        print("\nAll dependencies satisfied ✓")

    print("\nLaunching GestureOS...")
    print("=" * 55)

def main():
    check_and_install()
    # Launch main app
    script = os.path.join(os.path.dirname(__file__), "gesture_control.py")
    os.execv(sys.executable, [sys.executable, script])

if __name__ == "__main__":
    main()
