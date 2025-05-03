import libevdev
import socket
import json


UDP_HOST = "127.0.0.1"
UDP_PORT = 8888


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((UDP_HOST, UDP_PORT))

    try:
        device = create_device()

        while True:
            message, _ = server.recvfrom(1024)
            data = json.loads(message.decode())

            if data["type"] == 0:
                handle_device_event(device, data["payload"])
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"Error: {error}")
    finally:
        server.close()


def create_device():
    device = libevdev.Device()
    device.name = "Virtual RadioMaster TX12"

    def create_absinfo(value: int):
        return libevdev.InputAbsInfo(0, 2047, 7, 127, 0, value)

    device.enable(libevdev.EV_ABS.ABS_X, create_absinfo(1023))
    device.enable(libevdev.EV_ABS.ABS_Y, create_absinfo(1023))
    device.enable(libevdev.EV_ABS.ABS_Z, create_absinfo(0))

    device.enable(libevdev.EV_ABS.ABS_RX, create_absinfo(1023))
    device.enable(libevdev.EV_ABS.ABS_RY, create_absinfo(0))
    device.enable(libevdev.EV_ABS.ABS_RZ, create_absinfo(1023))

    device.enable(libevdev.EV_ABS.ABS_THROTTLE, create_absinfo(1023))
    device.enable(libevdev.EV_KEY.BTN_START)

    uinput = device.create_uinput_device()
    return uinput


def handle_device_event(device: libevdev.Device, payload):
    code = libevdev.evbit(payload["type"], payload["code"])
    value = payload["value"]

    device.send_events([
        libevdev.InputEvent(code, value),
        libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)
    ])


if __name__ == "__main__":
    main()
