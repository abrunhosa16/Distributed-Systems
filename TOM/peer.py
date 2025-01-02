import socket
import logging
import threading
import random
import math
import heapq
import pickle
import time
import signal
import sys

portuguese_cities = ["Lisboa", "Porto", "Coimbra", "Braga", "Aveiro", "Faro", "Serra da Estrela", "Guimarães", "Viseu", 
                     "Leiria", "Vale de Cambra", "Sintra", "Viana do Castelo", "Tondela", "Guarda", "Caldas da Rainha", 
                     "Covilhã", "Bragança", "Óbidos", "Vinhais", "Mirandela", "Freixo de Espada à Cinta", "Peniche"]


class PeerNode:
    def __init__(self, hostname: str, peers: set, port: int = 55550):
        self.hostname = hostname
        self.port = port
        self.peers = peers
        self.priority_queue = []  # Heap to store messages
        self.clock = 0
        self.logger = self._setup_logger()
        self.connected_peers = set()
        self.shutdown_flag = threading.Event()  # Flag for clean shutdown

    def _setup_logger(self):
        logger = logging.getLogger(f"{self.hostname}_log")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"{self.hostname}_peer.log", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    propagate_shutdown(node)


signal.signal(signal.SIGINT, signal_handler)


def poisson_delay(lambda_: int):
    return -math.log(1.0 - random.random()) / lambda_


def server_run(node: PeerNode):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((node.hostname, node.port))
    server.listen()

    try:
        node.logger.info(f"Server started on {node.hostname}:{node.port}")
        while not node.shutdown_flag.is_set():
            try:
                server.settimeout(1.0)  # Timeout to periodically check for shutdown
                client_socket, addr = server.accept()
                threading.Thread(target=handle_connection, args=(client_socket, node, addr[0])).start()
            except socket.timeout:
                continue
            except Exception as e:
                if node.shutdown_flag.is_set():
                    break
                node.logger.error(f"Error accepting connection: {e}")
    finally:
        server.close()
        node.logger.info("Server socket closed.")


def handle_connection(client: socket.socket, node: PeerNode, client_address: str):
    try:
        msg = client.recv(1024)
        if not msg:
            return
        received_data = pickle.loads(msg)
        ip_peer, word, receiv_clock = received_data

        if word == 'shutdown':
            node.logger.info(f"Shutdown message received from {ip_peer}.")
            node.shutdown_flag.set()
            return

        if word == 'ready':
            node.connected_peers.add(ip_peer)
            return

        node.clock = max(node.clock, receiv_clock) + 1
        if word != 'ack':
            ack = pickle.dumps((node.hostname, 'ack', node.clock))
            sending_message(node, ack)

        heapq.heappush(node.priority_queue, (receiv_clock, (ip_peer, word)))
        print_message(node)
    except Exception as e:
        node.logger.error(f"Error handling connection from {client_address}: {e}")
    finally:
        client.close()


def propagate_shutdown(node: PeerNode):
    shutdown_message = pickle.dumps((node.hostname, 'shutdown', node.clock))
    for peer in node.peers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((peer, node.port))
                sock.sendall(shutdown_message)
                node.logger.info(f"Sent shutdown signal to {peer}")
        except Exception as e:
            node.logger.warning(f"Failed to send shutdown signal to {peer}: {e}")

    node.shutdown_flag.set()


def sending_message(node: PeerNode, message, max_attempts=10):
    for peer in node.peers:
        attempts = 0
        while attempts < max_attempts:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((peer, node.port))
                    client_socket.sendall(message)
                    node.logger.info(f"Message sent successfully to {peer}")
                    if peer not in node.connected_peers:
                        node.connected_peers.add(peer)
                    break
            except socket.error as e:
                attempts += 1
                node.logger.warning(f"Attempt {attempts} failed for {peer}: {e}")
                time.sleep(3)


def print_message(node: PeerNode):
    ips = set(map(lambda ip: ip[1][0], node.priority_queue))
    if node.peers.issubset(ips):
        while len(node.priority_queue) > 0:
            curr_clock, (ip, msg) = heapq.heappop(node.priority_queue)
            if msg != 'ack':
                print(curr_clock, ip, msg)


def client(node: PeerNode):
    node.clock += 1
    word = random.choice(portuguese_cities)
    message = (node.hostname, word, node.clock)
    send_data = pickle.dumps(message)
    sending_message(node, send_data)


def periodic_send(node: PeerNode):
    def send_poisson_messages():
        while not node.shutdown_flag.is_set():
            delay = poisson_delay(1)
            if node.peers.issubset(node.connected_peers):
                client(node)
                time.sleep(delay)
            else:
                time.sleep(0.4)
                sending = (node.hostname, 'ready', 0)
                sending_message(node, pickle.dumps(sending))

    threading.Thread(target=send_poisson_messages, daemon=True).start()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Usage: python peer.py <hostname> <peer1> <peer2> ...")
        sys.exit(1)

    hostname_ = sys.argv[1]
    peers_ = set(sys.argv[2:])
    node = PeerNode(hostname=hostname_, peers=peers_)

    print(f"Node initialized at {hostname_}:{node.port}")

    periodic_send(node)
    server_run(node)
