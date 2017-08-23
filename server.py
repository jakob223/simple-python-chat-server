# Tcp Chat server

import socket, select
import random

class Server(object):
    # List to keep track of socket descriptors
    CONNECTION_LIST = []
    RECV_BUFFER = 4096  # Advisable to keep it as an exponent of 2
    PORT = 5000

    def __init__(self):
        self.user_name_dict = {}
        self.victim = 0
        self.bodysnatcher = 0
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_up_connections()
        self.client_connect()

    def set_up_connections(self):
        # this has no effect, why ?
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.PORT))
        self.server_socket.listen(10)  # max simultaneous connections.

        # Add server socket to the list of readable connections
        self.CONNECTION_LIST.append(self.server_socket)

        
    def choose_bodysnatcher_and_victim(self):
        options = [sock for sock in self.CONNECTION_LIST if sock != self.server_socket]
        self.bodysnatcher, self.victim = random.sample(options, 2)
        bodysnatcher_username = self.user_name_dict[self.bodysnatcher]
        victim_username = self.user_name_dict[self.victim].username
        self.victims = set()
        self.victims.add(self.victim)
        
        self.bodysnatcher.send("You're the bodysnatcher. You've snatched %s's body. To communicate with them secretly, send a message starting with '$'.\n\n" % victim_username)
        self.victim.send("You've been bodysnatched. Any messages you send will go only to the bodysnatcher.\n\n")
    
    def choose_new_victim(self):
        options = [sock for sock in self.CONNECTION_LIST if sock != self.server_socket]
        options = list(set(options) - self.victims - set([self.bodysnatcher]))
        if len(options) == 0:
            self.broadcast_data(0,"GAME OVER\n\n")
            return
        self.victim = random.choice(options)
        self.victims.add(self.victim)
        victim_username = self.user_name_dict[self.victim].username
        
        self.bodysnatcher.send("Your new victim is %s\n\n" % victim_username)
        self.victim.send("You've been bodysnatched. Any messages you send will go only to the bodysnatcher.\n\n")
        

    # Function to broadcast chat messages to all connected clients
    def broadcast_data(self, sock, message):
        # Do not send the message to master socket and the client who has send us the message
        for socket in self.CONNECTION_LIST:
            if socket != self.server_socket and socket != sock:
                # if not send_to_self and sock == socket: return
                try:
                    socket.send(message)
                except:
                    # broken socket connection may be, chat client pressed ctrl+c for example
                    socket.close()
                    self.CONNECTION_LIST.remove(socket)

    def send_data_to(self, sock, message):
        try:
            sock.send(message)
        except:
            # broken socket connection may be, chat client pressed ctrl+c for example
            socket.close()
            self.CONNECTION_LIST.remove(sock)

    def client_connect(self):
        print "Chat server started on port " + str(self.PORT)
        while 1:
            # Get the list sockets which are ready to be read through select
            read_sockets, write_sockets, error_sockets = select.select(self.CONNECTION_LIST, [], [])

            for sock in read_sockets:
                # New connection
                if sock == self.server_socket:
                    # Handle the case in which there is a new connection recieved through server_socket
                    self.setup_connection()
                # Some incoming message from a client
                else:
                    # Data recieved from client, process it
                    # try:
                        # In Windows, sometimes when a TCP program closes abruptly,
                        # a "Connection reset by peer" exception will be thrown
                        data = sock.recv(self.RECV_BUFFER)
                        if data:
                            if self.user_name_dict[sock].username is None:
                                self.set_client_user_name(data, sock)
                            else:
                                if data[:7]=="NEWGAME":
                                    self.broadcast_data(sock,"NEW GAME---------------------------------------\n\n\n\n-----------------------------------------\n")
                                    self.choose_bodysnatcher_and_victim()
                                elif data[:9]=="NEWVICTIM":
                                    self.broadcast_data(sock,"NEW VICTIM---------------------------------------")
                                    self.choose_new_victim()
                                elif sock == self.victim:
                                    self.bodysnatcher.send("<VICTIM> " + data)
                                elif sock == self.bodysnatcher:
                                    if data[0] == "$":
                                        self.victim.send('<BODYSNATCHER> ' + data[1:])
                                    else:
                                        self.broadcast_data(sock, "\r" + '<' + self.user_name_dict[self.victim].username + '> ' + data)
                                else:
                                    self.broadcast_data(sock, "\r" + '<' + self.user_name_dict[sock].username + '> ' + data)

                    # except:
         #
         #                self.broadcast_data(sock, "Client (%s, %s) is offline" % addr)
         #                print "Client (%s, %s) is offline" % addr
         #                sock.close()
         #                self.CONNECTION_LIST.remove(sock)
         #                continue

        self.server_socket.close()

    def set_client_user_name(self, data, sock):
        self.user_name_dict[sock].username = data.strip()
        self.send_data_to(sock, data.strip() + ', you are now in the chat room\n')
        self.send_data_to_all_regesterd_clents(sock, data.strip() + ' has joined the chat room\n')

    def setup_connection(self):
        sockfd, addr = self.server_socket.accept()
        self.CONNECTION_LIST.append(sockfd)
        print "Client (%s, %s) connected" % addr
        self.send_data_to(sockfd, "please enter a username: ")
        self.user_name_dict.update({sockfd: Connection(addr)})

    def send_data_to_all_regesterd_clents(self, sock, message):
        for local_soc, connection in self.user_name_dict.iteritems():
            if local_soc != sock and connection.username is not None:
                self.send_data_to(local_soc, message)


class Connection(object):
    def __init__(self, address):
        self.address = address
        self.username = None


if __name__ == "__main__":
    server = Server()