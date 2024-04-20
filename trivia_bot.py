from trivia_client import TriviaClient
import select
import random
import struct
import socket

class TriviaBot(TriviaClient):

    def __init__(self):
        # name = f"BOT-{random.choice(['Yosi','Nahum','Rahamim','Shimon','Yohai', 'Takum', 'Human Person', 'Mom', 'Dad', 'Your Ex'])}"
        super().__init__("BOT-")

    def game_start(self):
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'Thanks for playing!' in data:
                self.reset()
                break
            if 'Round begins!' or "last question!" in data:
                participants = data.split("\nQ")[0]
                participants = participants.split("\'")[1:-1]
                if self.username in participants:
                    message = random.choice(['y', 'n'])
                    print(message)
                    self.tcp_socket.sendall(message.encode())

if __name__ == "__main__":
    client = TriviaBot()
    client.start()