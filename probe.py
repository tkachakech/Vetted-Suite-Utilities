import cv2

def test_cameras():
    print("Scanning for active cameras...")
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"SUCCESS: Camera found at INDEX {i}")
                cap.release()
                return i
            cap.release()
        else:
            print(f"INDEX {i}: Not found.")
    return None

active_index = test_cameras()
if active_index is not None:
    print(f"\nYour camera is at Index {active_index}. Open your config file and set it.")
else:
    print("\nCRITICAL: No cameras detected. Check Windows Privacy Settings.")
