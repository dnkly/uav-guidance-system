import cv2
import time
import logging
import threading
from controller import VirtualController


class Simulator:
    def __init__(self, camera, controller_name, window_name):
        self._camera = camera
        self._window_name = window_name
        self._frame_time = 1 / 60

        self._controller = VirtualController(controller_name)
        self._lock = threading.Lock()
        self._is_running = threading.Event()

        self._reticle = None
        self._target = None

        self._overlay = {
            "crosshair_size": 4,
            "color": (255, 255, 255),
            "thickness": 2,
        }

    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        try:
            self._create_window()
            self._is_running.set()

            while self._is_running.is_set():
                start_time = time.time()

                if cv2.waitKey(1) == ord("q"):
                    break

                frame = self._camera.read()

                if frame is None:
                    continue

                self._draw_overlay(frame)
                cv2.imshow(self._window_name, frame)

                duration = time.time() - start_time
                sleep_time = self._frame_time - duration

                if sleep_time > 0:
                    time.sleep(sleep_time)
        except Exception as error:
            logging.error(error)
        finally:
            self.stop()

    def _create_window(self):
        width, height = self._camera.get_resolution()

        cv2.namedWindow(self._window_name, cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(self._window_name, width, height)

        self._reticle = {
            "x": width // 2,
            "y": height // 2,
            "size": 40,
        }

    def _draw_overlay(self, frame):
        if self._reticle is None:
            return

        x = self._reticle["x"]
        y = self._reticle["y"]

        size = self._overlay["crosshair_size"]
        color = self._overlay["color"]
        thickness = self._overlay["thickness"]

        cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
        cv2.line(frame, (x, y - size), (x, y + size), color, thickness)

        with self._lock:
            if self._target is None:
                self._draw_rect(frame, self._reticle)
            else:
                self._draw_rect(frame, self._target)

    def _draw_rect(self, frame, data):
        x = data["x"]
        y = data["y"]
        size = data["size"] // 2

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

    def send_event(self, event):
        self._controller.send_event(event)

    def update_reticle_size(self, size):
        with self._lock:
            self._reticle["size"] = size

    def update_target(self, target):
        with self._lock:
            self._target = target

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()
        cv2.destroyWindow(self._window_name)
