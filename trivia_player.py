import socket
from timeit import default_timer as timer

class Player:
    def __init__(self, name, address, dst_port, client_socket):
        self._score = True
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

    def announce(self, message):
        message += "\n"
        self._client_socket.sendall(message.encode())

    def question(self, question, answer, limit = 10):
        start = timer()
        try:
            self.client_socket.settimeout(limit)  # TODO: leave a second between questions to avoid next question being sent as answer
            data = self._client_socket.recv(1024)
            self.score = (int(answer == (data.decode().strip().lower() in ['y', 't', '1']))) * (
                        limit - timer() + start) / limit
            self.announce("Answer submitted, waiting for all players to answer...")
            return (answer == (data.decode().strip().lower() in ['y', 't', '1']))
        except:
            self.announce("Ran out of time, end of round...")
            self.score = 0
            return 0