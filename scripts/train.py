"""Fine-tune YOLOv8 on a playing-card dataset and install the weights.

    python scripts/train.py --data datasets/playing-cards/data.yaml --epochs 50

The dataset must be in YOLOv8 format with class names like "10H", "KS", "AC".
The best weights are copied to models/cards.pt, where the app looks for them.
"""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to the dataset's data.yaml")
    ap.add_argument("--base", default="yolov8s.pt", help="starting weights (yolov8n.pt is faster)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16, help="lower this if you run out of GPU memory")
    ap.add_argument("--device", default=None, help="0 for first GPU, 'cpu' to force CPU")
    args = ap.parse_args()

    model = YOLO(args.base)
    results = model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz,
                          batch=args.batch, device=args.device, project="runs", name="cards")

    best = Path(results.save_dir) / "weights" / "best.pt"
    dest = Path("models/cards.pt")
    dest.parent.mkdir(exist_ok=True)
    shutil.copy(best, dest)
    print(f"Copied {best} -> {dest}")


if __name__ == "__main__":
    main()
