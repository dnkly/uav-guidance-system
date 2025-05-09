import logging
from enum import Enum

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG,
)

class CommandType(Enum):
    SEND_EVENT = 0
    UPDATE_TARGET = 1
    RESET_TARGET = 2

CONTROLLER_NAME = "Virtual RadioMaster TX12"

SIMULATOR_HOST = "127.0.0.1"
SIMULATOR_PORT = 9001

VIDEO_STREAM_URL = "udp://127.0.0.1:9000"
WINDOW_NAME = "UAV Guidance System"
