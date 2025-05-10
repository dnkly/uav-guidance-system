import socket
import json
from config import CommandType


class Simulator:
    def __init__(self, host, port):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._client.connect((host, port))

    def close(self):
        self._client.close()

    def _send(self, type, payload = None):
        buffer = json.dumps({
            "type": type.value,
            "payload": payload,
        }).encode()

        self._client.send(buffer)

    def send_event(self, event):
        self._send(CommandType.SEND_EVENT, {
            "type": event.type.value,
            "code": event.code.value,
            "value": event.value,
        })

    def update_reticle_size(self, size):
        self._send(CommandType.UPDATE_RETICLE_SIZE, size)

    def update_target(self, target):
        self._send(CommandType.UPDATE_TARGET, {
            "x": target["x"],
            "y": target["y"],
            "size": target["size"],
        })

    def reset_target(self):
        self._send(CommandType.RESET_TARGET)
