import logging
import threading
import subprocess
import numpy as np


class VirtualCamera:
    def __init__(self, stream_url, resolution):
        self._width, self._height = resolution
        self._current_frame = None

        self._lock = threading.Lock()
        self._is_running = threading.Event()

        self._ffmpeg_process = None
        self._ffmpeg_command = [
            "ffmpeg",
            "-c:v", "hevc_cuvid",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-i", stream_url,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._width}x{self._height}",
            "-",
        ]

    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        try:
            self._ffmpeg_process = subprocess.Popen(
                self._ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            frame_size = self._width * self._height * 3
            self._is_running.set()

            while self._is_running.is_set():
                buffer = self._ffmpeg_process.stdout.read(frame_size)

                if len(buffer) < frame_size:
                    break

                frame = np.frombuffer(buffer, dtype=np.uint8)
                frame = frame.reshape((self._height, self._width, 3))

                with self._lock:
                    self._current_frame = frame
        except Exception as error:
            logging.error(error)
        finally:
            self.stop()

    def read(self):
        with self._lock:
            if self._current_frame is None:
                return None

            return self._current_frame.copy()

    def get_resolution(self):
        return self._width, self._height

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()

        if self._ffmpeg_process is not None:
            self._ffmpeg_process.terminate()
            self._ffmpeg_process.wait()
            self._ffmpeg_process = None
