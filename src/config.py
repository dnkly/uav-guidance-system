import logging
from enum import Enum

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG,
)

class CommandType(Enum):
    SEND_EVENT = 0
    UPDATE_RETICLE_SIZE = 1
    UPDATE_TARGET = 2
    RESET_TARGET = 3

CONTROLLER_PATH = "/dev/input/event15"

SIMULATOR_HOST = "127.0.0.1"
SIMULATOR_PORT = 9001
