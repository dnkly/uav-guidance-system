import libevdev
import simulator
import config


def main():
    try:
        with open(config.DEVICE_PATH) as fd:
            device = libevdev.Device(fd)

            while True:
                process_events(device)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"Error: {error}")
    finally:
        simulator.close()


def process_events(device: libevdev.Device):
    for event in device.events():
        if not event.matches(libevdev.EV_ABS):
            continue

        simulator.send_event(event)


if __name__ == "__main__":
    main()
