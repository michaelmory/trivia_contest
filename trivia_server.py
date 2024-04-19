import socket
import threading
import struct
import selectors
import select
import logging
import os
import time
from trivia_player import Player

trivia_questions = [
    ("Is HTTP a stateless protocol?", True),
    ("Does the TCP protocol guarantee delivery of packets in order?", True),
    ("Is UDP faster than TCP because it requires a three-way handshake for connection establishment?", False),
]
server_ip = socket.gethostbyname(socket.gethostname())
server_name = "Mystic"
udp_port = 13117
tcp_port = 1337
min_clients = 1 # start 10 second timer after a player connects and len(self.clients) >= min_clients

# when debug=True, the server will print debug messages
class TriviaServer:
    def __init__(self, host=server_ip, name = server_name, min_clients = min_clients, trivia_questions = trivia_questions, tcp_port=tcp_port, udp_port=udp_port, debug=False):
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
        self.state = 1 # 0 = shutdown, 1 = waiting for clients, 2 = trivia game in progress
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.game_timer = None
        self.countdown = 10
        # debug section (probably delete before submission)
        self.debug = debug
        self.tcp_socket.settimeout(1)  # Set a timeout of 1 second
        self.udp_socket.settimeout(1)  # Set a timeout of 1 second

    def start(self): #
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

    def setup_tcp_socket(self): #
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        print(f"Server started, listening on IP {self.host} and port {self.tcp_port}")

    def broadcast_offers(self): #
        message = struct.pack('!I B 32s H', 0xabcddcba, 0x02, self.name.encode().ljust(32), self.tcp_port)
        try:
            while self.state == 1:
                self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
                if self.debug:
                    print(f"Broadcasting server offer to port {self.udp_port}, Clients: {[k for k in self.clients.keys()]}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.state = 0

    def handle_client(self, client_socket, addr): #
        print(f"Connected to {addr}") # TODO: say connected only if connected
        try:
            # while self.state == 1:
                data = client_socket.recv(1024)
                if not data or self.state != 1:
                    pass
                client_name = data.decode().strip()
                if client_name not in self.clients: # TODO: if the name is taken, ask the client to choose another name
                    self.clients[client_name] = Player(client_name, addr[0], addr[1], client_socket)
                    print(f"New client {client_name} connected from {addr}")
                    if len(self.clients) >= self.min_clients:
                        self.reset_game_timer()
        finally:
            # client_socket.close()
            pass

    def broadcast_countdown(self):
        count = self.countdown
        while count > 0:
            self.announce_message(f"The game will start in {count} seconds.")
            if self.debug:
                print(f"Countdown: {count}")
            time.sleep(1)
            count -= 1

    def reset_game_timer(self):
        if self.game_timer:
            self.game_timer.cancel()
        if hasattr(self, 'countdown_timer') and self.countdown_timer.is_alive():
            self.countdown_timer.join()
        self.game_timer = threading.Timer(self.countdown, self.start_game)
        self.countdown_timer = threading.Thread(target=self.broadcast_countdown)
        self.game_timer.start()
        self.countdown_timer.start()
        
    def start_game(self):
        self.state = 2
        self.announce_message("Game is starting now!", 0x01)
        self.game_time()

    def game_time(self,timer = 10):
        for i, (question, answer) in enumerate(self.questions):
            self.announce_message(f"Question #{i+1}:") # TODO: end if there's a winner
            client_threads =  [threading.Thread(target=self.clients[client].question, args=(question,answer,timer)) for client in self.clients]
            for client_thread in client_threads:
                client_thread.start()
            for client_thread in client_threads:
                client_thread.join()
        self.announce_message("Game over! The scores are:\n", 0x05)
        scoreboard = sorted(self.clients, key = lambda x: self.clients[x].score, reverse = True)
        for client in scoreboard:
            self.announce_message(f"{client}: {self.clients[client].score}")
        self.announce_message(f"Congratulations {scoreboard[0]} on the big W\n\nThanks for playing!")
        self.reset_state()

    def reset_state(self):
        # self.state = 1
        self.disconnect_all()
        self.scores.clear()
        self.start()

    def announce_message(self, message, message_type = 0x00):
        # message_type 0x00 = simply print, 0x01 = game start, 0x02 = invalid, 0x03 = question, 0x04 = disconnect, 0x05 = game over
        for player in self.clients.values():
            player.announce(message, message_type)

    def disconnect_client(self, client_name):
        self.clients[client_name].announce("Disconnected by the server.", 0x04)
        self.clients[client_name].client_socket.close()
        del self.clients[client_name]

    def disconnect_all(self):
        for client_name in self.clients:
            self.clients[client_name].announce("Disconnected by the server.", 0x04)
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