import socket
import random

HOST = socket.gethostbyname(socket.gethostname())
PORT = random.randint(30000, 40000)
print(HOST)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.bind((HOST, PORT))
client.connect(('l813', 33333))

client.send(str('token').encode('UTF-8'))

client.close()


