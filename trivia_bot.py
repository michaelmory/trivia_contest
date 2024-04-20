from trivia_client import TriviaClient
import select
import random
import struct
import socket

class TriviaBot(TriviaClient):

    def __init__(self):
        """
        Initialize the TriviaBot with a random name.
        child of TriviaClient
        no input or output
        """
        # name = f"BOT-{random.choice(['Yosi','Nahum','Rahamim','Shimon','Yohai', 'Takum', 'Human Person', 'Mom', 'Dad', 'Your Ex'])}"
        super().__init__("BOT-") # Initialize the bot with a random name

    def game_start(self):  # Start the game, same as the client's game_start but randomizes the answer
        """
        Start the game. This function listens for the server's messages and sends a random answer to the server.
        no input or output
        """
        while self.running and self.tcp_socket:
            read_sockets, _, _ = select.select([self.tcp_socket], [], [])
            data = self.tcp_socket.recv(1024).decode().replace(r"\n","\n")
            print(data)
            if 'Disconnected by the server.' in data: # If the game is over, reset the client
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