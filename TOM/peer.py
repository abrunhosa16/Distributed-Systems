import socket 
import logging
import threading
import random 
import math 
import heapq
import pickle
import time 

portuguese_cities = ["Lisboa", "Porto", "Coimbra", "Braga", "Aveiro", "Faro", "Serra da Estrela", "Guimarães", "Viseu", "Leiria", "Vale de Cambra", "Sintra", "Viana do Castelo", "Tondela", "Guarda", "Caldas da Rainha", "Covilhã", "Bragança", "Óbidos", "Vinhais", "Mirandela", "Freixo de Espada à Cinta", "Peniche"]   
    
class PeerNode:
    def __init__(self, hostname: str, peers: set[int], port:int = 55555):
        self.hostname = hostname
        self.port = port
        self.peers = peers
        self.priority_queue: heapq = [] # heap that acc words and acks
        self.clock: int = 0
        self.logger = self._setup_logger()
        self.connected_peers: set = set()
        self.shutdown_flag = threading.Event()  # Flag for clean shutdown

    def _setup_logger(self):
        logger = logging.getLogger(f"{self.hostname}_log")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"{self.hostname}_peer.log", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def poisson_delay(lambda_:int):
    return -math.log(1.0 - random.random()) / lambda_

def server_run(node: PeerNode):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable port reuse
    server.bind((node.hostname, node.port))
    server.listen()

    while True:
        try:
            server.settimeout(1)  # Set timeout to allow periodic checks for shutdown
            client_socket: socket.socket
            addr: tuple[str, int]
            client_socket, addr = server.accept()  # Accept a new client connection
            client_address: str = addr[0]  # Extract the client address

            # Handle the connection in a separate thread
            threading.Thread(target=handle_connection, args=(client_socket, node, client_address)).start()
        except socket.timeout:
            continue
        
        except Exception as e:
            node.logger.error(f"Error accepting connection: {e}")  # Log any connection errors

def handle_connection(client: socket.socket, node: PeerNode, client_address):
    try:
        msg = client.recv(1024)

        received_data = pickle.loads(msg)

        ip_peer, word, receiv_clock = received_data

        if word == 'shutdown':
            propagate_shutdown(node)
            client.close()
            sys.exit(0)

        if word == 'ready':
            node.connected_peers.add(ip_peer)
            return  
            
        node.clock = max(node.clock, receiv_clock) + 1
        if word != 'ack':
            ack = pickle.dumps((node.hostname, 'ack', node.clock))
            sending_message(ack)

        heapq.heappush(node.priority_queue, (receiv_clock, (ip_peer, word)))
        print_message()
    except Exception as e:
        node.logger.error(f"Error handling connection from {client_address}: {e}")

    finally:
        client.close()  # Always close the client socket


def propagate_shutdown(node: PeerNode):
    """Send a shutdown message to all peers and shut down the node."""
    shutdown_message = pickle.dumps((node.hostname, 'shutdown', node.clock))
    for peer in node.peers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((node.hostname, peer))
                sock.sendall(shutdown_message)
                node.logger.info(f"Sent shutdown signal to {peer}")
        except Exception as e:
            node.logger.warning(f"Failed to send shutdown signal to {peer}: {e}")
    
    # Set the shutdown flag and log the event
    node.logger.info("Shutting down this peer")
    node.shutdown_flag.set()
    sys.exit(0)

def sending_message(message, max_attempts = 10):
    for peer in node.peers: 
        attempts = 0
        while True:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((peer, node.port))
                client_socket.sendall(message)
                logging.info(f"Message sent successfully to {peer}")

                if peer not in node.connected_peers:
                    node.connected_peers.add(peer)
                    print(node.connected_peers)

                client_socket.close()
                break
            except socket.error as e:
                attempts+=1
                logging.warning(f"Attempts {attempts} failed for {peer}: {e}")
                time.sleep(3)
                if attempts > max_attempts:
                    node.connected_peers.remove(peer)
                    node.peers.remove(peer)
                    break

def print_message():
    ips = set(map(lambda ip: ip[1][0], node.priority_queue))
    if node.peers.issubset(ips):
        while len(node.priority_queue) > 0:
            curr_clock, (ip, msg) = heapq.heappop(node.priority_queue)
            if msg != 'ack':
                print(curr_clock, ip, msg)


def client(node: PeerNode):
    node.clock += 1
    word = random.choice(list(portuguese_cities))  # Convert set to list for random.choice
    message = node.hostname, word, node.clock
    send_data = pickle.dumps(message)
    sending_message(send_data)

def periodic_send(node: PeerNode):
    def send_poisson_messages():
        while not node.shutdown_flag.is_set():
            delay = poisson_delay(1)
            if node.peers.issubset(node.connected_peers):
                client(node)
                time.sleep(delay)
            else:
                time.sleep(0.4)
                sending = node.hostname, 'ready', 0
                sending_message(pickle.dumps(sending))
    threading.Thread(target=send_poisson_messages, daemon=True).start()


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 3:
        print("Usage: python peer.py <hostname> <host_peers>")
        sys.exit(1)  

    hostname_ = sys.argv[1]  # Get hostname from arguments
    peers_ = sys.argv[1:]
    peers_ = set(map(str, peers_))
    node = PeerNode(hostname= hostname_, peers=peers_)

    print(f"Node initialized at {hostname_}:{node.port}")

    periodic_send(node)
    server_run(node)

    

