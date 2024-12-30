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
my_set: dict
my_set = dict()

def poisson_delay(lambda_:int):
    return -math.log(1.0 - random.random()) / (lambda_/60)

def delay_poisson(lambda_: int):
    return poisson_delay(lambda_)

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

def merge_set(dic1, dic2):
    merged = dic1
    for key in dic2:
        if key in merged:
            merged[key] = max(dic1[key], dic2[key])
        else:
            merged[key] = dic2[key]
    return merged

def dictionary_operations(dic: dict[str, float], server_port: int) -> dict[str, float]:
    current_time = time.time()  # Captura o tempo atual uma vez
    # Usa compreensão de dicionário para filtrar valores dentro do intervalo DELTA
    cop = {key: value for key, value in dic.items() if current_time - value <= DELTA}
    
    # Adiciona o servidor atual com o tempo atual
    cop[server_port] = current_time
    
    # Exibe a diferença de tempo para cada chave
    for key, value in dic.items():
        print(f"{key}: {current_time - value}")
    
    return cop


def server_run(host: str, port: int, neighboors: set[int] , logger: logging.Logger):
    global my_set

    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((host, port))  # Bind the server to the specified host and port
    server.listen()  # Start listening for incoming connections 
    logger.info(f"Server: endpoint running at port {port} ...")  # Log server startup


    initial_time: time.time
    initial_time = time.time()
    my_set[port] = initial_time

    for neigh in neighboors:
        my_set[neigh] = initial_time # Dict indicating the current peer and the neighboors

    while True:
        try:
            client_socket: socket.socket
            addr: tuple[str, int]
            client_socket, addr = server.accept()  # Accept a new client connection
            client_address: str = addr[0]  # Extract the client address
            logger.info(f"Server: new connection from {client_address[0]}")  # Log the connection

            # Handle the connection in a separate thread
            threading.Thread(target=handle_connection, args=(client_socket, client_address, neighboors, logger, port)).start()
        

        except Exception as e:
            logger.error(f"Error accepting connection: {e}")  # Log any connection errors



def gossip_algorithm(port, neighboors):
    global my_set
    my_set = dictionary_operations(my_set, port)

    message = pickle.dumps(my_set)

    for port_peer in neighboors:
            try:
                print(f"{my_set} sended to {port_peer}")
                next: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                next.connect((hostname, port_peer))
                next.sendall(message)
            except Exception as e:
                logging.error(f"Error trying connect: {e} {port_peer}")



def sending_message(port, neighboors):
    def starting_algorithm(port, neighboors):
        global my_set
        delay = poisson_delay(2)
        time.sleep(delay)
        gossip_algorithm(port, neighboors)
        print(f"Set was send {my_set}")
    threading.Thread(target=starting_algorithm, args=(port, neighboors, ))

        



    
# Function to handle individual client connections
def handle_connection(client: socket.socket, client_address: str, neighboors: set[int], logger: logging.Logger, server_port:int):
    global my_set  # Declare my_set as global

    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024)
        received_set = pickle.loads(msg)  # load the dict that came from another peer.

        logger.info(f"Server: message from host {client_address} [command = {received_set}]")
        print(f"{received_set} received from {client_address}")

        my_set = merge_set(my_set, received_set)


        my_set = dictionary_operations(my_set, server_port) 
        send_data = pickle.dumps(my_set) # preparing dict to send for the neighboors
        
        # Creating connection with all neighboors
        '''Probably i need to put a exception here, and is important put more logs.'''
        for port_peer in neighboors:
            try:
                print(f"{my_set} sended to {port_peer}")
                next: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                next.connect((hostname, port_peer))
                next.sendall(send_data)
            except Exception as e:
                logging.error(f"Error trying connect: {e} {port_peer}")

    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling
   

if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 3:
        print("Usage: python peer.py <hostname> <port> <ports_peer>")
        sys.exit(1)  

    hostname = sys.argv[1]  # Get hostname from arguments
    port = int(sys.argv[2])  # Get port from arguments
    neighboors = sys.argv[3:]
    neighboors = set(map(int, neighboors))
    log = logs(hostname)


    print(f"New server @ host={hostname} - port={port}")  # Inform user of peer initialization
    server_run(hostname, port, neighboors, log.logger)





