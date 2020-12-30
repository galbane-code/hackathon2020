import server
import client
import threading

# while True:
server = server.Server()
client1 = client.Client("mr.oogiia")
client2 = client.Client("bibi")
client3 = client.Client("benet")


t1 = threading.Thread(target=server.run_server)
# t3 = threading.Thread(target=server.run_tcp_socket)
#
t2 = threading.Thread(target=client1.run_client)
t4 = threading.Thread(target=client2.run_client)
t5 = threading.Thread(target=client3.run_client)
#
# t3.start()
t1.start()
t2.start()

# t4.start()
# t5.start()
