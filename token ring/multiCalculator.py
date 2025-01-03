import socket
import logging
import threading
import signal

PORT: int = 44426

FORMAT: str = 'UTF-8'

shutdown_event = threading.Event()


def signal_handler(sig, frame):
    print("\nSIGINT received. Shutting down...")
    shutdown_event.set() 

signal.signal(signal.SIGINT, signal_handler)

def server(ADDR: tuple):
    server :socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    try:
        while not shutdown_event.is_set():
            try:
                client, addr  = server.accept()
                threading.Thread(target=handle_connection, args=(client, )).start()

            except Exception as e:
                print(f"Error connection {e}")
    finally:
        server.close()
        print('Server is closed')
    

def handle_connection(client:socket.socket):
    try:
        msg: str = client.recv(1024).decode(FORMAT)
        print(f"mensagem {msg}")
        msg: list[str] = msg.split()
        op = msg[0]
        x = int(msg[1])
        y = int(msg[2])

        result: int = calculator(op, x, y)
        msg: str = str(result).encode(FORMAT)

        client.send(msg)

    except Exception as e:
        print(f"handle connection error {e}")
    
    
def calculator(op: str, x: int, y: int) -> int:
    if op == 'add':
        return x + y
    elif op == 'sub':
        return x - y
    elif op == 'mul':
        return x * y
    elif op == 'div':
        return x / y if y != 0 else 0
    else: 
        return 


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 1:
        print("Usage: python multiCalculator.py")
        sys.exit(1) 

    SERVER = sys.argv[1]
    print(f"New server @ host={SERVER} - port={PORT}")  # Inform user of peer initialization
    ADDR = SERVER, PORT
    server(ADDR)

