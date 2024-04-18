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
udp_port = 13117
tcp_port = 13118

# 
class TriviaServer:
    def __init__(self, host='0.0.0.0', tcp_port=tcp_port, udp_port=udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.clients = []
        self.running = True
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def start(self):
        self.setup_tcp_socket()
        udp_thread = threading.Thread(target=self.broadcast_offers)
        udp_thread.start()

        try:
            while self.running:
                client_socket, addr = self.tcp_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()
        finally:
            self.shutdown()

    def setup_tcp_socket(self):
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]  # Get the dynamically allocated port
        print(f"Server started, listening on IP {self.host} and port {self.tcp_port}")

    def broadcast_offers(self):
        message = struct.pack('!I B 32s H', 0xabcddcba, 0x02, b'MysticTriviaServer'.ljust(32), self.tcp_port)
        while self.running:
            self.udp_socket.sendto(message, ('<broadcast>', self.udp_port))
            time.sleep(1)

    def handle_client(self, client_socket, addr):
        print(f"Connected to {addr}")
        try:
            while True:
                data = client_socket.recv(1024)  # Adjust buffer size as needed
                if not data:
                    break
                # Process the data, respond to client
                print(f"Received data from {addr}: {data.decode()}")
                client_socket.sendall(data)  # Echo back the received data for now
        finally:
            client_socket.close()

    def shutdown(self):
        self.running = False
        self.tcp_socket.close()
        self.udp_socket.close()
        print("Server shutdown complete.")

# Usage
if __name__ == "__main__":
    server = TriviaServer()
    server.start()