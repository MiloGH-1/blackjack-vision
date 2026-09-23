"""Threaded camera capture so detection never waits on the camera."""

from __future__ import annotations

import sys
import threading

import cv2


def parse_source(source):
    """'0' -> 0 (webcam index); anything else (e.g. an http URL) stays a string."""
    if isinstance(source, int):
        return source
    s = str(source).strip()
    return int(s) if s.isdigit() else s


class Camera:
    def __init__(self, source=0, width: int = 1280, height: int = 720):
        src = parse_source(source)
        if isinstance(src, int) and sys.platform == "win32":
            self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)  # opens much faster on Windows
        else:
            self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera source {source!r}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self._frame = None
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self._running:
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._frame = frame

    def read(self):
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def release(self) -> None:
        self._running = False
        self._thread.join(timeout=1)
        self.cap.release()
