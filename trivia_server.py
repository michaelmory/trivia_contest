import socket
import threading
import struct
import selectors
import select
import logging
import os
import time
from copy import deepcopy
from trivia_player import Player
from random import shuffle
import os
os.system('color')

trivia_questions = [
    ("Is HTTP a stateless protocol?", False),
    ("Does the TCP protocol guarantee delivery of packets in order?", True),
    ("Is UDP faster than TCP because it requires a three-way handshake for connection establishment?", False),
    ("Are the Presentation and Session layers part of the TCP/IP model?", False),
    ("Is packet switching a fundamental concept in the Network layer?", True),
    ("Does the Application layer provide end-to-end data communication?", True),
    ("Is the main purpose of the Transport layer to provide reliable data transfer services to the upper layers?", True),
    ("Does the Physical layer define the hardware equipment, cabling, wiring, frequencies, and signals used in the network?", True),
    ("Is ICMP used for error reporting and query messages within the Internet Protocol Suite?", True),
    ("Are HTTP cookies used to maintain state in the stateless HTTP protocol?", True),
    ("Does the Data Link layer establish, maintain, and terminate a connection?", False),
    ("Is the Network layer responsible for data routing, packet switching, and control of network congestion?", True),
    ("Can caches reduce network latency by storing frequently accessed resources closer to the user?", True),
    ("Is the five-layer internet model composed of the Physical, Data Link, Network, Transport, and Application layers?", True),
    ("Does HTTPS encrypt the entire HTTP message?", True),
    ("Is SMTP a protocol used for receiving email messages?", False),
    ("Are IP addresses defined at the Transport layer of the OSI model?", False),
    ("Does FTP use TCP for reliable data transfer?", True),
    ("Is the primary purpose of ARP to translate URLs into IP addresses?", False),
    ("Can network delays be caused solely by the time it takes to propagate signals across the physical medium?", False)
]
server_ip = socket.gethostbyname(socket.gethostname())

