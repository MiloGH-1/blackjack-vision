"""Threaded camera capture so detection never waits on the camera.

A source is either a webcam index (0 = laptop, 1+ = virtual webcams such as
DroidCam / Iriun) or a network stream from a phone app. For streams, a bare
address is enough: "192.168.1.20" becomes DroidCam's http://192.168.1.20:4747/video.
"""

from __future__ import annotations

import re
import sys
import threading
import time

import cv2

DROIDCAM_PORT = 4747
OPEN_TIMEOUT_MS = 5000
STALE_SECONDS = 2.0          # read() gives None if no new frame for this long
RECONNECT_SECONDS = 3.0      # retry a dropped stream after this long without frames

_HOST_RE = re.compile(r"^(?P<host>[A-Za-z0-9.-]+)(?::(?P<port>\d+))?(?P<path>/.*)?$")
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def parse_source(source):
    """Turn a config/CLI camera value into something cv2.VideoCapture accepts.

    '0' -> 0 (webcam index)
    '192.168.1.20' -> 'http://192.168.1.20:4747/video' (DroidCam default)
    '192.168.1.20:8080' -> 'http://192.168.1.20:8080/video' (e.g. IP Webcam)
    'http://host:port' -> 'http://host:port/video'
    Anything else (a full URL with a path, a video file) is left alone.
    """
    if isinstance(source, int):
        return source
    s = str(source).strip()
    if s.isdigit():
        return int(s)

    if "://" in s:
        scheme, rest = s.split("://", 1)
        if "/" not in rest.rstrip("/"):
            return f"{scheme}://{rest.rstrip('/')}/video"
        return s

    m = _HOST_RE.match(s)
    if m and (m["port"] or _IPV4_RE.match(m["host"])):
        port = m["port"] or DROIDCAM_PORT
        path = m["path"] if m["path"] and m["path"] != "/" else "/video"
        return f"http://{m['host']}:{port}{path}"
    return s


def _open(src) -> cv2.VideoCapture:
    if isinstance(src, int):
        if sys.platform == "win32":
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)  # opens much faster on Windows
            if cap.isOpened():
                return cap
            cap.release()
        return cv2.VideoCapture(src)
    # Network streams: don't hang for ~30 s when the phone isn't reachable
    return cv2.VideoCapture(src, cv2.CAP_FFMPEG, [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, OPEN_TIMEOUT_MS,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, OPEN_TIMEOUT_MS,
    ])


def find_cameras(max_index: int = 6) -> list[tuple[int, tuple[int, int]]]:
    """Webcam indices that open and deliver a frame, with their resolution."""
    found = []
    for i in range(max_index):
        cap = _open(i)
        ok, frame = cap.read() if cap.isOpened() else (False, None)
        if ok:
            found.append((i, (frame.shape[1], frame.shape[0])))
        cap.release()
    return found


class Camera:
    def __init__(self, source=0, width: int = 1280, height: int = 720):
        self.source = parse_source(source)
        self.is_stream = isinstance(self.source, str)
        self._size = (width, height)
        self.cap = self._connect()
        if not self.cap.isOpened():
            raise RuntimeError(_open_error(source, self.source))

        self._frame = None
        self._frame_time = 0.0
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _connect(self) -> cv2.VideoCapture:
        cap = _open(self.source)
        if cap.isOpened() and not self.is_stream:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._size[1])
        return cap

    def _loop(self) -> None:
        last_ok = time.monotonic()
        while self._running:
            ok, frame = self.cap.read()
            if ok:
                last_ok = time.monotonic()
                with self._lock:
                    self._frame, self._frame_time = frame, last_ok
                continue
            time.sleep(0.05)
            # Wi-Fi streams drop when the phone sleeps or switches apps: reopen
            if self.is_stream and time.monotonic() - last_ok > RECONNECT_SECONDS:
                self.cap.release()
                self.cap = self._connect()
                last_ok = time.monotonic()

    def read(self):
        """Latest frame, or None if the camera hasn't delivered one recently."""
        with self._lock:
            if self._frame is None or time.monotonic() - self._frame_time > STALE_SECONDS:
                return None
            return self._frame.copy()

    def release(self) -> None:
        self._running = False
        self._thread.join(timeout=OPEN_TIMEOUT_MS / 1000 + 1)
        self.cap.release()


def _open_error(given, parsed) -> str:
    msg = f"Could not open camera source {given!r}"
    if isinstance(parsed, str):
        return (f"{msg} ({parsed}).\n"
                "Check the phone app is running and showing that address, and that the "
                "phone and laptop are on the same Wi-Fi. Opening the URL in a browser "
                "should show the video.")
    found = find_cameras()
    if found:
        listed = ", ".join(f"{i} ({w}x{h})" for i, (w, h) in found)
        return f"{msg}. Working webcam indices: {listed}."
    return (f"{msg}. No webcams were found at all - check Windows Settings > "
            "Privacy & security > Camera, or use a phone stream address instead.")
