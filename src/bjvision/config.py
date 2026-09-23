"""Load config.yaml with sensible defaults."""

from __future__ import annotations

from pathlib import Path

import yaml

from .strategy import Rules

DEFAULTS = {
    "decks": 6,
    "dealer_hits_soft_17": False,
    "double_after_split": True,
    "surrender": True,
    "dealer_peeks": True,
    "camera": 0,
    "frame_width": 1280,
    "frame_height": 720,
    "model_path": "models/cards.pt",
    "confidence": 0.5,
    "divider": 0.45,
    "smoothing_window": 10,
    "smoothing_min_hits": 6,
}


def load_config(path: str | Path = "config.yaml") -> dict:
    cfg = dict(DEFAULTS)
    p = Path(path)
    if p.exists():
        cfg.update(yaml.safe_load(p.read_text()) or {})
    return cfg


def rules_from(cfg: dict) -> Rules:
    return Rules(
        decks=int(cfg["decks"]),
        dealer_hits_soft_17=bool(cfg["dealer_hits_soft_17"]),
        double_after_split=bool(cfg["double_after_split"]),
        surrender=bool(cfg["surrender"]),
        dealer_peeks=bool(cfg["dealer_peeks"]),
    )
