import socket
import libevdev
import json
import config


_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_address = (config.UDP_HOST, config.UDP_PORT)


def send_event(event: libevdev.InputEvent):
    _send({
        "type": 0,
        "payload": {
            "type": event.type.value,
            "code": event.code.value,
            "value": event.value
        }
    })


def send_target(x: int, y: int):
    _send({
        "type": 1,
        "payload": {
            "x": x,
            "y": y
        }
    })


def _send(data):
    message = json.dumps(data).encode()
    _client.sendto(message, _address)


def close():
    _client.close()
