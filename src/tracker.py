import cv2
import numpy as np
import logging
import threading
from utils import (
    sklm,
    warp_image,
    warp_multiple_images,
)


class IncrementalTracker:
    def __init__(self, camera, simulator, config):
        self._camera = camera
        self._simulator = simulator

        self._nparticles = config["NPARTICLES"]
        self._condenssig = config["CONDENSSIG"]
        self._forgetting = config["FORGETTING"]
        self._batch_size = config["BATCH_SIZE"]

        template_size = config["TEMPLATE_SIZE"]
        self._template_shape = (template_size, template_size)
        self._template_dimension = template_size * template_size

        self._max_basis = config["MAX_BASIS"]
        self._affsig = np.asarray(config["AFFSIG"], dtype=np.float32)

        self._lock = threading.Lock()
        self._is_running = threading.Event()
        self._is_tracking = threading.Event()

        self._initial_box = None
        self._reset_params()

    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        try:
            self._create_initial_box()
            self._is_running.set()

            while self._is_running.is_set():
                self._is_tracking.wait()
                frame = self._camera.read()

                if frame is None:
                    continue

                with self._lock:
                    est = self._track(frame)

                self._is_tracking.wait()

                est_x = est[0]
                est_y = est[1]
                est_width = est[2] * self._template_shape[0]
                est_height = est_width * est[3]

                target_size = min(est_width, est_height)

                self._simulator.update_target({
                    "x": int(est_x),
                    "y": int(est_y),
                    "size": int(target_size),
                })
        except Exception as error:
            logging.error(error)
        finally:
            self.stop()

    def _create_initial_box(self):
        width, height = self._camera.get_dimensions()

        self._initial_box = {
            "x": width // 2,
            "y": height // 2,
            "size": 20,
        }

    def init(self):
        if self._is_tracking.is_set():
            return

        if self._initial_box is None:
            return

        degrees_of_freedom = self._affsig.size
        initial_params = np.zeros(degrees_of_freedom, dtype=np.float32)

        initial_params[0] = self._initial_box["x"]
        initial_params[1] = self._initial_box["y"]
        initial_params[2] = self._initial_box["size"] / self._template_shape[0]
        initial_params[3] = 1.0

        frame = self._camera.read()

        if frame is None:
            return

        grayscale_image = self._normalize_grayscale(frame)
        mean_2d = warp_image(grayscale_image, initial_params, self._template_shape)

        self._template["mean"] = mean_2d.flatten()
        self._params["wimg"] = mean_2d.copy()
        self._params["est"] = initial_params.copy()

        self._is_tracking.set()

    def _track(self, frame):
        grayscale_image = self._normalize_grayscale(frame)
        self._estimate_warp_condensation(grayscale_image)

        if len(self._warped_images) < self._batch_size:
            return self._params["est"]

        if "coef" in self._params:
            reconstruction = self._template["basis"] @ self._params["coef"]
            reconstructed_image = (reconstruction.T + self._template["mean"]).T

            self._update_model()

            recon = (reconstructed_image.T - self._template["mean"]).T
            self._params["coef"] = self._template["basis"].T @ recon
        else:
            self._update_model()

        self._warped_images = []
        current_eigenvector_count = self._template["basis"].shape[1]

        if current_eigenvector_count > self._max_basis:
            _sum = np.sum(np.power(self._template["eigval"][self._max_basis:], 2))
            self._template["reseig"] = self._forgetting * self._template["reseig"] + _sum

            self._template["basis"] = self._template["basis"][:, :self._max_basis]
            self._template["eigval"] = self._template["eigval"][:self._max_basis]

            if "coef" in self._params:
                self._params["coef"] = self._params["coef"][:self._max_basis]

        return self._params["est"]

    def _estimate_warp_condensation(self, grayscale_image):
        if "param" not in self._params:
            self._params["param"] = np.tile(self._params["est"], (self._nparticles, 1))
        else:
            cumulative_confidence = np.cumsum(self._params["conf"])
            random_samples = np.random.random(self._nparticles)
            cdf_indices = np.zeros(self._nparticles, dtype=np.int32)

            for i in range(self._nparticles):
                cdf_indices[i] = np.searchsorted(
                    cumulative_confidence,
                    random_samples[i],
                )

            self._params["param"] = self._params["param"][cdf_indices]

        self._params["param"] = np.random.normal(self._params["param"], self._affsig)

        warped_images_array = warp_multiple_images(
            grayscale_image,
            self._params["param"],
            self._template_shape,
        )

        warped_images_flat = warped_images_array.reshape(
            self._template_dimension,
            self._nparticles,
        )

        self._diff = warped_images_flat - self._template["mean"][:, np.newaxis]
        current_eigenvector_count = self._template["basis"].shape[1]

        if current_eigenvector_count > 0:
            projection = self._template["basis"].T @ self._diff

            self._diff -= self._template["basis"] @ projection
            self._params["coef"] = projection

        squared_diff = np.power(self._diff, 2)
        precision = 1.0 / self._condenssig

        robust_sigma = 0.1
        error = np.sum(squared_diff / (squared_diff + robust_sigma), axis=0) * -precision
        self._params["conf"] = np.exp(error)

        self._params["conf"] /= np.sum(self._params["conf"])
        max_index = np.argmax(self._params["conf"])

        self._params["est"] = self._params["param"][max_index].copy()
        self._params["wimg"] = warped_images_array[:, :, max_index].copy()
        self._params["err"] = self._diff[:, max_index].reshape(self._template_shape)
        self._params["recon"] = self._params["wimg"] + self._params["err"]

        self._warped_images.append(self._params["wimg"].flatten())

    def _normalize_grayscale(self, frame):
        grayscale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.float32(grayscale_image) / 255.0

    def _update_model(self):
        basis, eigval, mean, nsamples = sklm(
            self._warped_images,
            self._template,
            self._forgetting,
        )

        self._template["basis"] = basis
        self._template["eigval"] = eigval
        self._template["mean"] = mean
        self._template["nsamples"] = nsamples

    def update_initial_box(self, size):
        self._initial_box["size"] = size

    def reset(self):
        self._is_tracking.clear()
        self._simulator.update_target(None)

        with self._lock:
            self._reset_params()

    def _reset_params(self):
        self._warped_images = []

        self._params = {
            "conf": np.full(
                self._nparticles,
                1.0 / self._nparticles,
                dtype=np.float32,
            )
        }

        self._template = {
            "mean": np.zeros(self._template_dimension, dtype=np.float32),
            "basis": np.zeros((self._template_dimension, 0), dtype=np.float32),
            "eigval": np.array([], dtype=np.float32),
            "nsamples": 0,
            "reseig": 0,
        }

        self._diff = np.zeros(
            (self._template_dimension, self._nparticles),
            dtype=np.float32,
        )

    def stop(self):
        if not self._is_running.is_set():
            return

        self._is_running.clear()
