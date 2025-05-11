import logging
import numpy as np
from enum import Enum


logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG,
)


class SystemState(Enum):
    STANDBY = 0
    TRACKING = 1024
    AUTOPILOT = 2047


CONTROLLER_NAME = "Virtual RadioMaster TX12"
CONTROLLER_PATH = "/dev/input/event22"

VIDEO_STREAM_URL = "udp://127.0.0.1:9000"
WINDOW_NAME = "UAV Guidance System"


TRACKER_CONFIG = {
    # NPARTICLES. The number of particles used in the condensation
    # algorithm/particle filter.  Increasing this will likely improve the
    # results, but make the tracker slower.
    "NPARTICLES": 500,

    # CONDENSSIG. The standard deviation of the observation likelihood.
    "CONDENSSIG": 0.75,

    # FORGETTING. The forgetting factor, as described in the original paper. When
    # doing the incremental update, 1 means remember all past data, and 0
    # means remeber none of it.
    "FORGETTING": 0.95,

    # BATCH_SIZE. How often to update the eigenbasis. We've used this
    # value (update every 5th frame) fairly consistently, so it most
    # likely won't need to be changed.  A smaller batchsize means more
    # frequent updates, making it quicker to model changes in appearance,
    # but also a little more prone to drift, and require more computation.
    "BATCH_SIZE": 5,

    # TEMPLATE_SIZE. The resolution at which the tracking window is
    # sampled, 32-by-32 pixels by default.  If your initial
    # object window is very large you may need to increase this.
    "TEMPLATE_SIZE": 32,

    # MAX_BASIS. The number of basis vectors to keep in the learned
    # apperance model.
    "MAX_BASIS": 16,

    # RESIZE_RATE. Of input frames.
    "RESIZE_RATE": 0.8,

    # AFFSIG. These are the standard deviations of the dynamics distribution,
    # that is how much we expect the target object might move from one frame to the next.
    # The meaning of each number is as follows:
    #    AFFSIG(0) = x translation (pixels)
    #    AFFSIG(1) = y translation (pixels)
    #    AFFSIG(2) = scale
    #    AFFSIG(3) = aspect ratio
    #    AFFSIG(4) = rotation angle (radians)
    #    AFFSIG(5) = skew angle (radians)
    "AFFSIG": np.array([10, 10, 0.05, 0.002], dtype=np.float32),
}
