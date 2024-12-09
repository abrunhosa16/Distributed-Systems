import socket

host_calculator = 'localhost'
port_calculator = 12345

while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect((host_calculator, port_calculator))
    
    # Send the first operation
    s.send(b'+ 2 3')
    result1 = s.recv(1024).decode('UTF-8')
    print(f"Result 1: {result1}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host_calculator, port_calculator))

    
    # Send the second operation
    s.send(b'* 5 5')
    result2 = s.recv(1024).decode('UTF-8')
    print(f"Result 2: {result2}")
