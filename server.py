import os
import socket
import select
import utils
import threading
from contextlib import suppress


class FTPServer(threading.Thread):

    MSG_BUFFER = 8192
    MAX_CONNECTIONS = 10

    def __init__(self):
        """
        :param port:
        """
        threading.Thread.__init__(self)
        self.dir = os.getcwd()
        self.port = utils.check_args_port()
        self.public_ip = utils.get_ip_address()
        self.srv_socket = None
        self.server_is_running = False
        self.conns = []

    # Commands
    def list_files(self):
        files_dirs = os.walk(self.dir)
        file_list = "'\n- ".join( [x[0].replace(self.dir, '') for x in files_dirs if x[0].replace(self.dir, '') != ''])
        return "".join(["List of all files in path: %s/\n" % os.getcwd(), file_list])

    def send_file_to_client(self, conn, filename):
        if filename not in os.listdir(os.getcwd()):
            print("Not Found On Server")
        else:
            print(filename + " File Found")
            upload = open(os.getcwd()+'/'+filename, 'rb')
            data = upload.read(4096)
            while data:
                conn.sendall(data)
                data = upload.read(4096)
            print("Sending file: complete")

    def save_file_from_client(self, conn, filename):
        return "uploading file from client "+str(filename)

    # Main Program
    def loop_socket_check(self):

        while self.server_is_running:

            with suppress(socket.error):
                # Using select.select to obtain the read ready sockets in the connections list (self.conns)
                read_connections = select.select(self.conns, [], [], 30)[0]

            for connection in read_connections:

                if connection == self.srv_socket:
                    try:
                        cli_sock, (ip, port) = self.srv_socket.accept()
                    except socket.error:
                        break
                    self.conns.append(cli_sock)
                    print("[CON] Client [%s:%s] has connected\n" % (ip, port))

                else:
                    try:
                        args = connection.recv(1024).decode('utf')
                        args = args.split(" ")

                        if args:

                            ip, port = connection.getpeername()

                            if args[0] == "list":
                                print("[CMD] Client [%s:%s] has executed command: LIST" % (ip, port))
                                self.list_files()

                            elif args[0] == "put":
                                filename = args[1]
                                print("[CMD] Client [%s:%s] has executed command: PUT %s" % (ip, port, filename))
                                res = self.save_file_from_client(connection, filename)
                                print(res)

                            elif args[0] == "get":
                                filename = args[1]
                                print("[CMD] Client [%s:%s] has executed command: GET %s" % (ip, port, filename))
                                self.send_file_to_client(connection, filename)

                    except socket.error:
                        ip, port = connection.getpeername()
                        connection.close()
                        self.conns.remove(connection)
                        print("[DIS] Client [%s:%s] has disconnected\n" % (ip, port))

    def start(self):

        #utils.clear_terminal()

        print(
            "\nLaunching server at:"
            "\n- IP: %s"
            "\n- Port: %s"
            "\n- Directory: %s"
            "\n" % (self.public_ip, self.port, self.dir)
        )

        # Create socket and add to connections list
        self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind(('', self.port))
        self.srv_socket.listen(self.MAX_CONNECTIONS)
        self.conns.append(self.srv_socket)
        self.server_is_running = True

        print("Waiting for client(s) to connect...\n")

        # Loop checking server for new connections and data
        self.loop_socket_check()

        # If self.server_is_running is false, close server.
        self.srv_socket.close()


if __name__ == '__main__':
    server = FTPServer()
    server.start()
