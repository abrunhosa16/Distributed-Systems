import socket
import threading
import logging
import queue
import signal
import sys
from typing import Tuple
from poissonEvents import generate_requests

FORMAT = 'UTF-8'
queue_ = queue.Queue()
shutdown_event = threading.Event() 


class PeerNode:
    def __init__(self, hostname: str, port:int , next_address: Tuple[str, int], host_calculator:str, port_calculator:int = 12346):
        self.next_address = next_address
        self.calculator_address = host_calculator, port_calculator
        self.host = hostname
        self.port = port
        self.server_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    shutdown_event.set() 
    propagate_shutdown(peer_node)

signal.signal(signal.SIGINT, signal_handler)

class Logs:
    def __init__(self, hostname: str):
        self.logger = logging.getLogger("logfile")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"./{hostname}_peer.log", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

def propagate_shutdown(peer: PeerNode):
    print("Propagating shutdown...")
    try:
        next_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        next_socket.connect(peer.next_address)
        next_socket.send("shut".encode(FORMAT))
        
    except Exception as e:
        print(f"Failed to send shutdown signal to {peer.next_address}: {e}")
    
    print('server is closed')
    peer.server_socket.close()


def process_queue(address_calculator, logger):
    while not queue_.empty():
        calculator_server=  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            calculator_server.connect(address_calculator)
            item = queue_.get()
            calculator_server.send(item.encode(FORMAT))
            result = calculator_server.recv(1024).decode(FORMAT)
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


def server_run(logger: logging.Logger, peer_node: PeerNode):
    server = peer_node.server_socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((peer_node.host, peer_node.port))
    server.listen()
    logger.info(f"Server running at {peer_node.host}:{peer_node.port}")
    while not shutdown_event.is_set():
        try:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_connection, args=(client_socket, addr, logger, peer_node)).start()
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")    


def handle_connection(client: socket.socket, client_address: Tuple[str, int], logger: logging.Logger, peer_node: PeerNode):
    try:
        msg = client.recv(1024).decode(FORMAT)
        logger.info(f"Received message from {client_address}: {msg}")

        if msg == "shut":
            shutdown_event.set()
            propagate_shutdown(peer_node)
            return

        process_queue(peer_node.calculator_address, logger)
        forward_message(peer_node.next_address, msg, logger)

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
    next_address_ = (next_peer_host, port)
    peer_node = PeerNode(hostname= hostname, port= port, next_address= next_address_, host_calculator= calculator_host)

    print(f"Server starting at {hostname}:{port}")
    generate_requests(4, queue_)
    server_run(log.logger, peer_node)
