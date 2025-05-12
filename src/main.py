import libevdev
import logging
from camera import VirtualCamera
from simulator import Simulator
from tracker import IncrementalTracker
from config import (
    SystemState,
    CONTROLLER_NAME,
    CONTROLLER_PATH,
    VIDEO_STREAM_URL,
    VIDEO_RESOLUTION,
    WINDOW_NAME,
    TRACKER_CONFIG,
)


def main():
    camera = VirtualCamera(VIDEO_STREAM_URL, VIDEO_RESOLUTION)
    simulator = Simulator(camera, CONTROLLER_NAME, WINDOW_NAME)
    tracker = IncrementalTracker(camera, simulator, TRACKER_CONFIG)

    try:
        camera.run()
        simulator.run()
        tracker.run()

        with open(CONTROLLER_PATH) as fd:
            controller = libevdev.Device(fd)

            logging.info(f"Camera: {VIDEO_STREAM_URL}")
            logging.info(f"Controller: {controller.name}")
            logging.info("Listening to controller events...")

            while True:
                for event in controller.events():
                    process_event(event, simulator, tracker)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logging.error(error)
    finally:
        tracker.stop()
        simulator.stop()
        camera.stop()


def process_event(event, simulator, tracker):
    is_abs = event.matches(libevdev.EV_ABS)
    is_key = event.matches(libevdev.EV_KEY)

    if not is_abs and not is_key:
        return

    if event.matches(libevdev.EV_ABS.ABS_RZ):
        system_state = SystemState(event.value)

        match system_state:
            case SystemState.STANDBY:
                tracker.reset()
            case SystemState.TRACKING:
                tracker.init()
            case SystemState.AUTOPILOT:
                pass
    elif event.matches(libevdev.EV_ABS.ABS_THROTTLE):
        size = event.value // 20
        tracker.update_initial_box(size)
        simulator.update_reticle_size(size)
    else:
        simulator.send_event(event)


if __name__ == "__main__":
    main()
