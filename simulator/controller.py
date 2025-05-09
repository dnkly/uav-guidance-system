import libevdev


class VirtualController:
    def __init__(self, name):
        device = libevdev.Device()
        device.name = name

        self._configure_device(device)
        self.uinput = device.create_uinput_device()

    def _configure_device(self, device):
        def create_absinfo(value):
            return libevdev.InputAbsInfo(0, 2047, 7, 127, 0, value)

        device.enable(libevdev.EV_ABS.ABS_X, create_absinfo(1023))
        device.enable(libevdev.EV_ABS.ABS_Y, create_absinfo(1023))
        device.enable(libevdev.EV_ABS.ABS_Z, create_absinfo(0))

        device.enable(libevdev.EV_ABS.ABS_RX, create_absinfo(1023))
        device.enable(libevdev.EV_ABS.ABS_RY, create_absinfo(0))
        device.enable(libevdev.EV_ABS.ABS_RZ, create_absinfo(1023))

        device.enable(libevdev.EV_ABS.ABS_THROTTLE, create_absinfo(1023))
        device.enable(libevdev.EV_KEY.BTN_START)

    def send_event(self, event):
        code = libevdev.evbit(event["type"], event["code"])
        value = event["value"]

        self.uinput.send_events([
            libevdev.InputEvent(code, value),
            libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0),
        ])
