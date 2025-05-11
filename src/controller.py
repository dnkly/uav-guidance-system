import libevdev


class VirtualController:
    def __init__(self, name):
        device = libevdev.Device()
        device.name = name

        self._configure_device(device)
        self._uinput = device.create_uinput_device()

    def _configure_device(self, device):
        def create_absinfo(value):
            return libevdev.InputAbsInfo(0, 2047, 7, 127, 0, value)

        device.enable(libevdev.EV_ABS.ABS_X, create_absinfo(1024))
        device.enable(libevdev.EV_ABS.ABS_Y, create_absinfo(1024))
        device.enable(libevdev.EV_ABS.ABS_Z, create_absinfo(0))

        device.enable(libevdev.EV_ABS.ABS_RX, create_absinfo(1024))
        device.enable(libevdev.EV_ABS.ABS_RY, create_absinfo(1024))
        device.enable(libevdev.EV_KEY.BTN_TL)

    def send_event(self, event):
        syn_report = libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)
        self._uinput.send_events([event, syn_report])
