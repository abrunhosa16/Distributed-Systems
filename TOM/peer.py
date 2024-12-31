import socket 
import logging
import threading
import random 
import math 
import heapq
import pickle
import time 
lock = threading.Lock()
processed = set()


portuguese_cities = ["Lisboa",
    "Porto",
    "Coimbra",
    "Braga",
    "Aveiro",
    "Faro",
    "Serra da Estrela",
    "Guimarães",
    "Viseu",
    "Leiria",
    "Vale de Cambra",
    "Sintra",
    "Viana do Castelo",
    "Tondela",
    "Guarda",
    "Caldas da Rainha",
    "Covilhã",
    "Bragança",
    "Óbidos",
    "Vinhais",
    "Mirandela",
    "Freixo de Espada à Cinta",
    "Peniche"]

class PeerNode:
    def __init__(self, hostname, port, peers):
        self.hostname = hostname
        self.port = port
        self.peers = set(peers)
        self.priority_queue = []
        self.clock = 0
        self.ready_peers = set()  # To track "ready" peers

        self.logger = self._setup_logger()

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
    server.bind((node.hostname, node.port))
    server.listen()
    #logger.info(f"Server: endpoint running at port {port} ...")  # Log server startup

    while True:
        try:
            client_socket: socket.socket
            addr: tuple[str, int]
            client_socket, addr = server.accept()  # Accept a new client connection
            client_address: str = addr[0]  # Extract the client address
            #logger.info(f"Server: new connection from {client_address[0]}")  # Log the connection

            # Handle the connection in a separate thread
            threading.Thread(target=handle_connection, args=(client_socket, node, client_address)).start()
        
        except Exception as e:
            node.logger.error(f"Error accepting connection: {e}")  # Log any connection errors

def handle_connection(client: socket.socket, node: PeerNode, client_address):
    try:
        msg = client.recv(1024)
        received_data = pickle.loads(msg)

        # Check if it's a "ready" message
        if isinstance(received_data[1], str) and received_data[1] == "ready":
            with lock:
                node.ready_peers.add(received_data[0])
                node.logger.info(f"Received 'ready' message from {client_address}")
            return

        # Handle regular messages
        ip_peer, word, receiv_clock = received_data
        with lock:
            node.clock = max(node.clock, receiv_clock) + 1
            if word != 'ack':
                ack = pickle.dumps((node.hostname, 'ack', node.clock))
                sending_message(ack)

            heapq.heappush(node.priority_queue, (receiv_clock, (ip_peer, word)))
            print_message()
    except Exception as e:
        node.logger.error(f"Error handling connection from {client_address}: {e}")
 

def sending_message(message, retry_delay=2, max_retries=3, max_backoff=30):
    for peer in node.peers:
        attempts = 0
        while attempts < max_retries:
            try:
                # Use a context manager to ensure the socket is closed
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as next_sock:
                    logging.info(f"Attempting to connect to {peer}, try {attempts + 1}")
                    next_sock.connect((peer, node.port))
                    next_sock.sendall(message)
                    logging.info(f"Message sent successfully to {peer}")
                    break  # Exit the retry loop on successful send
            except socket.error as e:
                attempts += 1
                logging.warning(f"Attempt {attempts} failed for {peer}: {e}")
                
                if attempts < max_retries:
                    # Calculate backoff time (capped)
                    backoff = min(retry_delay * (2 ** attempts), max_backoff)
                    logging.info(f"Retrying in {backoff:.1f} seconds...")
                    time.sleep(backoff)
                else:
                    logging.error(f"Failed to send message to {peer} after {max_retries} attempts.")



def print_message():
    ips = set(map(lambda ip: ip[1][0], node.priority_queue))
    if node.peers.issubset(ips):
        while len(node.priority_queue) > 0:
            mes_clock, msg_info = heapq.heappop(node.priority_queue)
            if msg_info[1] != 'ack':
                print(mes_clock, msg_info)


     
def client():
    global lock
    with lock:
        node.clock += 1
        word = random.choice(list(portuguese_cities))  # Convert set to list for random.choice
        message = node.hostname, word, node.clock
        send_data = pickle.dumps(message)
        
        sending_message(send_data)


def periodic_send():
    def delay_poisson_messages():
        while True:
            delay = poisson_delay(1)
            time.sleep(delay)
            client()
    threading.Thread(target=delay_poisson_messages, daemon=True).start()


def send_ready_message(node: PeerNode):
    ready_message = pickle.dumps((node.hostname,"ready"))
    for peer in node.peers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((peer, node.port))
                sock.sendall(ready_message)
        except Exception as e:
            node.logger.warning(f"Failed to send 'ready' message to {peer}: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 3:
        print("Usage: python peer.py <hostname> <host_peers>")
        sys.exit(1)  

    hostname_ = sys.argv[1]  # Get hostname from arguments
    port_ = 55555
    peers_ = sys.argv[1:]
    peers_ = set(map(str, peers_))
    node = PeerNode(hostname= hostname_, port=port_, peers=peers_)

    print(f"Node initialized at {hostname_}:{port_}")
    threading.Thread(target=server_run, args=(node,), daemon=True).start()

    send_ready_message(node)

    while node.peers != node.ready_peers:
        print('ainda nao')
        time.sleep(1)
    

    # Wait until all peers are ready
    periodic_send()
    server_run(node)


    #print(f"New server @ host={hostname_} - port={port_}")  # Inform user of peer initialization
    #server_run(node)

