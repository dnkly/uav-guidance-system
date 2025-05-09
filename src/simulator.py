import socket
import json
from config import CommandType


class Simulator:
    def __init__(self, host, port):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._client.connect((host, port))

    def close(self):
        self._client.close()

    def _send(self, data):
        buffer = json.dumps(data).encode()
        self._client.send(buffer)

    def send_event(self, event):
        self._send({
            "type": CommandType.SEND_EVENT.value,
            "payload": {
                "type": event.type.value,
                "code": event.code.value,
                "value": event.value,
            },
        })

    def update_target(self, target):
        self._send({
            "type": CommandType.UPDATE_TARGET.value,
            "payload": {
                "x": target["x"],
                "y": target["y"],
            },
        })

    def reset_target(self):
        self._send({ "type": CommandType.RESET_TARGET.value })
