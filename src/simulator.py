import socket
import libevdev
import json
from config import CommandType


class Simulator:
    def __init__(self, host: str, port: int):
        self._client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._client.connect((host, port))

    def close(self):
        self._client.close()

    def _send(self, data):
        buffer = json.dumps(data).encode()
        self._client.send(buffer)

    def send_event(self, event: libevdev.InputEvent):
        self._send({
            "type": CommandType.SEND_EVENT.value,
            "payload": {
                "type": event.type.value,
                "code": event.code.value,
                "value": event.value,
            },
        })

    def update_target(self, x: int, y: int):
        self._send({
            "type": CommandType.UPDATE_TARGET.value,
            "payload": {
                "x": x,
                "y": y
            },
        })

    def reset_target(self):
        self._send({ "type": CommandType.RESET_TARGET.value })
