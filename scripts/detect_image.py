"""Run the detector on a still photo and print what it finds.

    python scripts/detect_image.py photo.jpg [--show]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cv2  # noqa: E402

from bjvision.config import load_config  # noqa: E402
from bjvision.detector import CardDetector  # noqa: E402
from bjvision.tracker import merge_corners  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    img = cv2.imread(args.image)
    if img is None:
        sys.exit(f"Could not read {args.image}")

    dets = CardDetector(cfg["model_path"], cfg["confidence"]).detect(img)
    h, w = img.shape[:2]
    cards = merge_corners(dets, 0.2 * (w * w + h * h) ** 0.5)

    print(f"{len(dets)} raw detections -> {len(cards)} cards")
    for c in sorted(cards, key=lambda c: (c.center[1], c.center[0])):
        print(f"  {c.label:4} at ({c.center[0]:.0f}, {c.center[1]:.0f})")

    if args.show:
        for d in dets:
            cv2.rectangle(img, d.box[:2], d.box[2:], (0, 255, 255), 2)
            cv2.putText(img, f"{d.label} {d.conf:.2f}", d.box[:2],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow("detections", img)
        cv2.waitKey(0)


if __name__ == "__main__":
    main()
