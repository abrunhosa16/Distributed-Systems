import socket
import threading
import json
import os
import signal
import sys
import random
import math
from queue import PriorityQueue

lambda_value = 1
neighbors_map = {}
lamport_clock = 0
queue = PriorityQueue()

words_array = [
    "Air Ball", "Alley-oop", "Assist", "Backboard", "Backcourt", "Bank Shot",
    "Baseline", "Bench", "Block", "Bounce Pass", "Box Out", "Charging",
    "Chest Pass", "Double Dribble", "Dribble", "Dunk", "Fast Break",
    "Field Goal", "Flagrant Foul", "Free Throw", "Full-Court Press",
    "Goaltending", "Half-Court", "Inbounds Pass", "Jump Ball", "Layup",
    "Man-to-Man Defense", "Offense", "Overtime", "Personal Foul", "Pivot",
    "Rebound", "Screen", "Shot Clock", "Slam Dunk", "Steal",
    "Technical Foul", "Three-Point Line", "Traveling", "Turnover", "Zone Defense"
]

self_ip = None

def start_peer_server(ip_address, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip_address, port))
    server.listen()

    print(f"Server running on {ip_address}:{port}")

    def handle_client(client_socket, connection_ip):
        global lamport_clock

        if connection_ip not in neighbors_map:
            print(f"ADDED NEIGHBOR: {connection_ip}")
            neighbors_map[connection_ip] = client_socket
        else:
            client_socket.close()
            return

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                messages = data.decode().strip().split('\n')
                for message in messages:
                    handle_incoming_message(message, connection_ip)
        except Exception as e:
            print(f"Client socket error: {e}")
        finally:
            print(f"REMOVED NEIGHBOR: {connection_ip}")
            neighbors_map.pop(connection_ip, None)
            client_socket.close()

    def accept_clients():
        while True:
            client_socket, client_address = server.accept()
            connection_ip = client_address[0]
            threading.Thread(target=handle_client, args=(client_socket, connection_ip)).start()

    threading.Thread(target=accept_clients, daemon=True).start()
    return server

def setup_persistent_socket(peer_ip, peer_port, retry_delay=2, max_retries=5):
    retries = 0

    while retries <= max_retries:
        try:
            if peer_ip in neighbors_map:
                return
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, peer_port))
            print(f"ADDED NEIGHBOR: {peer_ip}")
            neighbors_map[peer_ip] = client_socket

            def listen_to_peer():
                try:
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        messages = data.decode().strip().split('\n')
                        for message in messages:
                            handle_incoming_message(message, peer_ip)
                except Exception as e:
                    print(f"Error with peer {peer_ip}: {e}")
                finally:
                    print(f"REMOVED NEIGHBOR: {peer_ip}")
                    neighbors_map.pop(peer_ip, None)
                    client_socket.close()

            threading.Thread(target=listen_to_peer, daemon=True).start()
            return
        except Exception:
            retries += 1
            if retries > max_retries:
                print(f"Failed to connect to {peer_ip}")
            else:
                threading.Event().wait(retry_delay)

def graceful_shutdown(signal_received=None, frame=None):
    print("Shutting down gracefully...")
    send_message("SHUTDOWN")
    neighbors_map.clear()
    sys.exit(0)

def handle_incoming_message(message, peer_ip):
    global lamport_clock

    msg_data = json.loads(message)
    text, clock = msg_data["text"], msg_data["clock"]
    lamport_clock = max(lamport_clock, clock) + 1

    if text == "SHUTDOWN":
        print("Received shutdown message from a peer.")
        sys.exit(0)

    if text != "ACK":
        send_message("ACK")

    queue.put((clock, peer_ip, text))
    print_messages()

def send_message(message):
    global lamport_clock
    lamport_clock += 1

    json_message = json.dumps({"text": message, "clock": lamport_clock, "peerIp": self_ip})
    for socket in neighbors_map.values():
        try:
            socket.sendall((json_message + '\n').encode())
            if message == "SHUTDOWN":
                socket.close()
        except Exception as e:
            print(f"Error sending message: {e}")

def print_messages():
    while not queue.empty():
        clock, peer_ip, text = queue.get()
        if text != "ACK":
            print(f"{peer_ip}: {text}")

def get_poisson_delay(lambda_val):
    return -math.log(1.0 - random.random()) / lambda_val

def start_message_sending():
    def send_periodically():
        while True:
            delay = get_poisson_delay(lambda_value)
            threading.Event().wait(delay)
            random_word = random.choice(words_array)
            send_message(random_word)

    threading.Thread(target=send_periodically, daemon=True).start()

def get_own_ip():
    for interface_name, addresses in os.popen("ipconfig").readlines():
        if "IPv4" in address:
            return addresses[0]
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python peer.py [peerIps]")
        sys.exit(1)

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    peer_ips = sys.argv[1:]
    self_ip = get_own_ip()

    server = start_peer_server("0.0.0.0", 4000)

    for peer_ip in peer_ips:
        setup_persistent_socket(peer_ip, 4000)

    start_message_sending()
