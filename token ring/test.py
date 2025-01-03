import socket
import threading
import logging
import time
import queue
import signal
import sys
from typing import Tuple
from poissonEvents import generate_requests

PORT_CALCULATOR = 12346
FORMAT = 'UTF-8'
queue_ = queue.Queue()
shutdown_event = threading.Event()  # Usando evento para shutdown seguro


class PeerNode:
    def __init__(self, next_address: Tuple[str, int]):
        self.next_address = next_address


def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    shutdown_event.set()  # Marca o evento de desligamento
    propagate_shutdown(peer_node.next_address)
    print("Shutdown signal sent")


signal.signal(signal.SIGINT, signal_handler)


class Logs:
    def __init__(self, hostname: str):
        self.logger = logging.getLogger("logfile")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"./{hostname}_peer.log", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


def propagate_shutdown(next_address: Tuple[str, int]):
    print("Propagating shutdown...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as next_socket:
            next_socket.connect(next_address)
            next_socket.send("shut".encode(FORMAT))
    except Exception as e:
        print(f"Failed to send shutdown signal to {next_address}: {e}")


def process_queue(address_calculator, logger):
    while not queue_.empty():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as calculator_server:
            try:
                calculator_server.connect(address_calculator)
                item = queue_.get()
                calculator_server.send(item.encode(FORMAT))
                result = calculator_server.recv(1024).decode(FORMAT)
                logger.info(f"Calculator result: {result}")
                print(result)
            except Exception as e:
                logger.error(f"Error connecting to calculator: {e}")


def forward_message(next_address: Tuple[str, int], msg: str, logger: logging.Logger):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as next_socket:
            next_socket.connect(next_address)
            next_socket.send(msg.encode(FORMAT))
            logger.info(f"Message forwarded to {next_address}: {msg}")
    except Exception as e:
        logger.warning(f"Failed to forward message to {next_address}: {e}")


def server_run(host: str, port: int, next_address: Tuple[str, int], logger: logging.Logger, address_calculator):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()

        logger.info(f"Server running at {host}:{port}")
        while not shutdown_event.is_set():
            try:
                client_socket, addr = server.accept()
                threading.Thread(target=handle_connection, args=(client_socket, addr, next_address, logger, address_calculator)).start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")


def handle_connection(client: socket.socket, client_address: Tuple[str, int], next_address: Tuple[str, int], logger: logging.Logger, address_calculator):
    try:
        msg = client.recv(1024).decode(FORMAT)
        logger.info(f"Received message from {client_address}: {msg}")

        if msg == "shut":
            shutdown_event.set()
            propagate_shutdown(next_address)
            return

        process_queue(address_calculator, logger)
        forward_message(next_address, msg, logger)

    except Exception as e:
        logger.error(f"Error handling connection: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python peer.py <hostname> <next_peer_host> <calculator_host>")
        sys.exit(1)

    hostname = sys.argv[1]
    next_peer_host = sys.argv[2]
    calculator_host = sys.argv[3]
    port = 44422

    log = Logs(hostname)
    next_address = (next_peer_host, port)
    peer_node = PeerNode(next_address)

    print(f"Server starting at {hostname}:{port}")
    generate_requests(4, queue_)
    server_run(hostname, port, next_address, log.logger, (calculator_host, PORT_CALCULATOR))
