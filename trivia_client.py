import socket
import threading
import select
import sys
import struct
from inputimeout import inputimeout, TimeoutOccurred
import time

class TriviaClient:
    def __init__(self, username="Player"):
        self.username = username
        self.server_name = None
        self.server_address = None
        self.tcp_socket = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 13117))  # Listen on all interfaces for UDP broadcasts
        self.running = True

    def start(self):
        print("Client started, listening for offer requests...")
        self.listen_for_offers()

        # This thread will allow the client to receive and send messages once connected
        if self.tcp_socket:
            self.game_lobby()

    def reset(self): # Reset the client to its initial state
        print("Resetting...")
        self.server_name = None
        self.server_address = None
        self.tcp_socket = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 13117))
        self.running = True
        self.start()

    def listen_for_offers(self):
        while self.running and not self.tcp_socket:
            data, addr = self.udp_socket.recvfrom(1024)  # Buffer size is 1024 bytes
            if self.validate_offer(data):
                print(f"Received offer from server '{self.server_name}' at {addr[0]}, attempting to connect...") #todo: change message so it fits description
                self.server_address = (addr[0], int.from_bytes(data[37:39], byteorder='big'))
                self.connect_to_server()


    def validate_offer(self, data):
        magic_cookie, message_type = struct.unpack('!I B', data[:5])
        if magic_cookie == 0xabcddcba and message_type == 0x02:
            unpacked_data = struct.unpack('!I B 32s H', data)
            self.server_name = unpacked_data[2].decode().strip()
            return True
        return False

    # def connect_to_server(self): # before timeout version
    #     self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         self.tcp_socket.connect(self.server_address)
    #         self.tcp_socket.sendall((self.username + "\n").encode())
    #         response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
    #         while "name." in response:
    #             print(response)
    #             self.username = input("Enter a new username (using only letters, numbers or spaces): ")
    #             self.tcp_socket.sendall((self.username + "\n").encode())
    #             response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
    #         print(f"Connected to server {self.server_name} at {self.server_address[0]}")
    #     except Exception as e:
    #         print(f"Failed to connect to server: {e}")
    #         self.tcp_socket = None
    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(5)  # Set a timeout of 5 seconds
        try:
            self.tcp_socket.connect(self.server_address)
            self.tcp_socket.sendall((self.username + "\n").encode())
            response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            while "name." in response:
                print(response)
                self.username = input("Enter a new username (using only letters, numbers or spaces): ")
                self.tcp_socket.sendall((self.username + "\n").encode())
                response = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            if "! Hi "+self.username in response:
                print(f"Connected to server {self.server_name} at {self.server_address[0]}")
        except socket.timeout:
            print("Server is not responding. Connection attempt failed.")
            self.reset()
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.tcp_socket = None  # Reset the TCP socket
            self.reset()

    # def game_lobby(self): # before timeout version
    #     while self.running and self.tcp_socket:
    #         read_sockets, _, _ = select.select([self.tcp_socket], [], [])
    #         data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
    #         if data:
    #             print(data)
    #         if 'now!' in str(data):
    #             self.game_start()
    def game_lobby(self):
        while self.running and self.tcp_socket:
            try:
                read_sockets, _, _ = select.select([self.tcp_socket], [], [], 10)  # Set a timeout of 10 seconds
                if read_sockets:
                    data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
                    if data:
                        data = data.replace("<3\n","")
                        self.tcp_socket.sendall("<3".encode())
                        if data == "":
                            continue
                        print(data)
                    if 'now!' in str(data):
                        self.game_start()
                else:
                    # check if the server is still responding
                    print("Server is not responding. Exiting game.")
                    self.reset()
                    break
            except Exception as e:
                print(f"An error occurred: {e}\nResetting game...")
                self.reset()
                break

    # def game_start(self): before timeout version
    #     while self.running and self.tcp_socket:
    #         read_sockets, _, _ = select.select([self.tcp_socket], [], [])
    #         data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
    #         print(data)
    #         if 'Thanks for playing!' in data:
    #             self.stop()
    #             break

    #         if 'Round begins!' or "last question!" in data:#todo: input control
    #             participants = data.split("\nQ")[0]
    #             participants = participants.split("\'")[1:-1]
    #             if self.username in participants:
    #                 message = input("enter your answer (Y1T: for Yes \ NF0 for no)")
    #                 if message in ['0', 'N', 'n', 'f', 'F', '1', 'y', 'Y', 't', 'T']:
    #                     self.tcp_socket.sendall(message.encode())
    def game_start(self):
        # self.tcp_socket.settimeout(5)  # Set a timeout of 5 seconds
        while self.running and self.tcp_socket:
            try:
                read_sockets, _, _ = select.select([self.tcp_socket], [], [], 11)  # Set a timeout of 11 seconds
                if read_sockets:
                    data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
                    print(data)
                    if 'Thanks for playing!' in data:
                        self.reset()
                        break
                    if 'Round begins!' or "last question!" in data:
                        participants = data.split("\nQ")[0]
                        participants = participants.split("\'")[1:-1]
                        if self.username in participants:
                            message = self.input_timeout()
                            print(message)
                        if message != '!':
                            self.tcp_socket.sendall(message.encode())
                else:
                    print("Server is not responding. Exiting game.")
                    self.reset()
                    break
            except socket.timeout:
                print("Server is not responding. Exiting game.")
                self.reset()
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                self.reset()
                break

    def input_timeout(self):
        try:
            timer = time.time()
            message = inputimeout("enter your answer (\033[1;32m[Y,1,T]\033[0m for Yes \ \033[1;31m[N,F,0]\033[0m for no)", timeout=10)
            while message not in ['0', 'N', 'n', 'f', 'F', '1', 'y', 'Y', 't', 'T']:
                message = inputimeout("Invalid input. Please enter your answer (\033[1;32m[Y,1,T]\033[0m for Yes \ \033[1;31m[N,F,0]\033[0m for no)", timeout=10- (time.time()-timer))
        except TimeoutOccurred:
            message = '!'
        return message

    def stop(self):
        self.running = False
        if self.tcp_socket:
            self.tcp_socket.close()
        self.udp_socket.close()
        print("Client stopped.")

# Usage
if __name__ == "__main__":
    username = "yeled zevel"
    client = TriviaClient(username)
    client.start()