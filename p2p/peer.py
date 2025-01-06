import socket 
import logging
import threading
import time 
import pickle
import math
import random 
import signal 

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
DELTA = 90  

# Periodically calculates a delay for Anti-Entropy updates using a Poisson distribution.
def poisson_delay(lambda_:int):
    return -math.log(1.0 - random.random()) / (lambda_/60)

# Merges a received set of peers into the current peer's map, updating timestamps where necessary.
def merge_set(recv_set):
    merged = peer_node.my_set
    for key in recv_set:
        if key in merged:
            merged[key] = max(peer_node.my_set[key], recv_set[key])
        else:
            merged[key] = recv_set[key]

    peer_node.my_set = merged

# Removes outdated entries from the peer's map and updates its own timestamp.
def dictionary_operations():
    current_time = time.time() 
    peer_node.my_set = {key: value for key, value in peer_node.my_set.items() if current_time - value <= DELTA}
    peer_node.my_set[peer_node.host] = current_time
    
class PeerNode:
    def __init__(self, hostname: str, port: int, neighboors):
        self.host = hostname
        self.port = port 
        self.my_set = dict()
        self.neighboors = set(map(str, neighboors))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.shutdown_flag = threading.Event()
        
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

# Handles server-side logic, listens for incoming connections, and updates the peer map based on received data.
def server_run(logger: logging.Logger):
    server = peer_node.server_socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((peer_node.host, peer_node.port))  # Bind the server to the specified host and port
    server.listen()  # Start listening for incoming connections 
    logger.info(f"Server: endpoint running at port {peer_node.port} ...")  # Log server startup

    initial_time: time.time
    initial_time = time.time()
    peer_node.my_set[peer_node.host] = initial_time

    for neigh in peer_node.neighboors:
        peer_node.my_set[neigh] = initial_time # Dict indicating the current peer and the neighboors

    try:
        while not peer_node.shutdown_flag.is_set():
            try:
                server.settimeout(1)  # Allows checking shutdown_event periodically
                client_socket: socket.socket
                addr: tuple[str, int]
                client_socket, addr = server.accept()  # Accept a new client connection
                client_address: str = addr[0]  # Extract the client address
                logger.info(f"Server: new connection from {client_address[0]}")  # Log the connection
                # Handle the connection in a separate thread
                threading.Thread(target=handle_connection, args=(client_socket, client_address, logger)).start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")  # Log any connection errors
            except socket.timeout:
                continue  # Check for shutdown_event after timeout
    finally:
        print('Server is closed')
        server.close()

    
# Handles communication with a single peer, processes received data, and updates the map.
def handle_connection(client: socket.socket, client_address: str, logger: logging.Logger):
    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024)
        op, received_set = pickle.loads(msg)  # load the dict that came from another peer.

        if op == 'pull':
            merge_set(received_set)
            dictionary_operations()
            msg = pickle.dumps(('push', peer_node.my_set))
            client.sendall(msg)
            print(f'my current set after pull {peer_node.my_set}')
            return
        
        if op == 'push':
            merge_set(received_set)
            print(f'after push my set {peer_node.my_set}')
            return

        logger.info(f"Server: message from host {client_address} [command = {received_set}]")
        #print(f"{received_set} received from {client_address}")



    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling

    finally:
        client.close()

# Periodically triggers Anti-Entropy updates by sending the current map to neighbors.
def start_anti_entropy():
    """
    Periodically updates the peer map using Anti-Entropy.
    """
    def anti_entropy_cycle():
        while True:
            delay = poisson_delay(2)
            time.sleep(delay)
            gossiping_message()

    threading.Thread(target=anti_entropy_cycle, daemon=True).start()

# Sends the peer's current map to all neighbors as part of the Anti-Entropy algorithm.
def gossiping_message(max_attempts = 3):
    dictionary_operations()  # Cleans up outdated entries and updates the timestamp
    send_data = pickle.dumps(('pull', peer_node.my_set))
    neigh = random.choice(list(peer_node.neighboors))
    attempts = 0
    while True:
        try:
            print(f"{peer_node.my_set} sended to {neigh}")
            next: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            next.connect((neigh, peer_node.port))
            next.sendall(send_data)
            break
        except Exception as e:
            attempts+=1
            print(f"Attempts {attempts} failed for {neigh}: {e}, trying again in 3 seconds ...")
            time.sleep(3)
            if attempts > max_attempts:
                break

#Captures the SIGINT signal (Ctrl+C) and starts the shutdown process for the server and connected peers.
def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    peer_node.shutdown_flag.set() 

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 2:
        print("Usage: python peer.py <hostname> <port> <ports_peer>")
        sys.exit(1)  

    hostname = sys.argv[1]  # Get hostname from arguments
    port = 50000  # Get port from arguments
    neighboors = sys.argv[2:]
    log = logs(hostname)

    peer_node = PeerNode(hostname= hostname, port= port, neighboors= neighboors)

    print(f"New server @ host={hostname} - port={port}")  # Inform user of peer initialization
    start_anti_entropy()
    server_run(log.logger)





