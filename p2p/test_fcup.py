import socket
import threading
import json
import time
import math
import random
import sys

# Stores peer data { peerIp: timestamp }
peer_map = {}
# Stores peers connected to this peer
socket_array = []
# Poisson distribution parameter
lambda_param = 4 / 60
# Time-to-live for each peer entry
entry_ttl = 60


def start_peer_server(ip_address, port):
    """
    Sets up a server to accept incoming peer connections.
    """
    def handle_client(client_socket: socket.socket):
        connection_ip = client_socket.getpeername()[0]
        print(f"New Connection: {connection_ip}")

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8').strip()
                handle_incoming_message(message)
            except Exception as e:
                print(f"Client socket error: {e}")
                break

        client_socket.close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip_address, port))
    server.listen()
    print(f"Server running on {ip_address}:{port}")

    def accept_connections():
        while True:
            client_socket, _ = server.accept()
            threading.Thread(target=handle_client, args=(client_socket,)).start()

    threading.Thread(target=accept_connections, daemon=True).start()


def handle_incoming_message(message):
    """
    Handles incoming messages to register peers and update the map.
    """
    try:
        received_data = json.loads(message)
        print(received_data)

        for peer_ip, timestamp in received_data:
            peer_map[peer_ip] = max(peer_map.get(peer_ip, 0), timestamp)

        delete_expired_peers()
        print(f"Updated peer map: {len(peer_map)} total nodes ({list(peer_map.items())})")
    except Exception as e:
        print(f"Error processing incoming message: {e}")


def disseminate_peer_map():
    """
    Disseminates the current peer map to connected peers.
    """
    peer_map[server_ip] = time.time()
    delete_expired_peers()

    valid_entries = [
        (peer, timestamp)
        for peer, timestamp in peer_map.items()
        if (time.time()  - timestamp) <= entry_ttl
    ]

    message = json.dumps(valid_entries)

    for sock in socket_array:
        try:
            sock.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending data to peer: {e}")


def start_anti_entropy():
    """
    Periodically updates the peer map using Anti-Entropy.
    """
    def anti_entropy_cycle():
        while True:
            delay = get_poisson_delay(lambda_param)
            time.sleep(delay)
            disseminate_peer_map()
            print(f"Disseminated peer map: {list(peer_map.keys())}")

    threading.Thread(target=anti_entropy_cycle, daemon=True).start()


def delete_expired_peers():
    """
    Deletes expired peers (timestamp < TTL).
    """
    current_time = time.time() 
    for peer, timestamp in list(peer_map.items()):
        if current_time - timestamp > entry_ttl and peer != server_ip:
            print(f"Deleted peer: {peer}")
            del peer_map[peer]


def setup_persistent_socket(peer_ip, peer_port, name):
    """
    Sets up a persistent connection to the specified peer with retry logic.
    """
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, peer_port))
            print(f"{name} connected to {peer_ip}:{peer_port}")

            def listen_to_peer():
                while True:
                    try:
                        data = sock.recv(1024)
                        if not data:
                            break
                        handle_incoming_message(data.decode('utf-8'))
                    except Exception as e:
                        print(f"{name} error: {e}")
                        break

            threading.Thread(target=listen_to_peer, daemon=True).start()
            return sock
        except Exception as e:
            print(f"{name} error: {e}")
            print(f"Retrying connection to {peer_ip}:{peer_port} in 3 seconds...")
            time.sleep(3)


def get_poisson_delay(lambda_param):
    """
    Returns the delay to apply when creating the requests.
    """
    return -math.log(1.0 - random.random()) / lambda_param


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python your_script.py <selfPort> <peersPorts>")
        sys.exit(1)

    server_ip = sys.argv[1]
    peers_ips =sys.argv[2:]

    start_peer_server(server_ip, 3000)

    for peer_ip in peers_ips:
        socket_array.append(setup_persistent_socket( peer_ip, 3000, "PeerSocket"))

    start_anti_entropy()

    # Keep the main thread alive
    while True:
        time.sleep(1)
