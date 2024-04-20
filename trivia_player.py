import socket
from timeit import default_timer as timer

class Player:
    # a class for a player in the game 
    def __init__(self, name, address, dst_port, client_socket):
        """
        Initialize the player with a name, address, destination port, and client socket.
        input: name - the name of the player
               address - the address of the player
               dst_port - the destination port of the player
               client_socket - the client socket of the player
        output: None"""
        self._score = True
        self._name = name
        self._address = address
        self._dst_port = dst_port
        self._client_socket = client_socket
        self._time =10

    @property
    def time(self):
        """
        The time it took the player to answer the question.
        """
        return self._time

    @time.setter
    def time(self, value):
        """
        Set the time it took the player to answer the question.
        """
        self._time = value

    @property
    def score(self):
        """
        Player's score, used for statistics and tie breaking.
        """
        return self._score

    @score.setter
    def score(self, value):
        """
        Set the player's score.
        """
        self._score = value

    @property
    def name(self):
        """
        The name of the player.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the name of the player.
        """
        self._name = value

    @property
    def address(self):
        """
        The IP address of the player.
        """
        return self._address

    @address.setter
    def address(self, value):
        """
        Set the IP address of the player.
        """
        self._address = value

    @property
    def dst_port(self):
        """
        The destination port of the player.
        """
        return self._dst_port

    @dst_port.setter
    def dst_port(self, value):
        """
        Set the destination port of the player.
        """
        self._dst_port = value

    @property
    def client_socket(self):
        """
        The client socket of the player.
        """
        return self._client_socket

    @client_socket.setter
    def client_socket(self, value):
        """
        Set the client socket of the player.
        """
        self._client_socket = value

    def announce(self, message):
        """
        Send a message to the player, separated by a newline.
        input: message - the message to send to the player
        output: None
        """
        message += "\n"
        self._client_socket.sendall(message.encode())

    def question(self, question, answer, limit = 10):
        """"
        Ask the player a question and get their answer.
        input: question - the question to ask the player
               answer - the correct answer to the question
               limit - the time limit for the player to answer the question
        output: True if the player answered correctly, False (0) otherwise
        """
        # player respons to question 
        start = timer()  # a timer to answer the questiob
        try:
            self.client_socket.settimeout(
                limit)  
            data = self._client_socket.recv(1024)
            self.score = (int(answer == (data.decode().strip().lower() in ['y', 't', '1']))) * (
                         timer() - start) # calculate how fast and wether or not answered correctly
            self.time = timer()- start
            self.announce("Answer submitted, waiting for all players to answer...")
            return (answer == (data.decode().strip().lower() in ['y', 't', '1']))
        except socket.timeout:
            # in case of the player not answering in time
            self.announce("Ran out of time, end of round...")
            self.score = 0
            self.time = 10 
            return 0

        