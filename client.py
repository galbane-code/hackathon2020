import random
import socket
import struct
import time
from threading import Thread
import getch
import colors
from curtsies import Input
# import curses


class Client:
    magic_cookie = 0xfeedbeef
    offer = 0x2

    def __init__(self, name):
        self.name = name
        self.client_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) 
        self.client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
        self.udp_port = 13400
        self.client_buffer_size = 1024
        self.first_connection = True
        self.keep_playing = True
        self.client_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket_udp.bind(('', self.udp_port))

    def run_client(self):
        """
        This method runs the client until a manual interrupt.
        calls udp socket
        :return:
        """
        while True:
            self.udp_recv()
            
            self.client_socket_tcp.close()
            self.client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            

    def udp_recv(self):
        """
        the client will wait for UDP packets on a specific port coming from a server.
        the client will validate the packet, and will recieve\decline the sender's offer.
        :return:
        """
        print(colors.yellow + "Client started, listening for offer requests...")          
        self.first_connection = False

        end = time.time() + 5
        keep_alive = True
        while keep_alive and time.time() < end:
            try:
                
                msg, server_address = self.client_socket_udp.recvfrom(self.client_buffer_size)
                
                msg_unpacked = struct.unpack("Ibh", msg)
            except:
                print("from run udp recieve client")
                continue

            if msg_unpacked[0] == Client.magic_cookie and msg_unpacked[1] == Client.offer:
                tcp_server_port = msg_unpacked[2]
                server_ip = "172.1.0.137"
                keep_alive = False

                self.tcp_connection(server_ip, tcp_server_port)
                

    def tcp_connection(self, server_ip, tcp_server_port):
        """
        After client approved connection, it will send its name to the server.
        the client waits to a msg from the sender about and displays it.
        :param server_ip:
        :param tcp_server_port:
        :return:
        """
        
        print(colors.yellow + "Received offer from {} attempting to connect...​".format(server_ip))
        try:
        
            self.client_socket_tcp.connect((server_ip, tcp_server_port))

            self.client_socket_tcp.send(("{}\n".format(self.name)).encode("utf-8"))
            msg = self.client_socket_tcp.recv(self.client_buffer_size)
            self.show_msg(msg)
            self.play_game()
        except:
            # print("problem")
            return

    def show_msg(self, msg):
        """
        prints msgs from sender to the screen
        :param msg:
        :return:
        """
        msg = msg.decode("utf-8").split("\n")

        for idx, s in enumerate(msg):
            if s != "":
                i = random.randint(0, len(colors.colors) - 1)
                print(colors.colors[i] + s + colors.reset)

    def show_winner(self, msg):
        """
        prints msgs from sender to the screen
        :param msg:
        :return:
        """
        msg = msg.decode("utf-8").split("\n")

        print("\n")
        for idx, s in enumerate(msg):
            if s != "":
                print(colors.winner + s + colors.reset)

    def play_game(self):
        """
        Two threads run in the client - one for listening to server's msgs, and one for playing the game.
        This methods receives chars a input from the user and sends it to the server.
        thw while condition is changed by the "listener" thread of the client, tells it to stop playing the game.
        when done, the clients goes back to "udp listen" mode.
        :return:
        """
        Thread(target=self.listen).start()
        
        while self.keep_playing:
            
            try:
                with Input(keynames='curtsies') as input_generator: 
                    char = input_generator.send(0.1)
                    if char:
                        self.client_socket_tcp.send(char.encode("utf-8"))
            except:
                # print("from play game")
                continue         
        
        self.keep_playing = True

        print("Server disconnected, listening for offer requests...")

    def listen(self):
        """
        listens to server's msgs inorder to tell the client when the game is closed by the server.
        :return:
        """
        while True:
            try:
                msg = self.client_socket_tcp.recv(self.client_buffer_size)
                if msg:
                    self.show_winner(msg)
                if not msg:                    
                    self.keep_playing = False
                    
                    break
            except:
                # print("from listen")
                continue


if __name__ == "__main__":
    client = Client("oogie")
    client.run_client()