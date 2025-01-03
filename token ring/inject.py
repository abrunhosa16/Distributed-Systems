import socket
import sys

HOST = socket.gethostbyname(socket.gethostname())
print(HOST)

class NodeP:
    def __init__(self, next_):
        self.next_host = next_
        self.port = 44459
try:
    node: NodeP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    client.bind((HOST, node.port))
    client.connect((node.next_host, node.port))

    client.send(str('token').encode('UTF-8'))

    client.close()
except Exception as e:
    print(f'Error sending token {e}')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inject.py next_host")
        sys.exit(1)

    next_host = sys.argv[1]
    node = NodeP(next_= next_host)
    