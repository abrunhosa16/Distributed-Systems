import socket 
import logging
import threading
import random 
import math 
import heapq
import pickle
import time 

priority_queue = []
clock = 0

australian_animals = {
    "kangaroo",
    "koala",
    "wombat",
    "platypus",
    "echidna",
    "emu",
    "crocodile",
    "tasmanian_devil",
    "wallaby",
    "cassowary",
    "dingo",
    "quokka",
    "bandicoot",
    "bilby",
    "sugar_glider",
    "lyrebird",
    "cockatoo",
    "kookaburra",
    "goanna",
    "frilled_lizard",
    "fairy_penguin",
    "numbat",
    "tree_kangaroo",
    "spotted_quoll",
    "thorny_devil"
}

def poisson_delay(lambda_:int):
    return -math.log(1.0 - random.random()) / lambda_

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
    global clock
    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024)
        received_word = pickle.loads(msg)  # load the dict that came from another peer.
        ip_peer, word, receiv_clock = received_word
        clock = max(clock, receiv_clock) + 1

        '''bleat to everyone'''
        if word != 'ack':
            ack = pickle.dumps((port, 'ack', clock))
            sending_message(ack)

        heapq.heappush(priority_queue, (receiv_clock, (ip_peer, word)))
        #logger.info(f"Server: message from host {client_address} [command = {received_word}]")
        print_message()
    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling   

def sending_message(message, retry_delay=4):
    for peer in peers:
        attempts = 0
        while attempts < 3:
            try:
                logging.info(f"{message} sent to {peer}, attempt {attempts + 1}")
                next_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                next_sock.connect((peer, port))
                next_sock.sendall(message)
                next_sock.close()
                break
            except Exception as e:
                attempts += 1
                logging.error(f"Attempt {attempts} failed to connect to {peer}: {e}")
                if attempts < 3:
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    logging.error(f"Failed to connect to {peer} after 3 attempts.")


def print_message():
    print('oi1')
    ips = set(map(lambda values: values[1][0], priority_queue))
    if peers.issubset(ips):
        print('oi2')

        while len(priority_queue) > 0:
            print('oi3')
            value = heapq.heappop(priority_queue)
            if value[1][1] != 'ack':
                print(value)
            
def client():
    global clock
    clock += 1
    word = random.choice(list(australian_animals))  # Convert set to list for random.choice
    message = hostname, word, clock
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
    log = logs(hostname)

    print(f"New server @ host={hostname} - port={port}")  # Inform user of peer initialization
    periodic_send()
    server_run(hostname, port, log.logger)

