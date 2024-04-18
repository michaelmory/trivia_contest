import socket
import threading
import struct
import selectors
import logging
import os
import time

trivia_questions = [
    ("Is HTTP a stateless protocol?", True),
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
server_name = "Mystic"
udp_port = 13117
tcp_port = 1337
min_clients = 2 # start 10 second timer after a player connects and len(self.clients) >= min_clients

# when debug=True, the server will print debug messages
class TriviaServer:
    def __init__(self, host=server_ip, name = server_name, tcp_port=tcp_port, udp_port=udp_port, debug=False):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.name = name
        self.clients = {}  # {client_name: client_socket}
        self.state = 1 # 0 = shutdown, 1 = waiting for clients, 2 = trivia game in progress
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.game_timer = None
        # debug section
        self.debug = debug
        self.tcp_socket.settimeout(1)  # Set a timeout of 1 second
        self.udp_socket.settimeout(1)  # Set a timeout of 1 second

    def start(self):
        self.setup_tcp_socket()
        udp_thread = threading.Thread(target=self.broadcast_offers)
        udp_thread.start()
        try:
            while self.state == 1:
                try:
                    client_socket, addr = self.tcp_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    client_thread.start()
                except socket.timeout:
                    continue  # If the accept() call times out, just continue the loop
        except KeyboardInterrupt:
            print("\nInterrupt received! Shutting down server...")
            self.state = 0
        finally:
            self.shutdown()

    def setup_tcp_socket(self):
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]  # Get the dynamically allocated port
        print(f"Server started, listening on IP {self.host} and port {self.tcp_port}")

    def broadcast_offers(self):
        message = struct.pack('!I B 32s H', 0xabcddcba, 0x02, self.name.encode().ljust(32), self.tcp_port)
        while self.state:
            self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
            if self.debug:
                print(f"Broadcasting server offer to port {self.udp_port}, Clients: {[k[:-1] for k in self.clients.keys()]}")
            time.sleep(1)

    def handle_client(self, client_socket, addr):
        print(f"Connected to {addr}")
        try:
            while True:
                data = client_socket.recv(1024)  # Adjust buffer size as needed
                if not data:
                    break
                # Process the data, respond to client
                msg = data.decode()
                print(f"Received data from {addr}: {msg}")
                # add the client to the list of clients
                self.clients[msg] = client_socket
                client_socket.sendall(data)  # Echo back the received data for now
        finally:
            client_socket.close()

    def shutdown(self):
        self.state = 0
        # disconnect all clients
        for _, client in self.clients.items():
            client.close()
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