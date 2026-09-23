import pytest

from bjvision.camera import parse_source


@pytest.mark.parametrize("given, expected", [
    (0, 0),
    ("1", 1),
    (" 2 ", 2),
    ("192.168.1.20", "http://192.168.1.20:4747/video"),
    ("192.168.1.20:8080", "http://192.168.1.20:8080/video"),
    ("192.168.1.20:8080/", "http://192.168.1.20:8080/video"),
    ("192.168.1.20:4747/mjpegfeed", "http://192.168.1.20:4747/mjpegfeed"),
    ("phone.local:4747", "http://phone.local:4747/video"),
    ("http://192.168.1.20:8080", "http://192.168.1.20:8080/video"),
    ("http://192.168.1.20:8080/", "http://192.168.1.20:8080/video"),
    ("http://192.168.1.20:8080/video", "http://192.168.1.20:8080/video"),
    ("rtsp://10.0.0.5:8554/live", "rtsp://10.0.0.5:8554/live"),
    ("table.mp4", "table.mp4"),
    (r"C:\videos\table.mp4", r"C:\videos\table.mp4"),
])
def test_parse_source(given, expected):
    assert parse_source(given) == expected
