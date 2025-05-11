import cv2
import logging
import threading


class VirtualCamera:
    def __init__(self, stream_url):
        self._stream_url = stream_url
        self._current_frame = None

        self._capture = cv2.VideoCapture()
        self._lock = threading.Lock()
        self._is_running = threading.Event()

    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        try:
            self._capture.open(self._stream_url, cv2.CAP_FFMPEG)
            self._is_running.set()

            while self._is_running.is_set():
                ret, frame = self._capture.read()

                if not ret:
                    break

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

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()
        self._capture.release()

    def get_dimensions(self):
        self._is_running.wait()
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return width, height