class TriviaServer:
    
    def __init__(self, name="Mystic", host=server_ip, min_clients=2, trivia_questions=trivia_questions,
                 tcp_port=1337, udp_port=13117):
        """
        Initialize the TriviaServer with the given parameters.
        input: host - the IP address of the server
               name - the name of the server
               min_clients - the minimum number of clients needed to start the game
               trivia_questions - a list of tuples containing questions and answers
               tcp_port - the port number for the TCP connection
               udp_port - the port number for the UDP connection
        output: None
        """
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.name = name
        self.questions = trivia_questions  # all of our questions for the game
        self.min_clients = min_clients  # minimum number of clinets needed to run the game
        self.clients = {}  # {client_name: player_object}
        self.fastest_player = ("",10)  #  the fastest player in the current session and his average answering speed
        self.scoreboard = {}  # scoreboard counting how many wins each player has
        self.state = 1  # 0 = shutdown, 1 = waiting for clients, 2 = trivia game in progress
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.game_timer = None
        self.countdown_timer = None
        self.countdown = 10
        self.reset = True
        self.tcp_socket.settimeout(1)  # Set a timeout of 1 second
        self.udp_socket.settimeout(1)  # Set a timeout of 1 second

    def start(self):
        """
        Start the TriviaServer. This function sets up the TCP and UDP sockets,
        broadcasts offers to clients, and handles client connections.
        no input or output
        """
        if self.state == 1: # initial start
            self.setup_tcp_socket()
        elif self.state == 2: # server was reset
            self.state = 1
        else: # only one other option
            self.shutdown()
        udp_thread = threading.Thread(target=self.broadcast_offers)
          # start broadcasting for players
        udp_thread.start()
        try:
            while self.state == 1:
                try:  
                     # adding connecting to clients and starting game if possible
                    client_socket, addr = self.tcp_socket.accept()   
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    client_thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.shutdown()
        finally:
            pass

    def setup_tcp_socket(self):  
        """
        Set up the TCP socket for the server.
        no input or output
        """
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        print(f"\033[32mServer started, listening on IP {self.host} and port {self.tcp_port}\033[0m")

    def broadcast_offers(self):
        """
        Broadcast server offers to clients using UDP.
        no input or output
        """
        # broadcasting offers for anyone who wants to join
        message = struct.pack('!I B 32s H', 0xabcddcba, 0x02, self.name.encode().ljust(32), self.tcp_port) # breoadcast message standard
        try:
            while self.state == 1: # while the game has not started, keep broadcasting every second
                self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
                print(f"Broadcasting server offer to port {self.udp_port}, Clients connected: {[k for k in self.clients.keys()]}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.state = 0


    def valid_username(self, client_name):
        """
        Validate the client's username.
        input: client_name - the client's username
        output: True if the username is valid, False otherwise
        """
        if client_name in self.clients or client_name == "":
            return False
        for c in client_name:
            if not c.isalnum() and not c.isspace():
                if "BOT-" in client_name: # if the username is a bot, it is valid
                    return True
                return False
        return True
    def handle_client(self, client_socket, addr):
        """
        Handle a client connection. This function receives the client's username,
        validates it, and adds the client to the game.
        input: client_socket - the client's socket
                addr - the client's address
        output: None
        """
        # connect to the client and start game if enougn players are present
        print(f"{addr} attempting to connect")  
        try:
            data = client_socket.recv(1024)
            if not data or self.state != 1:
                pass
            client_name = data.decode().strip()
            while not self.valid_username(client_name):  # check if the username is valid and not taken, if not ask for a new one
                client_socket.sendall("\033[1;32mUsername invalid or already taken. Please try again with a different name.".encode())
                data = client_socket.recv(1024)
                if not data or self.state != 1: # if the server has still not started or the client disconnected
                    pass
                client_name = data.decode().strip()
            self.clients[client_name] = Player(client_name, addr[0], addr[1], client_socket)
            print(f"New client {client_name} connected from {addr}")
            self.announce_message(f"\033[1;32m{client_name} has joined the lobby!")
            if len(self.clients) >= self.min_clients: # if enough players are present start the game
                self.reset_game_timer()
        finally:
            pass

    def broadcast_countdown(self):  
        """
        Broadcast a countdown message to all clients then starts the game.
        Threaded function, countdown can be reset.
        no input or output
        """
        # broadcasting to all players that the game will start soon
        count = self.countdown
        while self.reset or count > 0:
            if self.reset: # if the countdown was reset, start over
                self.reset = False
                count = self.countdown
            self.announce_message(f"\033[1;33mThe game will start in {count} seconds.\033[0m")
            print(f"Countdown: {count}")
            time.sleep(1)
            count -= 1
        self.reset = True
        self.countdown_timer = None
        self.start_game()

    def reset_game_timer(self):
        """
        Reset or initiate the game timer.
        no input or output"""
        if not self.countdown_timer:
            self.countdown_timer = threading.Thread(target=self.broadcast_countdown)
            self.countdown_timer.start()
        else:
            self.reset = True

    def start_game(self): 
        """
        Start the game.
        no input or output
        """
        self.state = 2
        self.announce_message("\033[1;34mGame is starting now!")
        self.game_time()

    def game_time(self, timer=10):
        """
        Run the game.
        input: timer - the time limit for answering questions
        output: None
        """
         # the game itself
        ingame = list(self.clients.keys())  # a list of players still in the game
        player_speeds = {cli: 0 for cli in ingame if "BOT-" not in cli}  # a list of how fast players answer on average excluding bots
        shuffle(self.questions)  # shuffling the questions so they are not allways the same order

        # Regular rounds
        for i, (question, answer) in enumerate(self.questions):  
            # runing over all of the questions
            if len(ingame) == 1 or i == len(self.questions) - 1:  
                # if there is only one player left or one question left  no need for the loop
                break
            cl = str([c for c in ingame])[1:-1]  # creating a string of all current players
            self.announce_message("\033[1;35mRound begins! You're up, \033[32m"+ cl +f"\033[1;0m\n\nQuestion #{i + 1}: \n{question}")  # sending question to clients
            client_threads = [threading.Thread(target=self.clients[client].question, args=(question, answer, timer)) for
                              client in self.clients if client in ingame]  # starting a thread for each client
            for client_thread in client_threads:
                client_thread.start()
            for client_thread in client_threads:
                client_thread.join()  # wait for everyone to finish answering or timer to run out
            losers = ingame.copy()  # a list used to remove those who lost the round
            for client in self.clients:  
                 # going over the clients checking who answered correctly
                if client in ingame:
                    if not self.clients[client].score:
                        self.announce_message(f"\033[1;31m{client}\033[31m is incorrect!\033[0m")
                        if "BOT-" not in client:  
                            # if the player answered wrong calculate the average time it took him to answer up until now
                            player_speeds[client] = (player_speeds[client]+self.clients[client].time)/(i+1)
                        losers.remove(client)  # remove loser from list
                    else: 
                        # if the player answered correctly 
                        self.announce_message(f"\033[1;32m{client}\033[32m is correct!\033[0m")
                        if "BOT-" not in client:
                            player_speeds[client] += self.clients[client].time
                    
            if len(losers) != 0:  
                # if some players are still in the game start next round
                ingame = losers
                time.sleep(0.5)
            else:  
                # if all current players lost, start another round with everyone
                for client in ingame:
                    if "BOT-" not in client:
                        player_speeds[client] = (player_speeds[client])*(i+1)
                self.announce_message(f"\033[1;36mEveryone was wrong - you all continue to the next round!\033[0m")
                time.sleep(0.5)

        # Final round / Tiebreaker
        if len(ingame) > 1: 
             # if the main game finished and there are still players then we reached the last question
             # runs the same as the game but uses speed as tiebreaker
            cl = str([c for c in ingame])[1:-1]
            self.announce_message(f"\033[1;95mThis is the last question! fastest one to answer correctly wins!\033[0m \nRemaining contestants:\033[32m" + cl + f"\033[1;34m\nQuestion la finale: \n{self.questions[-1][0]}\033[0m")
            client_threads = [threading.Thread(target=self.clients[client].question,
                                               args=(self.questions[-1][0], self.questions[-1][1], timer)) for client in
                              self.clients if client in ingame]
            for client_thread in client_threads:
                client_thread.start()
            for client_thread in client_threads:
                client_thread.join()
            for client in ingame:
                if "BOT-" not in client:
                    player_speeds[client] = ((player_speeds[client])+self.clients[client].time)/len(self.questions)
        for client in self.clients:  
                 # going over the clients checking who answered correctly
            if client in ingame:
                if not self.clients[client].score:
                    self.announce_message(f"\033[1;31m{client}\033[31m is incorrect!\033[0m")
                else: 
                    # if the player answered correctly 
                    self.announce_message(f"\033[1;32m{client}\033[32m is correct!\033[0m")
                    
        # calculates game statistics
        ingame = [min(ingame, key=lambda player: self.clients[player].time)]
        player_speeds = {key: round(value, 3) if value != 0 else 10 for key, value in player_speeds.items()}

        player_speeds =dict(sorted(player_speeds.items(), key=lambda item: item[1], reverse=False))
        speeds = list(player_speeds.items())
        # check if record was broken
        if self.fastest_player[1] > speeds[0][1] and speeds[0][1] != 0:
            self.fastest_player = speeds[0]
        # updates scoreboard
        if ingame[0] in self.scoreboard:
            self.scoreboard[ingame[0]] += 1
        else:
            self.scoreboard[ingame[0]] = 1 
        
        # announce the winnder and show statistics
        self.announce_message(f"\033[1;167mGame over! The Winner is: {ingame[0]}\033[0m")
        self.announce_message(f"\033[1;175mCongratulations {ingame[0]} on the big W\n\nThanks for playing!\033[0m")
        self.announce_message(f"\n\n\n\033[1;35mscoreboard:\n\033[0m {self.scoreboard}")
        self.announce_message(f"\n\033[1;35mfastest player record: \033[1;33m{self.fastest_player} \033[1;36m\n\ncurrent game player speeds:\n  \033[33m{player_speeds}\033[0m")
        self.reset_state()

    def reset_state(self):
        """
        Reset the server state.
        called after the game ends
        no input or output
        """
        # restart the game
        self.disconnect_all()
        self.start()

    def announce_message(self, message):
        """
        A form of broadcasting a message to all connected clients.
        input: message - the message to send to all clients
        output: None
        """
        # send a message to all clients
        for player in self.clients.values():
            player.announce(message)

    def disconnect_client(self, client_name):
        """
        Disconnect a client from the server.
        input: client_name - the client's username
        output: None
        """
        # disconnect client from the server
        self.clients[client_name].announce("Disconnected by the server.")
        self.clients[client_name].client_socket.close()
        del self.clients[client_name]

    def disconnect_all(self):
        """
        Disconnect all clients from the server.
        no input or output
        """
        # disconnect all clients from server
        for client_name in self.clients:
            self.clients[client_name].announce("Disconnected by the server.")
            self.clients[client_name].client_socket.close()
        self.clients.clear()

    def shutdown(self):
        """
        Shut down the server.
        no input or output
        """
        # shut down the seever
        self.state = 0
        self.disconnect_all()
        self.tcp_socket.close()
        self.udp_socket.close()
        print("Server shutdown complete.")


if __name__ == "__main__":
    server = TriviaServer("ServeReder")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nInterrupt received! Shutting down server...")
        server.shutdown()