import socket
import threading
import logging
import queue
import signal
import sys
from typing import Tuple
from poissonEvents import generate_requests
import time

FORMAT = 'UTF-8'
    
# Represents a peer in the network, storing its local address, the next peer's address, and the calculator server's address, queue and shutdown command.
class PeerNode:
    def __init__(self, hostname: str, port:int , next_address: Tuple[str, int], host_calculator:str):
        self.next_address = next_address
        self.calculator_address = host_calculator, port
        self.host = hostname
        self.port = port
        self.server_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.queue_ = queue.Queue()
        self.shutdown_event = threading.Event() 

class Logs:
    def __init__(self, hostname: str):
        self.logger = logging.getLogger("logfile")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"./{hostname}_peer.log", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

#Captures the SIGINT signal (Ctrl+C) and starts the shutdown process for the server and connected peers.
def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    peer_node.shutdown_event.set() 
    propagate_shutdown(peer_node)

signal.signal(signal.SIGINT, signal_handler)

# Sends a shutdown command ("shut") to the next peer in the network and closes the local server's socket.
def propagate_shutdown(peer: PeerNode):
    print("Propagating shutdown...")
    try:
        next_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        next_socket.connect(peer.next_address)
        next_socket.send("shut".encode(FORMAT))
        
    except Exception as e:
        print(f"Failed to send shutdown signal to {peer.next_address}: {e}")

    finally:
        print('server is closed')
        peer.server_socket.close()

# Processes items in the queue by sending them to a calculator server and print the received results.
def process_queue(node: PeerNode, logger: Logs):
    while not node.queue_.empty():
        calculator_server=  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            calculator_server.connect(node.calculator_address)
            item = node.queue_.get()
            calculator_server.send(item.encode(FORMAT))
            result = calculator_server.recv(1024).decode(FORMAT)
            print(result)
        except Exception as e:
            logger.error(f"Error connecting to calculator: {e}")
            propagate_shutdown(node)
            return
    
# Forwards a received message to the next peer in the network.
def forward_message(next_address: Tuple[str, int], msg: str, logger: logging.Logger, max_attempts = 3):
    attempts = 0
    while True:
        try:
            next_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            next_socket.connect(next_address)
            next_socket.send(msg.encode(FORMAT))
            logger.info(f"Message forwarded to {next_address}: {msg}")
            break
        except Exception as e:
            attempts+=1
            print(f"Attempts {attempts} failed for {next_address}: {e}, trying again in 3 seconds ...")
            time.sleep(3)
            if attempts > max_attempts:
                propagate_shutdown(peer_node)
                break

# Starts the server socket to listen for peer connections and manages connections in separate threads.
def server_run(logger: logging.Logger, peer_node: PeerNode):
    server = peer_node.server_socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((peer_node.host, peer_node.port))
    server.listen()
    logger.info(f"Server running at {peer_node.host}:{peer_node.port}")
    while not peer_node.shutdown_event.is_set():
        try:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_connection, args=(client_socket, addr, logger, peer_node)).start()
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")    

# Handles an incoming connection:
    # - Processes the client's message.
    # - Propagates shutdown if the message is "shut".
    # - Processes the message queue and forwards messages to the next peer.
def handle_connection(client: socket.socket, client_address: Tuple[str, int], logger: logging.Logger, peer_node: PeerNode):
    try:
        msg = client.recv(1024).decode(FORMAT)
        logger.info(f"Received message from {client_address}: {msg}")

        if msg == "shut":
            peer_node.shutdown_event.set()
            propagate_shutdown(peer_node)
            return

        process_queue(peer_node, logger)
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
    port = 50000
    next_peer_host = sys.argv[2]
    next_address_ = (next_peer_host, port)

    calculator_host = sys.argv[3]

    log = Logs(hostname)
    peer_node = PeerNode(hostname= hostname, port= port, next_address= next_address_, host_calculator= calculator_host)

    print(f"Server starting at {hostname}:{port}")
    # generate and put in a queue following a poisson distribution.
    generate_requests(4, peer_node.queue_)
    server_run(log.logger, peer_node)
