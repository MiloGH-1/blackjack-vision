"""YOLOv8 wrapper: frame in, card detections out."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cards import Card, parse_label


@dataclass(frozen=True)
class Detection:
    label: str                      # normalised, e.g. "10H"
    card: Card
    box: tuple[int, int, int, int]  # x1, y1, x2, y2
    conf: float

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.box
        return (x1 + x2) / 2, (y1 + y2) / 2


class CardDetector:
    def __init__(self, model_path: str | Path, confidence: float = 0.5):
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(
                f"No model weights at {path}. Train one with scripts/train.py "
                "or download pretrained weights - see README.md.")
        from ultralytics import YOLO  # imported lazily: it's slow and heavy
        self.model = YOLO(str(path))
        self.confidence = confidence
        self._labels = {}
        for idx, name in self.model.names.items():
            try:
                card = parse_label(name)
                self._labels[idx] = (f"{card.rank}{card.suit}", card)
            except ValueError:
                pass  # ignore any non-card classes
        if not self._labels:
            raise ValueError(f"Model classes don't look like cards: {self.model.names}")

    def detect(self, frame) -> list[Detection]:
        result = self.model.predict(frame, conf=self.confidence, verbose=False)[0]
        out = []
        for box in result.boxes:
            cls = int(box.cls[0])
            if cls not in self._labels:
                continue
            label, card = self._labels[cls]
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            out.append(Detection(label, card, (x1, y1, x2, y2), float(box.conf[0])))
        return out
