import cv2
import logging
import threading


class VirtualCamera:
    def __init__(self, stream_url, window_name):
        self._capture = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
        self._lock = threading.Lock()
        self._is_running = threading.Event()

        self._window_name = window_name
        self._target = None

        self._width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._center = {
            "x": self._width // 2,
            "y": self._height // 2,
        }

        self._overlay = {
            "bounding_box_size": 20,
            "crosshair_size": 4,
            "color": (255, 255, 255),
            "thickness": 2,
        }

    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        try:
            cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self._window_name, self._width, self._height)
            self._is_running.set()

            while self._is_running.is_set():
                ret, frame = self._capture.read()

                if not ret:
                    break

                self._draw_overlay(frame)
                cv2.imshow(self._window_name, frame)

                if cv2.waitKey(1) == ord("q"):
                    break
        except Exception as error:
            logging.error(error)
        finally:
            self.stop()

    def _draw_overlay(self, frame):
        x = self._center["x"]
        y = self._center["y"]

        size = self._overlay["crosshair_size"]
        color = self._overlay["color"]
        thickness = self._overlay["thickness"]

        cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
        cv2.line(frame, (x, y - size), (x, y + size), color, thickness)

        with self._lock:
            if self._target is None:
                self._draw_rect(self._center, frame)
            else:
                self._draw_rect(self._target, frame)

    def _draw_rect(self, position, frame):
        x = position["x"]
        y = position["y"]

        size = self._overlay["bounding_box_size"]
        color = self._overlay["color"]
        thickness = self._overlay["thickness"]

        cv2.line(frame, (x - size, y - size), (x - size, y - size // 2), color, thickness)
        cv2.line(frame, (x - size, y - size), (x - size // 2, y - size), color, thickness)

        cv2.line(frame, (x + size, y - size), (x + size, y - size // 2), color, thickness)
        cv2.line(frame, (x + size, y - size), (x + size // 2, y - size), color, thickness)

        cv2.line(frame, (x - size, y + size), (x - size, y + size // 2), color, thickness)
        cv2.line(frame, (x - size, y + size), (x - size // 2, y + size), color, thickness)

        cv2.line(frame, (x + size, y + size), (x + size, y + size // 2), color, thickness)
        cv2.line(frame, (x + size, y + size), (x + size // 2, y + size), color, thickness)

    def update_target(self, target):
        with self._lock:
            self._target = target

    def reset_target(self):
        with self._lock:
            self._target = None

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()
        self._capture.release()
        cv2.destroyWindow(self._window_name)
