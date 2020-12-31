import socket
import struct
import time
from threading import Thread
import colors
from scapy.arch import get_if_addr


class Server:
    """KeyBoard Spam Game Server!!!
        bonuses: colored printing and the top 5 players of the server statistics.
    """
    SUBNET_NAME = 'eth1'
    def __init__(self):
        self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # self.server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_port_number = 12000
        self.udp_port = 13117
        self.server_ip = get_if_addr(Server.SUBNET_NAME)
        self.udp_broad = "172.1.255.255"
        
        self.sever_buffer_size = 1024
        self.clients_connections = {}
        self.client_names = []
        self.group_one = {}
        self.group_two = {}
        self.counter_list = [0, 0]
        self.game_is_on = False
        self.first_connection = True
        self.all_time_players = {}
        

    def run_server(self):
        """
        This method runs until manual interrupt.
        runs 2 threads, one for UDP packets send, and one for TCP communication with the clients
        :return:
        """
        while True:
            t1 = Thread(target=self.send_udp_packet)
            t2 = Thread(target=self.run_tcp_socket)

            t1.start()
            t2.start()

            t1.join()
            t2.join()
            
            time.sleep(1)

    def send_udp_packet(self):
        """
        This function sends udp packets once in a second to all network users listening on port 13117 .
        packet will contain two verifying msgs and the tcp port number that the server is listening to.
        the server will wait for clients for 10 seconds.
        """
        finish_time = time.time() + 10
        print(colors.magenta + "Server started, listening on IP address {}".format(socket.gethostbyname(socket.gethostname())))               
        
        while time.time() < finish_time:
            message = struct.pack('Ibh', 0xfeedbeef, 0x2, self.tcp_port_number)                                        
            self.server_socket_udp.sendto(message, (self.udp_broad, self.udp_port))                                     
            time.sleep(1)
        print("server's UDP connection timeout")

        self.game_is_on = True
        self.first_connection = False
        self.deliver_announcment()
        self.start_game()
        self.finish_game()
        self.reset()

    def run_tcp_socket(self):
        """"
        This function connects clients to a TCP socket, gets their names, and splits them into 2 groups
        for the game.
        """
        if self.first_connection:            
            self.server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket_tcp.bind((self.server_ip, self.tcp_port_number))
            self.first_connection = False            

        self.server_socket_tcp.listen()
        self.server_socket_tcp.settimeout(5)

        group = 1
        while not self.game_is_on:
            try:
                connection_socket, client_address = self.server_socket_tcp.accept()
                bytes_name = connection_socket.recv(self.sever_buffer_size)
            except:
                break

            name = bytes_name.decode("utf-8").split("\n")[0]
            self.client_names.append(name)
            self.clients_connections[client_address[0]] = (connection_socket, name)

            if client_address[0] not in self.all_time_players:
                self.all_time_players[client_address[0]] = [0, name]

            if group == 1:
                self.group_one[client_address[0]] = (connection_socket, name)
                group = 2
            elif group == 2:
                self.group_two[client_address[0]] = (connection_socket, name)
                group = 1

    def deliver_announcment(self):
        """
        This function sends msg to all clients assigned to the current game.
        the content of the msg is the game purpose, and the 2 groups.
        :return:
        """
        msg = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n*****\n"
        for name in self.group_one.values():
            msg += name[1] + "\n"

        msg += "Group 2:\n*****\n"
        for name in self.group_two.keys():
            msg += name[2] + "\n"

        msg += "Start pressing keys on your keyboard as fast as you can!!\n"
        self.send_to_all_clients(msg)

    
    def start_game(self):
        """
        This function starts new Thread to each client playing the game.
        :return:
        """
        
        for idx, (client_name, connection_socket) in enumerate(self.clients_connections.items()):
            thread = Thread(target=self.update_counter, args=(client_name, connection_socket[0]))
            thread.start()
            thread.join()

    def update_counter(self, client_name, connection_socket):
        """
        each client's thread counts the amount of chars it sends, and incrementing the corresponding group counter
        game finishes after 10 seconds
        :param client_name:
        :param connection_socket:
        :return:
        """
        end_time = time.time() + 10
        connection_socket.settimeout(1)

        while time.time() < end_time:
            try:
                msg = connection_socket.recv(self.sever_buffer_size)
                msg = msg.decode("utf-8")
            except:
                continue

            if client_name in self.group_one:
                self.counter_list[0] += len(msg)
            if client_name in self.group_two:
                self.counter_list[1] += len(msg)

    def finish_game(self):
        """
        points are calculated, and the winner group is published.
        this msg interrupt the client and ends the game on the client side.
        when done, the server goes back to "send udp packets" mode.
        :return:
        """
        
        count_1 = self.counter_list[0]
        count_2 = self.counter_list[1]

        if count_1 > count_2:
            winner = "Group 1"
            winner_names = self.group_one

        elif count_1 < count_2:
            winner = "Group 2"
            winner_names = self.group_two
        else:
            winner = "no one"
            winner_names = {}

        msg = "Game over!\nGroup 1 typed in {} characters. Group 2 typed in {} characters.\n{} wins!\n\n" \
              "Congratulations to the winners:\n**********\n".format(count_1, count_2, winner)

        for ip, name in winner_names.items():
            msg += name[1] + "\n"
            self.all_time_players[ip][0] += 1

        msg += "\nGame over, sending out offer requests..."
        
        self.send_to_all_clients(msg)
        self.disconnect_all_clients()
      
        self.show_top_5()
    
    def disconnect_all_clients(self):
        for conn in self.clients_connections.values():
            conn[0].close()


    def send_to_all_clients(self, msg):
        """
        deliver a msg to all clients method
        :param msg:
        :return:
        """
        for address in self.clients_connections.values():
            address[0].send(msg.encode("utf-8"))

    def reset(self):
        """
        resets server's settings.
        """
        # for connection_socket in self.clients_connections.values():
        
        self.tcp_port_number = 12000
        self.sever_buffer_size = 1024
        self.clients_connections = {}
        self.client_names = []
        self.group_one = {}
        self.group_two = {}
        self.counter_list = [0, 0]
        self.game_is_on = False

        
    def show_top_5(self):
        if len(self.all_time_players) == 0:
            return

        print(colors.green + "\n\n===========================================\nHERE ARE THE TOP 5 PLAYERS OF ALL TIME:")
        sorted_players = {k: v for k, v in
                                   sorted(self.all_time_players.items(), key=lambda item: item[0], reverse=True)}

        for idx, (key, value) in enumerate(sorted_players.items()):
            if idx == 5:
                break
            else:
                print(colors.blue + "{}. IP address-{}: (Number of wins:{}, Name:{})"
                      .format(idx+1, key, value[0], value[1]) + colors.reset)
        print(colors.green + "===========================================\n\n" + colors.reset)

if __name__ == "__main__":
    server = Server()
    server.run_server()