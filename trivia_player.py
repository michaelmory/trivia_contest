import socket

class Player:
    def __init__(self, name, address, dst_port, client_socket):
        self._score = 0
        self._name = name
        self._address = address
        self._dst_port = dst_port
        self._client_socket = client_socket

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def dst_port(self):
        return self._dst_port

    @dst_port.setter
    def dst_port(self, value):
        self._dst_port = value

    @property
    def client_socket(self):
        return self._client_socket

    @client_socket.setter
    def client_socket(self, value):
        self._client_socket = value

    def anounce(self, message):
        self._client_socket.sendall(message.encode())