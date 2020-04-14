#!/usr/bin/env python3

import socket
import selectors
import types


HEADER_LENGTH = 1024
host = socket.gethostname()
port = 65432
sel = selectors.DefaultSelector()  # choose the best selector for OS
client_dic = {}
sock_list = []




# toDo get_client_list
def get_client_list(key):
    pass


def accept_wrapper(sock):
    # This function will accept the new clients_dict, and will register them.
    conn, addr = sock.accept()

    conn.setblocking(False)  # for multiple clients_dict

    # print(f"accepted connection from {addr[0]}:{addr[1]} username:{user['data'].decode('utf-8')}")D
    print("accepted connection from", addr[0], addr[1])

    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")  # create a object for data
    # events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, selectors.EVENT_READ, data=data)

    # send_command(sock)


def service_connection(key, mask):
    # client connection handling; mask contains the events that are ready (2 or 3)
    sock = key.fileobj
    data = key.data  # data: addr, inb, outb

    #  Read Event
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:  # if there is any data
            data.outb += recv_data  # add to outb
            if data.outb:
                print("echo", data.outb, "from", data.addr)
                sent = len(data.outb)
                data.outb = data.outb[sent:]  # remove from buffer


def write_to_client(dic):
    clients = dic
    if len(clients) < 2:
        print("not enough clients_dict")


def send_command(key):
    sock = key
    while True:
        cmd = input('cmd> ')
        if cmd == 'quit':
            sock.send(b'quit')
            print("quit connection")

            sel.unregister(sock)
            sock.close()
            break
        if cmd == 'list':
            try:
                accept_wrapper(sock)
            except Exception as e:
                print("no new client!", e)
        if len(cmd) > 0:
            sock.send(cmd.encode())
            del cmd


# optional: type host and port over terminal -> delete the hard codeded host and port and uncomment the code below
# host, port = sys.argv[1], int(sys.argv[2])  # usage:, server.py <host> <port>
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()  # enable server to accept connections
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)  # register the socket for listening

socket_list = [lsock]
clients = {}


def receive_msg(client_socket):
    try:
        messsage_header = client_socket.recv(HEADER_LENGTH)
        if not len(messsage_header):
            return False

        messsage_lenght = int(messsage_header.decode('utf-8'))
        return {"header": messsage_header, "data": client_socket.recv(messsage_lenght)}
    except Exception as e:
        print(str(e))
        return False


while True:

    try:
        # Wait until some registered file objects become ready,
        # returns a list of (key, events) tuples
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:  # data is from listening socket-> accecpt
                accept_wrapper(key.fileobj)  # fileobj returns the socket obj
                print(key.events)

            else:
                print(key.events)
                service_connection(key, mask)  # already accepted -> next to handling the data
                # send_command(key.fileobj)

    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        pass
