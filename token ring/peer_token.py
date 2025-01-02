import socket  
import threading  
import logging 
import time 
import queue
from poissonEvents import generate_requests

PORT_CALCULATOR: int = 12345
FORMAT: str = 'UTF-8'
queue_ = queue.Queue()


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

# Function to start and run the server
def server_run(host: str, port: int, next_addr: tuple  , logger: logging.Logger, address_calculator):
    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((host, port))  # Bind the server to the specified host and port
    server.listen()  # Start listening for incoming connections (1 = max backlog)
    logger.info(f"Server: endpoint running at port {port} ...")  # Log server startup

    while True:
        try:
            client_socket: socket.socket
            addr: tuple[str, int]
            # Accept a new client connection
            client_socket, addr = server.accept()
            client_address: str = addr[0]  # Extract the client address
            logger.info(f"Server: new connection from {client_address}")  # Log the connection

            # Handle the connection in a separate thread
            threading.Thread(target=handle_connection, args=(client_socket, client_address, next_addr, logger, address_calculator)).start()

        except Exception as e:
            logger.error(f"Error accepting connection: {e}")  # Log any connection errors

# Function to handle individual client connections
def handle_connection(client: socket.socket, client_address: str, next_address: tuple[str, int], logger: logging.Logger, address_calculator):
    try:
        # Create input streams for the client connection
        msg: str = client.recv(1024).decode(FORMAT)
        logger.info(f"Server: message from host {client_address} [command = {msg}]")

        while not queue_.empty():
            calculator_server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            calculator_server.connect(address_calculator)
            try:
                item: str = queue_.get()
                calculator_server.send(item.encode(FORMAT))
                result: str= calculator_server.recv(1024).decode(FORMAT)
                logger.info(f"multiculator: message from calculator [result = {result}]")
                print(result)

            except Exception as e: 
                print(f"Error connect calculator {e}")

        next: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        next.connect(next_address)
        next.send(msg.encode(FORMAT))

    except Exception as e:
        logging.error(f"Error handling connection: {e}")  # Log any errors during connection handling
   

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 5:
        print("Usage: python peer.py <hostname> <port> <host_peer> <port_peer>")
        sys.exit(1)  

    hostname = sys.argv[1]  # Get hostname from arguments
    next = sys.argv[2]
    HOST_CALCULATOR = sys.argv([5])
    log = logs(hostname)



    print(f"New server @ host={hostname} - port={33333}")  # Inform user of peer initialization
    generate_requests(4, queue_)
    server_run(hostname, 33333, next, log.logger, (HOST_CALCULATOR, PORT_CALCULATOR))

