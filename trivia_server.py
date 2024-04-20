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

trivia_questions = [
    ("Is HTTP a stateless protocol?", True),
    ("Does the TCP protocol guarantee delivery of packets in order?", True),
    ("Is UDP faster than TCP because it requires a three-way handshake for connection establishment?", False),
    # ("Are the Presentation and Session layers part of the TCP/IP model?", False),
    # ("Is packet switching a fundamental concept in the Network layer?", True),
    # ("Does the Application layer provide end-to-end data communication?", True),
    # ("Is the main purpose of the Transport layer to provide reliable data transfer services to the upper layers?", True),
    # ("Does the Physical layer define the hardware equipment, cabling, wiring, frequencies, and signals used in the network?", True),
    # ("Is ICMP used for error reporting and query messages within the Internet Protocol Suite?", True),
    # ("Are HTTP cookies used to maintain state in the stateless HTTP protocol?", True),
    # ("Does the Data Link layer establish, maintain, and terminate a connection?", False),
    # ("Is the Network layer responsible for data routing, packet switching, and control of network congestion?", True),
    # ("Can caches reduce network latency by storing frequently accessed resources closer to the user?", True),
    # ("Is the five-layer internet model composed of the Physical, Data Link, Network, Transport, and Application layers?", True),
    # ("Does HTTPS encrypt the entire HTTP message?", True),
    # ("Is SMTP a protocol used for receiving email messages?", False),
    # ("Are IP addresses defined at the Transport layer of the OSI model?", False),
    # ("Does FTP use TCP for reliable data transfer?", True),
    # ("Is the primary purpose of ARP to translate URLs into IP addresses?", False),
    # ("Can network delays be caused solely by the time it takes to propagate signals across the physical medium?", False)
]
server_ip = socket.gethostbyname(socket.gethostname())
server_name = "Mystic"
udp_port = 13117
tcp_port = 1337
min_clients = 2 # start 10 second timer after a player connects and len(self.clients) >= min_clients


