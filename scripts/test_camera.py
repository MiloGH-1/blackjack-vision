"""Check a camera source works. Press Q to quit.

    python scripts/test_camera.py --scan                  # list working webcam indices
    python scripts/test_camera.py --source 0              # laptop webcam
    python scripts/test_camera.py --source 192.168.1.20   # phone running DroidCam over Wi-Fi
    python scripts/test_camera.py --source http://192.168.1.20:8080/video   # e.g. IP Webcam
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cv2  # noqa: E402

from bjvision.camera import Camera, find_cameras, parse_source  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0", help="webcam index, phone IP or stream URL")
    ap.add_argument("--scan", action="store_true", help="list working webcam indices and exit")
    args = ap.parse_args()

    if args.scan:
        found = find_cameras()
        if not found:
            print("No webcams found.")
        for i, (w, h) in found:
            print(f"  camera {i}: {w}x{h}")
        return

    print(f"Opening {parse_source(args.source)!r} ...")
    try:
        cam = Camera(args.source)
    except RuntimeError as e:
        sys.exit(f"Error: {e}")
    print("Opened. Press Q in the window to quit.")
    try:
        while True:
            frame = cam.read()
            if frame is not None:
                h, w = frame.shape[:2]
                cv2.putText(frame, f"{w}x{h}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2)
                cv2.imshow("camera test", frame)
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
