import socket
import threading
import select
import sys
import struct

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
            self.communicate()


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

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect(self.server_address)
            self.tcp_socket.sendall((self.username + "\n").encode())
            print(f"Connected to server {self.server_name} at {self.server_address[0]}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.tcp_socket = None

    def communicate(self):

        self.game_lobby()

        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            for sock in read_sockets:
                if sock == sys.stdin:
                    message = sys.stdin.readline()
                    print(f' the message is {message}')
                    self.tcp_socket.sendall(message.encode())
                else:
                    response = sock.recv(1024)
                    if not response:
                        print("Server disconnected.")
                        self.running = False
                    else:
                        print(response.decode(), end='')

    def game_lobby(self):
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'now' in str(data):
                self.game_start()
    def game_start(self):
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'Thanks for playing!' in data:
                self.stop()
                break

            if 'Round begins!' in data:#todo: input control
                participants = data.split("\nQ")[0]
                participants = participants.split(", ")[1:]
                if self.username in participants:
                    message = input("enter your answer (Y1T: for Yes \ NF0 for no)")
                    if message in ['0', 'N', 'n', 'f', 'F', '1', 'y', 'Y', 't', 'T']:
                        self.tcp_socket.sendall(message.encode())

    def stop(self):
        self.running = False
        if self.tcp_socket:
            self.tcp_socket.close()
        self.udp_socket.close()
        print("Client stopped.")

# Usage
if __name__ == "__main__":
    username = input("Enter your username: ")
    client = TriviaClient(username)
    client.start()