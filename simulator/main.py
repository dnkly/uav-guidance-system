import socket
import logging
import json
from camera import VirtualCamera
from controller import VirtualController
from config import (
    CommandType,
    CONTROLLER_NAME,
    SIMULATOR_HOST,
    SIMULATOR_PORT,
    VIDEO_STREAM_URL,
    WINDOW_NAME,
)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    camera = VirtualCamera(VIDEO_STREAM_URL, WINDOW_NAME)
    controller = VirtualController(CONTROLLER_NAME)

    try:
        server.bind((SIMULATOR_HOST, SIMULATOR_PORT))
        camera.run()

        logging.info(f"Server: {SIMULATOR_HOST}:{SIMULATOR_PORT}")
        logging.info(f"Camera: {VIDEO_STREAM_URL}")
        logging.info(f"Controller: {CONTROLLER_NAME}")
        logging.info("Listening to guidance system commands...")

        while True:
            buffer, _ = server.recvfrom(1024)
            command = json.loads(buffer.decode())
            process_command(command, camera, controller)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logging.error(error)
    finally:
        camera.stop()
        server.close()


def process_command(command, camera, controller):
    command_type = CommandType(command["type"])
    payload = command["payload"]

    match command_type:
        case CommandType.SEND_EVENT:
            controller.send_event(payload)
        case CommandType.UPDATE_RETICLE_SIZE:
            camera.update_reticle_size(payload)
        case CommandType.UPDATE_TARGET:
            camera.update_target(payload)
        case CommandType.RESET_TARGET:
            camera.reset_target()


if __name__ == "__main__":
    main()
