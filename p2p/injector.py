import socket
import pickle

'''Injector send a empty set to start operation.'''

HOST = socket.gethostname()
PORT = 12354

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.bind((HOST, PORT))
client.connect(('localhost', 22222))
 
my_set = dict()
data = pickle.dumps(my_set)

client.sendall(data)

client.close()

