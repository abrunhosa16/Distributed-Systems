import socket 
import logging
import threading
import time 
import pickle
import math
import random 

'''
<+ Create a network of 6 peers (p1 to p6), running on different machines (m1 to m6), with
the topology shown in the figure above.
* Peers must have a thread waiting for others to connect and register themselves. This is
how peers get to know each other and the network is built.

* Each peer keeps a map data structure (e.g., Map or HashMap in Java) with the
IPs/names of the machines of the peers that have registered themselves with it. For
example, peer p2 (in machine m2) keeps the entries [m1, m3, m4] whereas peer p6 (in
machine m6) keeps only [m4].

* Now implement the Anti-Entropy Algorithm so peers can disseminate their maps. Each
peer updates its map twice per minute following a Poisson distribution, each time printing the number of peers in the updated map.

* Once the dissemination algorithm starts, the number of items in the map at each peer
will approximate the total number of peers in the network.

* What happens to the number of peers if you remove some of them from the above
network, e.g., killing the processes? Devise a scheme that handles this situation (hint:
you can use timestamps for the map entries and remove entries older than a given
threshold).

'''
# MAXIMUM TIME WITHOUT UPDATE
DELTA = 60   

def poisson_delay(lambda_:int):
    return -math.log(1.0 - random.random()) / (lambda_/60)

def delay_poisson(lambda_: int):
    return poisson_delay(lambda_)

def merge_set(recv_set):
    merged = peer_node.my_set
    for key in recv_set:
        if key in merged:
            merged[key] = max(peer_node.my_set[key], recv_set[key])
        else:
            merged[key] = recv_set[key]

    peer_node.my_set = merged

def dictionary_operations():
    current_time = time.time()  # Captura o tempo atual uma vez
    # Usa compreensão de dicionário para filtrar valores dentro do intervalo DELTA
    peer_node.my_set = {key: value for key, value in peer_node.my_set.items() if current_time - value <= DELTA}
    
    # Adiciona o servidor atual com o tempo atual
    peer_node.my_set[peer_node.host] = current_time
    
class PeerNode:
    def __init__(self, hostname: str, port: int, neighboors):
        self.host = hostname
        self.port = port 
        self.my_set = dict()
        self.neighboors = set(map(str, neighboors))
        
class logs:
    def __init__(self, hostname: str):
        self.host: str = hostname
        self.logger: logging.Logger = logging.getLogger("logfile")
        self.logger.setLevel(logging.INFO)
        try:
            handler = logging.FileHandler(f"./{hostname}_peer.log", mode="a")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception as e:
            print(f"Error setting up logger: {e}")

def server_run(logger: logging.Logger):

    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((peer_node.host, peer_node.port))  # Bind the server to the specified host and port
    server.listen()  # Start listening for incoming connections 
    logger.info(f"Server: endpoint running at port {peer_node.port} ...")  # Log server startup

    initial_time: time.time
    initial_time = time.time()
    peer_node.my_set[peer_node.host] = initial_time

    for neigh in peer_node.neighboors:
        peer_node.my_set[neigh] = initial_time # Dict indicating the current peer and the neighboors

    while True:
        try:
            client_socket: socket.socket
            addr: tuple[str, int]
            client_socket, addr = server.accept()  # Accept a new client connection
            client_address: str = addr[0]  # Extract the client address
            logger.info(f"Server: new connection from {client_address[0]}")  # Log the connection

            # Handle the connection in a separate thread
            threading.Thread(target=handle_connection, args=(client_socket, client_address, logger)).start()
    
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")  # Log any connection errors

    
# Function to handle individual client connections
def handle_connection(client: socket.socket, client_address: str, logger: logging.Logger):
    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024)
        received_set = pickle.loads(msg)  # load the dict that came from another peer.

        logger.info(f"Server: message from host {client_address} [command = {received_set}]")
        #print(f"{received_set} received from {client_address}")

        merge_set(received_set)

        print(peer_node.my_set)

    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling

def start_anti_entropy():
    """
    Periodically updates the peer map using Anti-Entropy.
    """
    def anti_entropy_cycle():
        while True:
            delay = delay_poisson(4)
            print(f"delay {delay}")
            time.sleep(delay)
            gossiping_message()

    threading.Thread(target=anti_entropy_cycle, daemon=True).start()

def gossiping_message():
    
    dictionary_operations()
    send_data = pickle.dumps(peer_node.my_set)
    for neigh in peer_node.neighboors:
        try:
            print(f"{peer_node.my_set} sended to {neigh}")
            next: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            next.connect((neigh, peer_node.port))
            next.sendall(send_data)
        except Exception as e:
            logging.error(f"Error trying connect: {e} {neigh}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 2:
        print("Usage: python peer.py <hostname> <port> <ports_peer>")
        sys.exit(1)  

    hostname = sys.argv[1]  # Get hostname from arguments
    port = 22222  # Get port from arguments
    neighboors = sys.argv[2:]
    log = logs(hostname)

    peer_node = PeerNode(hostname= hostname, port= port, neighboors= neighboors)

    print(f"New server @ host={hostname} - port={port}")  # Inform user of peer initialization
    start_anti_entropy()
    server_run(log.logger)





