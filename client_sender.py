import socket

HOST = socket.gethostname()  # The server's hostname or IP address
PORT = 65432  # The port used by the server
HEADERSIZE = 10

# message = md.report()  # dict with report data
# prepare report to send:

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect((HOST, PORT))  # connects to server
        s.settimeout(5)
        while True:

            message = input()
            message = f"{len(message):<{HEADERSIZE}}" + message
            s.sendall(message.encode())  # send report
            data_recv = s.recv(10)
            print("response: ", data_recv.decode('utf-8'))

    except Exception as e:
        print(e)
        s.close()
        exit()
