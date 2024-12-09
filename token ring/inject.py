import socket

HOST = 'localhost'
PORT = 12348

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.bind((HOST, PORT))
client.connect(('localhost', 22222))

client.send(str('token').encode('UTF-8'))

client.close()


