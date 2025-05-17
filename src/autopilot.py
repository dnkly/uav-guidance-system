import queue
import logging
import threading
import libevdev


class Autopilot:
    def __init__(self, simulator, resolution):
        self._simulator = simulator
        self._queue = queue.Queue()
        width, height = resolution

        self._center = {
            "x": width // 2,
            "y": height // 2,
        }

        self._is_running = threading.Event()
        self._is_enabled = False

        self._target_size = None
        self._deadzone = 0.02
        self._smoothing = 0.4

        self._s_dx = 0
        self._s_dy = 0

    def run(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        try:
            self._is_running.set()

            while self._is_running.is_set():
                target = self._queue.get()

                if self._target_size is None:
                    self._target_size = target["size"]

                dx = target["x"] - self._center["x"]
                dy = target["y"] - self._center["y"] + target["size"] / 2
                ds = target["size"] - self._target_size

                self._s_dx = (1 - self._smoothing) * dx + self._smoothing * self._s_dx
                self._s_dy = (1 - self._smoothing) * dy + self._smoothing * self._s_dy

                nx = self._s_dx / self._center["x"]
                ny = self._s_dy / self._center["y"]
                ns = ds / self._center["y"]

                if abs(ny) < self._deadzone:
                    ny = 0

                throttle = -(ny + ns + 0.05)

                self._send_event(libevdev.EV_ABS.ABS_Y, ny)
                self._send_event(libevdev.EV_ABS.ABS_X, nx)
                self._send_event(libevdev.EV_ABS.ABS_RX, nx)
                self._send_event(libevdev.EV_ABS.ABS_Z, throttle)
        except Exception as error:
            logging.error(error)
        finally:
            self.stop()

    def _send_event(self, code, coef):
        value = int(1023 + coef * 1023)
        event = libevdev.InputEvent(code, value)
        self._simulator.send_event(event)

    def update_target(self, target):
        if self._is_enabled:
            self._queue.put(target)

    def is_enabled(self):
        return self._is_enabled

    def enable(self):
        self._is_enabled = True

    def disable(self):
        self._is_enabled = False
        self._target_size = None
        self._s_dx = 0
        self._s_dy = 0

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()
        self.disable()
