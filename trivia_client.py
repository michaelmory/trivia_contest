import socket
import threading
import select
import sys
import struct

class TriviaClient:
    def __init__(self, username="Player"):
        self.username = username
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
            communication_thread = threading.Thread(target=self.communicate)
            communication_thread.start()

    def listen_for_offers(self):
        while self.running and not self.tcp_socket:
            data, addr = self.udp_socket.recvfrom(1024)  # Buffer size is 1024 bytes
            if self.validate_offer(data):
                print(f"Received offer from server at {addr[0]}") #todo: change message so it fits description
                self.server_address = (addr[0], int.from_bytes(data[37:39], byteorder='big'))
                self.connect_to_server()


    def validate_offer(self, data):
        magic_cookie, message_type = struct.unpack('!I B', data[:5])
        if magic_cookie == 0xabcddcba and message_type == 0x02:
            return True
        return False

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect(self.server_address)
            self.tcp_socket.sendall((self.username + "\n").encode())
            print(f"Connected to server {self.server_address[0]}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.tcp_socket = None

    def communicate(self):
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([sys.stdin, self.tcp_socket], [], [])
            for sock in read_sockets:
                if sock == sys.stdin:
                    message = sys.stdin.readline()
                    self.tcp_socket.sendall(message.encode())
                else:
                    response = sock.recv(1024)
                    if not response:
                        print("Server disconnected.")
                        self.running = False
                    else:
                        print(response.decode(), end='')

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