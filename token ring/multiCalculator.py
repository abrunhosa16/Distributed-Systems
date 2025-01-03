import socket
import logging
import threading

PORT: int = 12347

FORMAT: str = 'UTF-8'

def server(ADDR: tuple):
    server :socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    while True:
        try:
            client, addr  = server.accept()
            threading.Thread(target=handle_connection, args=(client, )).start()

        except Exception as e:
            print(f"Error connection {e}")

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

