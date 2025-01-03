import socket
import random

HOST = socket.gethostbyname(socket.gethostname())
PORT = random.randint(30000, 40000)
print(HOST)

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    client.bind((HOST, PORT))
    client.connect(('l813', 44436))

    client.send(str('token').encode('UTF-8'))

    client.close()
except Exception as e:
    print(f'Error sending token {e}')


