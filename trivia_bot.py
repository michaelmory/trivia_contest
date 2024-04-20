from trivia_client import TriviaClient
import select
import random
import struct
import socket

class TriviaBot(TriviaClient):

    def __init__(self):
        name = f"BOT-{random.choice(['Yosi','Nahum','Rahamim','Shimon','Yohai'])}"
        super().__init__(name)

    def game_start(self):
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'Thanks' in data:
                self.stop()
                break

            if 'Question' in data: #todo: input control
                message = random.choice(['y', 'n'])
                self.tcp_socket.sendall(message.encode())

if __name__ == "__main__":
    client = TriviaBot()
    client.start()