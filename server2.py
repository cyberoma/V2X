import socket
import selectors
import sys

sel = selectors.DefaultSelector()  # choose the best select for current OS

PORT = 65432  # The server's hostname or IP address
IP = socket.gethostname()  # The port used by the server

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP Socket
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # modifies the socket to allow us to reuse the address.
lsock.bind((IP, PORT))
lsock.listen()  # start listening on PORT
print(f"listening on: {IP}, {PORT} ")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)  # register socket for select()

# dict of connected clients_dict
clients = {}
id = 0
# collect console output
console_out = []


def accept(sock):
    conn, addr = sock.accept()
    console_out.append(f"accepted: {addr[0]} from {addr[1]}")
    # print('accepted', addr[0], 'from', addr[1])
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, data=None)
    client_id = id + 1
    clients[conn] = addr[0]
    print("clients_dict:", clients)


def read(key):
    try:
        sock = key.fileobj
        message = sock.recv(1024)
        if not len(message):
            return False
        return {"data": message, "addr": sock.getpeername()[0]}  # return message and and addr of sender

    except Exception as ex:
        print("disconnected from client\n", ex)
        return False


def broadcast(clients, sock, message):
    # go through all clients_dict
    for client_sockets in clients:
        # client who sends the message don't get it back
        if client_sockets != sock:
            client_sockets.send(message)


def run_server():
    # variables:
    # key.fileob: incoming sockets -> clients_dict
    # lsock: server socket
    # message: received message from clients_dict
    try:
        events = sel.select(timeout=None)

        for key, _ in events:
            # print("key val {}".format(key))
            # check if socket is new -> accept it
            if key.fileobj == lsock:
                print("new connection!")
                accept(key.fileobj)
                print("key:", key.fileobj)

            else:
                message = read(key)
                if message is False:
                    del clients[key.fileobj]
                    sel.unregister(key.fileobj)  # remove from selector
                    continue
                # broadcast the message to other clients_dict
                # broadcast(clients_dict, key.fileobj, (message['addr'] + ">" + message['data'].decode("utf-8")).encode())
                broadcast(clients, key.fileobj, message['data'])

    except Exception as e:
        print(str(e))
        sel.close()
        sys.exit()


while True:
    run_server()