# when debug=True, the server will print debug messages
class TriviaServer:
    def __init__(self, host=server_ip, name=server_name, min_clients=min_clients, trivia_questions=trivia_questions,
                 tcp_port=tcp_port, udp_port=udp_port, debug=False):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.name = name
        self.questions = trivia_questions
        self.min_clients = min_clients
        self.clients = {}  # {client_name: player_object}
        self.scores = {}
        self.questions = trivia_questions
        self.question_index = 0
        self.state = 1  # 0 = shutdown, 1 = waiting for clients, 2 = trivia game in progress
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.game_timer = None
        self.countdown_timer = None
        self.countdown = 10
        self.reset = True
        # debug section (probably delete before submission)
        self.debug = debug
        self.tcp_socket.settimeout(1)  # Set a timeout of 1 second
        self.udp_socket.settimeout(1)  # Set a timeout of 1 second

    def start(self):  #
        if self.state == 1:
            self.setup_tcp_socket()
        elif self.state == 2:
            self.state = 1
        else:
            self.shutdown()
        udp_thread = threading.Thread(target=self.broadcast_offers)
        udp_thread.start()
        try:
            while self.state == 1:
                try:
                    client_socket, addr = self.tcp_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    client_thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.shutdown()
        finally:
            # self.shutdown()
            pass

    def setup_tcp_socket(self):  #
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        print(f"\033[32mServer started, listening on IP {self.host} and port {self.tcp_port}\033[0m")

    def broadcast_offers(self):  #
        message = struct.pack('!I B 32s H', 0xabcddcba, 0x02, self.name.encode().ljust(32), self.tcp_port)
        try:
            while self.state == 1:
                self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
                if self.debug:
                    print(
                        f"Broadcasting server offer to port {self.udp_port}, Clients: {[k for k in self.clients.keys()]}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.state = 0


    def valid_username(self, client_name):
        if client_name in self.clients or client_name == "":
            return False
        for c in client_name:
            if not c.isalnum() and not c.isspace():
                return False
        return True
    def handle_client(self, client_socket, addr):  #
        print(f"{addr} attempting to connect")  # TODO: say connected only if connected
        try:
            # while self.state == 1:
            data = client_socket.recv(1024)
            if not data or self.state != 1:
                pass
            client_name = data.decode().strip()
            while not self.valid_username(client_name):  # TODO: if the name is taken, ask the client to choose another name
                client_socket.sendall("Username invalid or already taken. Please try again with a different name.".encode())
                data = client_socket.recv(1024)
                if not data or self.state != 1:
                    pass
                client_name = data.decode().strip()
            self.clients[client_name] = Player(client_name, addr[0], addr[1], client_socket)
            print(f"New client {client_name} connected from {addr}")
            if len(self.clients) >= self.min_clients:
                self.reset_game_timer()
        finally:
            # client_socket.close()
            pass

    def broadcast_countdown(self):
        # count = self.countdown
        while self.reset or count > 0:
            if self.reset:
                self.reset = False
                count = self.countdown
            self.announce_message(f"\033[1;11mThe game will start in {count} seconds.\033[0m")
            if self.debug:
                print(f"Countdown: {count}")
            time.sleep(1)
            count -= 1
        self.reset = True
        self.countdown_timer = None
        self.start_game()

    def reset_game_timer(self):
        if not self.countdown_timer:
            self.countdown_timer = threading.Thread(target=self.broadcast_countdown)
            self.countdown_timer.start()
        else:
            self.reset = True

    def start_game(self):
        self.state = 2
        self.announce_message("Game is starting now!")
        self.game_time()

    def game_time(self, timer=10):

        ingame = list(self.clients.keys())
        shuffle(self.questions)
        for i, (question, answer) in enumerate(self.questions):
            if len(ingame) == 1 or i == len(self.questions) - 1:
                break
            cl = str([c for c in ingame])[1:-1]
            self.announce_message("Round begins! You're up, "+ cl +f"\nQuestion #{i + 1}: \n{question}")
            client_threads = [threading.Thread(target=self.clients[client].question, args=(question, answer, timer)) for
                              client in self.clients if client in ingame]
            for client_thread in client_threads:
                client_thread.start()
            for client_thread in client_threads:
                client_thread.join()
            losers = ingame.copy()
            for client in self.clients:
                if client in ingame:
                    if not self.clients[client].score:
                        self.announce_message(f"\033[31m{client} is incorrect!\033[0m")
                    else:
                        self.announce_message(f"\033[32m{client} is correct!\033[0m")
                    if not self.clients[client].score:
                        print(client, self.clients[client].score)
                        losers.remove(client)
            if len(losers) != 0:
                ingame = losers
            else:
                self.announce_message(f"\033[1;36mEveryone was wrong - you all continue to the next round!\033[0m")

        if len(ingame) > 1:
            cl = str([c for c in ingame])[1:-1]
            self.announce_message(f"\033[1;95mThis is the last question! fastest one to answer correctly wins!\033[0m \nRemaining contestants:\033[32m" + cl + f"\033[0m\nQuestion la finale: \n{self.questions[-1][0]}")
            client_threads = [threading.Thread(target=self.clients[client].question,
                                               args=(self.questions[-1][0], self.questions[-1][1], timer)) for client in
                              self.clients if client in ingame]
            for client_thread in client_threads:
                client_thread.start()
            for client_thread in client_threads:
                client_thread.join()
                ingame = [max(ingame, key=lambda player: self.clients[player].score)]

        self.announce_message(f"\033[1;167mGame over! The Winner is: {ingame[0]}\033[0m")
        self.announce_message(f"\033[1;175mCongratulations {ingame[0]} on the big W\n\nThanks for playing!\033[0m")
        self.reset_state()

    def reset_state(self):
        # self.state = 1
        self.disconnect_all()
        self.scores.clear()
        self.start()

    def announce_message(self, message):
        for player in self.clients.values():
            player.announce(message)

    def disconnect_client(self, client_name):
        self.clients[client_name].announce("Disconnected by the server.")
        self.clients[client_name].client_socket.close()
        del self.clients[client_name]

    def disconnect_all(self):
        for client_name in self.clients:
            self.clients[client_name].announce("Disconnected by the server.")
            self.clients[client_name].client_socket.close()
        self.clients.clear()

    def shutdown(self):
        self.state = 0
        # disconnect all clients
        self.disconnect_all()
        self.tcp_socket.close()
        self.udp_socket.close()
        print("Server shutdown complete.")


# Usage
if __name__ == "__main__":
    server = TriviaServer(debug=True)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nInterrupt received! Shutting down server...")
        server.shutdown()