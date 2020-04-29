import socket
import selectors
import sys
from ast import literal_eval as make_tuple

HEADERSIZE = 10


def get_value_from_key(dic, key):
    """

    :param dic: dictionary
    :param key: key of dict
    :return: value of dict
    """
    return list(dic.keys())[list(dic.values()).index(key)]


class TCPServer:

    def __init__(self):
        super().__init__()
        self.report_command = 'report_start'
        self.sel = selectors.DefaultSelector()
        self.IP = socket.gethostname()
        self.PORT = 65432
        self.clients_dict = {}
        self.lsock = object
        self._create_socket()
        self.client_id = 0
        self.host_list = []
        self.message = {}

    def _create_socket(self):
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lsock.bind((self.IP, self.PORT))
        self.lsock.listen()  # start listening on PORT
        print(f"listening on: {self.IP}, {self.PORT} ")
        self.lsock.setblocking(False)
        # register socket for select()
        self.sel.register(self.lsock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def _accept_sockets(self, sock):
        conn, addr = sock.accept()
        print('accepted', addr[0], 'from', addr[1])
        conn.setblocking(False)

        self.sel.register(conn, selectors.EVENT_READ, data=None)
        self._add_clients(conn, addr[0])

    def close_server(self):
        self.sel.close()
        print("Server closed!")

    def _add_clients(self, sock, addr):
        # dict of connected clients_dict
        self.client_id += 1
        # clients_dic = {socket_obj: (id, host)}
        self.clients_dict[sock] = self.client_id, addr

    def get_clients(self):
        # return list of host address and id from clients_dict sockets
        if self.clients_dict:
            for sock in self.clients_dict:
                # if host addr not in list
                if not self.clients_dict[sock] in self.host_list:
                    self.host_list.append(self.clients_dict[sock])
            return self.host_list

    def _receive_msg(self, key):
        full_msg = ''
        msg_len = 0
        new_msg = True

        try:
            self.sock = key.fileobj
            while True:
                msg = self.sock.recv(16)
                if not len(msg):
                    return
                if new_msg:
                    # buffering message
                    msg_len = int(msg[:HEADERSIZE])
                    new_msg = False
                full_msg += msg.decode('utf-8')
                # check if full msg received
                if len(full_msg) - HEADERSIZE == msg_len:
                    # return message and and host addr of sender
                    self.message = {"data": full_msg[HEADERSIZE:],
                                    "addr": self.clients_dict[key.fileobj]}
                    # send Response to client
                    key.fileobj.sendall(b'OK')
                    return self.message

        except Exception as e:
            print("disconnected from client\n", e)
            return False

    def get_msg(self):
        if self.message:
            return self.message
        return {}

    def extract_pos(self):
        """

        :return: pos as tuple (x,y)
        """

        # extract pos from report data -> works only if pos is the first value
        if self.message['data']:
            try:
                pos_tuple = make_tuple(self.message['data'].split(';')[0].split(':')[1])
                return pos_tuple
            except Exception as e:
                print(e)
                return 0, 0

    def send_cmd_to_client(self, host, msg):
        """

        :param host: host = ('id', 'host')
        :param msg: message to send as string
        """
        # clients_dict: {'socket':'(id, host address)'}
        client_id, client_host = host
        selected_host = (int(client_id), client_host)
        print("selected_host", selected_host)
        # check if socket with given host exists
        if selected_host in self.clients_dict.values():
            # extract socket from given host address -> get key from value of dict
            selected_socket = get_value_from_key(self.clients_dict, selected_host)

            try:
                # send msg to host
                print('send msg')
                selected_socket.sendall(msg.encode())
            except Exception as e:
                print(e)
        # socket not found
        else:
            print('no socket with given host found, nothing to send!')

    def broadcast(self, msg, host='', to=''):
        """

        :param msg: message as string
        :param host: id and host from sender as tuple. Empty to send to all
        :param to: empty or 'all' to send to all
        :return: broadcast message
        """
        try:
            # send cmd to all clients_dict
            if self.clients_dict and msg:
                if to == 'all':
                    # go through all clients_dict
                    for client_sockets in self.clients_dict:
                        client_sockets.sendall(msg.encode('utf-8'))
                # without sender client
                else:
                    # sock1: send_report script, sock2: client_listener script
                    sock1 = get_value_from_key(self.clients_dict, host)
                    # get host of client_listener -> same host but other id
                    client_id, addr = host
                    sock2 = get_value_from_key(self.clients_dict, (client_id - 1, addr))
                    for client_sockets in self.clients_dict:
                        if client_sockets != sock1 and client_sockets != sock2:
                            client_sockets.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(e)

    def run_server(self):
        try:
            # contains all events
            # select: waits until gets new event
            events = self.sel.select(timeout=None)
            for key, _ in events:
                # check if socket is new -> accept it
                if key.fileobj == self.lsock:
                    self._accept_sockets(key.fileobj)
                else:
                    # read incoming message
                    message = self._receive_msg(key)
                    if message is False:
                        # nothing received or connection lost
                        self.sel.unregister(key.fileobj)
                        # remove client and host addr from list
                        self.host_list.remove(self.clients_dict[key.fileobj])
                        del self.clients_dict[key.fileobj]
                        continue



        except Exception as e:
            print(str(e))
            self.sel.close()
            sys.exit()


class Statistic:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.forward = 0
        self.discard = 0

    def check_area(self, curr_x, curr_y):
        """

        :param curr_x: x coordinate from pi
        :param curr_y: y coordinate from pi
        :return: false if block else true
        """
        if curr_x in self.x and curr_y in self.y:
            self.discard += 1
            return False
        self.forward += 1
        return True

    def get_statistic(self):
        return self.forward, self.discard
