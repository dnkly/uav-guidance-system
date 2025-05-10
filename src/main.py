import libevdev
import logging
from simulator import Simulator
from config import (
    CONTROLLER_PATH,
    SIMULATOR_HOST,
    SIMULATOR_PORT,
)


def main():
    simulator = Simulator(SIMULATOR_HOST, SIMULATOR_PORT)

    try:
        with open(CONTROLLER_PATH) as fd:
            controller = libevdev.Device(fd)

            logging.info(f"Simulator: {SIMULATOR_HOST}:{SIMULATOR_PORT}")
            logging.info(f"Controller: {controller.name}")
            logging.info("Listening to controller events...")

            while True:
                for event in controller.events():
                    process_event(event, simulator)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logging.error(error)
    finally:
        simulator.close()


def process_event(event, simulator):
    is_abs = event.matches(libevdev.EV_ABS)
    is_key = event.matches(libevdev.EV_KEY)

    if not is_abs and not is_key:
        return

    simulator.send_event(event)


if __name__ == "__main__":
    main()
