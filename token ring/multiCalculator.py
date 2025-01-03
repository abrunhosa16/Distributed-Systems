import socket
import threading
import signal
import sys

PORT: int = 44429
FORMAT: str = 'UTF-8'

shutdown_event = threading.Event()


def signal_handler(sig, frame):
    """Handles SIGINT (Ctrl+C) to signal the server to shut down."""
    print("\nSIGINT received. Shutting down...")
    shutdown_event.set()

signal.signal(signal.SIGINT, signal_handler)


def server(ADDR: tuple):
    """Starts the server and listens for incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(ADDR)
    server_socket.listen()
    print(f"Server running at {ADDR[0]}:{ADDR[1]}")

    try:
        while not shutdown_event.is_set():
            try:
                server_socket.settimeout(1)  # Allows checking shutdown_event periodically
                client, addr = server_socket.accept()
                print(f"Connection from {addr}")
                threading.Thread(target=handle_connection, args=(client,)).start()
            except socket.timeout:
                continue  # Check for shutdown_event after timeout
            except Exception as e:
                print(f"Error accepting connection: {e}")
    finally:
        print("Closing server socket...")
        server_socket.close()


def handle_connection(client: socket.socket):
    """Handles communication with a single client."""
    try:
        msg = client.recv(1024).decode(FORMAT)
        print(f"Message received: {msg}")

        # Parse the message
        msg_parts = msg.split()
        if len(msg_parts) != 3:
            client.send("Invalid message format".encode(FORMAT))
            return

        op, x, y = msg_parts[0], int(msg_parts[1]), int(msg_parts[2])
        result = calculator(op, x, y)
        response = str(result)

        client.send(response.encode(FORMAT))
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        print("Closing client socket...")
        client.close()


def calculator(op: str, x: int, y: int) -> int:
    """Performs basic arithmetic operations."""
    if op == 'add':
        return x + y
    elif op == 'sub':
        return x - y
    elif op == 'mul':
        return x * y
    elif op == 'div':
        return x // y if y != 0 else 0
    else:
        return 0  # Default return for unsupported operations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python multiCalculator.py <SERVER_HOST>")
        sys.exit(1)

    SERVER = sys.argv[1]
    ADDR = (SERVER, PORT)
    print(f"Starting server @ host={SERVER}, port={PORT}")
    server(ADDR)
