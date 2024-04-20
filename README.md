# trivia_contest
Final Project for our Information Communications Course at BGU

## Overview
This repository contains the Python source code for a local network Server-Client trivia game. The server broadcasts offers over UDP, the clients connect over TCP, and then answer True or False questions.

## Files
- `trivia_server.py`: Implements the game server using TCP and UDP sockets and manages the game.
- `trivia_player.py`: Defines a Player class to manage each player's connection and gameplay.
- `trivia_client.py`: A regular client that a player can use to connect to the server and play the trivia game.
- `trivia_bot.py`: A bot that connects to the servers and answers questions randomly.

## Game Rules
- The server waits for at least two clients to connect before starting the game.
- Questions are asked one at a time to all players, and they must answer within 10 seconds.
- Players who answered correctly within the time frame go on to the next round, while players who answered wrong are eliminated and become spectators.
- The game continues until only one player remains, or a tie breaking last round.
