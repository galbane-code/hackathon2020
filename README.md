# hackathon2020
Using client-server architecture we built keyboard-spamming game.
users connect to the server by recieving udp packets sent as <broadcast> msgs containing information about a TCP connection to the game server.
clients play against each other trying to send as many chars as possible to the server. the winner ia announced, being writen in an overall-winners table, and the server is then ready 
for another game to begin.
