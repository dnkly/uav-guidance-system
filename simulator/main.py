import socket
import logging
import json
from config import CommandType, CONTROLLER_NAME, SIMULATOR_HOST, SIMULATOR_PORT
from controller import VirtualController


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    controller = VirtualController(CONTROLLER_NAME)

    try:
        server.bind((SIMULATOR_HOST, SIMULATOR_PORT))

        logging.info(f"Server: {SIMULATOR_HOST}:{SIMULATOR_PORT}")
        logging.info(f"Controller: {CONTROLLER_NAME}")
        logging.info("Listening to guidance system commands...")

        while True:
            buffer, _ = server.recvfrom(1024)
            command = json.loads(buffer.decode())
            process_command(command, controller)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logging.error(error)
    finally:
        server.close()


def process_command(
    command: dict,
    controller: VirtualController,
):
    command_type = CommandType(command["type"])

    match command_type:
        case CommandType.SEND_EVENT:
            controller.send_event(command["payload"])
        case CommandType.UPDATE_TARGET:
            pass
        case CommandType.RESET_TARGET:
            pass


if __name__ == "__main__":
    main()
