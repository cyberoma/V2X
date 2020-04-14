import socket

HOST = socket.gethostname()  # The server's hostname or IP address
PORT = 65432  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect((HOST, PORT))  # connects to server

    except Exception as e:
        print(e)
        exit()

    while True:
        message = input()  # take input in command line
        s.sendall(message.encode())  # send input
        data = s.recv(1024)  # get echo of input
        print('Received', repr(data))
        if not data:  # if get nothing back -> close connection
            print('closing connection to', HOST)
            break
