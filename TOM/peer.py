import socket 
import logging
import threading
import random 
import math 
import heapq
import pickle
import time 

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

def server_run(host: str, port: int, logger: logging.Logger):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((host, port))
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
            threading.Thread(target=handle_connection, args=(client_socket, client_address, logger)).start()
        
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")  # Log any connection errors

# Function to handle individual client connections
def handle_connection(client: socket.socket,  client_address, logger):
    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024)
        received_word = pickle.loads(msg)  # load the dict that came from another peer.
        ip_peer, word, receiv_clock = received_word
        node.clock = max(node.clock, receiv_clock) + 1

        '''bleat to everyone'''
        if word != 'ack':
            ack = pickle.dumps((node.hostname, 'ack', node.clock))
            sending_message(ack)

        heapq.heappush(node.priority_queue, (receiv_clock, (ip_peer, word)))
        #logger.info(f"Server: message from host {client_address} [command = {received_word}]")
        print_message()
    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling   

def sending_message(message, retry_delay=4):
    for peer in node.peers:
        attempts = 0
        while attempts < 10:
            try:
                logging.info(f"{message} sent to {peer}, attempt {attempts + 1}")
                next_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                next_sock.connect((peer, node.port))
                next_sock.sendall(message)
                next_sock.close()
                break
            except Exception as e:
                attempts += 1
                logging.error(f"Attempt {attempts} failed to connect to {peer}: {e}")
                time.sleep(retry_delay)  # Wait before retrying


def print_message():
    ips = set(map(lambda values: values[1][0], node.priority_queue))
    while ips.issubset(node.peers):
        value = heapq.heappop(node.priority_queue)
        if value[1][1] != 'ack':
            print(value)
            
def client():
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 3:
        print("Usage: python peer.py <hostname> <port> <ports_peer>")
        sys.exit(1)  

    hostname = sys.argv[1]  # Get hostname from arguments
    port = 55555
    peers = sys.argv[1:]
    peers = set(map(str, peers))
    node = PeerNode(hostname= hostname, port=port, peers=peers)

    print(f"New server @ host={hostname} - port={port}")  # Inform user of peer initialization
    periodic_send()
    server_run(node.hostname, node.port, node.logger)

