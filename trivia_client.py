import socket
import threading
import select
import sys
import struct
from inputimeout import inputimeout, TimeoutOccurred
import time
from random import shuffle


class TriviaClient:
    def __init__(self, username="Player"):
        self.bot_names = ['Yosi','Nahum','Rahamim','Shimon','Yohai', 'Takum', 'Human Person', 'Mom', 'Dad', 'Your Ex'] # bot names
        shuffle(self.bot_names)
        self.username = username
        if "BOT-" in self.username: # if the username is a bot, choose a random name
            self.username = "BOT-"+self.bot_names.pop()
        self.server_name = None
        self.server_address = None
        self.tcp_socket = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 13117))  # Listen on all interfaces for UDP broadcasts
        self.running = True

    def reset(self): # Reset the client to its initial state
        restart = self.input_timeout("Play another game?    ", 60)
        if restart in ['0', 'N', 'n', 'f', 'F', '!']: # If the user doesn't want to play again, stop the client
            self.stop()
            return
        print("Resetting...")
        self.server_name = None
        self.server_address = None
        self.tcp_socket = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 13117))
        self.running = True
        self.start()

    def start(self): # Start the client
        print("Client started, listening for offer requests...")
        self.listen_for_offers() # Listen for UDP broadcasts and connect to server
        self.game_lobby() # Wait for the game to start


    def listen_for_offers(self): # Listen for UDP broadcasts
        while self.running and not self.tcp_socket:
            data, addr = self.udp_socket.recvfrom(1024)  # Buffer size is 1024 bytes
            if self.validate_offer(data): # Validate the server's offer
                print(f"Received offer from server '{self.server_name}' at {addr[0]}, attempting to connect...")
                self.server_address = (addr[0], int.from_bytes(data[37:39], byteorder='big')) # Extract the server's address
                self.connect_to_server() 


    def validate_offer(self, data): # Validate the server's offer
        magic_cookie, message_type = struct.unpack('!I B', data[:5]) # Unpack the magic cookie and message type
        if magic_cookie == 0xabcddcba and message_type == 0x02: # Check and return if the magic cookie and message type are correct
            unpacked_data = struct.unpack('!I B 32s H', data)
            self.server_name = unpacked_data[2].decode().strip()
            return True
        return False

    def connect_to_server(self): # Connect to the server after receiving a valid offer
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect(self.server_address)
            self.tcp_socket.sendall((self.username + "\n").encode())
            response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            while "name." in response: # If the username is taken, choose a new one
                if "BOT-" in self.username: # if the username is a bot, choose a random name
                    self.username = "BOT-"+self.bot_names.pop()
                    continue
                print(response)
                self.username = input("Enter a new username (using only letters, numbers or spaces): ")
                self.tcp_socket.sendall((self.username + "\n").encode())
                response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(f"Connected to server {self.server_name} at {self.server_address[0]}, waiting for players to join...\n") 
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.tcp_socket = None # Reset the TCP socket and listen for offers again

    def game_lobby(self): # Wait for the game to start
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'now!' in str(data): # If the game is starting, start the game
                self.game_start()
    
    def input_timeout(self, question, t): # Get user Yes or No answer with a timeout to prevent blocking
        try:
            timer = time.time()
            message = inputimeout(question, timeout=t)
            while message not in ['0', 'N', 'n', 'f', 'F', '1', 'y', 'Y', 't', 'T']:
                message = inputimeout("Invalid input. Please enter your answer (\033[1;32m[Y,1,T]\033[0m for Yes \ \033[1;31m[N,F,0]\033[0m for no) ", timeout=t-(time.time()-timer))
        except TimeoutOccurred:
            message = '!' # Special message to indicate timeout
        return message


    def game_start(self): # Start the game
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'Disconnected by the server.' in data: # If the game is over, reset the client
                self.reset()
                break
            if 'Round begins!' or "last question!" in data: # If a new question is asked, get the user's answer
                participants = data.split("\nQ")[0] # Get the participants
                participants = participants.split("\'")[1:-1]
                if self.username in participants: # If the user is a participant, get the user's answer
                    question  = "enter your answer (\033[1;32m[Y,1,T]\033[0m for Yes \ \033[1;31m[N,F,0]\033[0m for no) "
                    message = self.input_timeout(question, 10)
                    if message != '!':
                        self.tcp_socket.sendall(message.encode())

    def stop(self): # Stop the client (unused)
        self.running = False
        if self.tcp_socket:
            self.tcp_socket.close()
        self.udp_socket.close()
        print("Client stopped.")

# Usage
if __name__ == "__main__":
    username = "yeled"
    client = TriviaClient(username)
    client.start()