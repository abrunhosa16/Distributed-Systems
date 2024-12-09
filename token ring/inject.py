import socket

HOST = socket.gethostbyname(socket.gethostname())
PORT = 12348

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.bind((HOST, PORT))
client.connect(('l1203', 3000))

client.send(str('token').encode('UTF-8'))

client.close()


