import socket
from multiprocessing import Process, Manager, Value, Queue
import time
from threading import Thread

HEADERSIZE = 10

clients = []  # list of all connected clients
input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
host = socket.gethostbyname(socket.gethostname())
new_client = False  # this tells whether a new client is connected

processing_servers = [] # list of all connected processing servers. Useful for updating information


# this method receives images from client associated with client_id
def receive_images(client_id):
    s = time.time()
    global clients
    global HEADERSIZE
    full_msg = bytearray()
    new_msg = True
    receive_msg_size = HEADERSIZE
    header = ''
    while True:
        try:
            msg = clients[client_id].recv(receive_msg_size)
            full_msg.extend(msg)
            if new_msg:
                # make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                header += msg.decode()
                if len(header) < HEADERSIZE:
                    print("Error should happen here")
                    receive_msg_size = HEADERSIZE - len(header)
                    print("Current message size:", receive_msg_size)
                else:
                    msglen = int(header)
                    new_msg = False
            else:
                # ensure receiving full message
                remaining_len = msglen + HEADERSIZE - len(full_msg)

                receive_msg_size = remaining_len
                # Process fullly received message
                if len(full_msg) - HEADERSIZE == msglen:
                    e = time.time()
                    print(e - s)
                    return full_msg

        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            break


# this method will be called from 'def coordinator' process as a thread to accept new clients.
def accept_clients():
    global clients
    global input_server
    global new_client
    while True:
        client_socket, address = input_server.accept()
        clients.append(client_socket)
        time.sleep(1)
        new_client = True


# this process handle communications from clients and direct them (synchronously) to all processing servers
def coordinator(image, tasks_list, num_of_processing_server):
    global clients
    global new_client
    # this address and port is for clients to connect
    input_server.bind(("192.168.1.126", 2999))
    input_server.listen(5)

    Thread(target=accept_clients).start()  # start accepting clients

    # main task: receives messages from clients and direct them (synchronously) to processing servers
    while True:
        if new_client:
            image.append(None)
            tasks_list.extend([True] * num_of_processing_server.value)
            new_client = False

        if clients:
            for k in range(0, len(tasks_list), num_of_processing_server.value):
                if all(tasks_list[k:k + num_of_processing_server.value]):
                    try:
                        client_id = (len(tasks_list) // k) - 1
                    except ZeroDivisionError:
                        client_id = 0
                    message = receive_images(client_id)
                    image[client_id] = message
                    for i in range(k,
                                   k + num_of_processing_server.value):  # this will raise IndexOutOfBound if num_of_processing_server is updated before the task_list
                        tasks_list[i] = False
    # TODO: handle when a client disconnect


def handle_one_processing_server(image, tasks_list, ps_socket, process_id, num_of_processing_servers):
    global HEADERSIZE

    # update the task_list since a new processing server connected
    try:
        num_of_clients = len(tasks_list) // num_of_processing_servers.value
    except ZeroDivisionError:
        num_of_clients = 0
    tasks_list.extend([True] * num_of_clients)

    # we don't want to update num_of_processing_servers until we update the tasks_list to prevent IndexOutOfBound exception in coordinator process.
    num_of_processing_servers.value += 1
    ps_socket.settimeout(0.1)
    while True:
        if tasks_list:
            client_id = 0
            for i in range(process_id, len(tasks_list), num_of_processing_servers.value):
                if not tasks_list[i]:
                    if image[client_id] is not None:
                        message = image[client_id]
                        try:
                            ps_socket.send(message)
                        except socket.timeout:
                            print("skip a message")
                        tasks_list[i] = True
                        client_id += 1

    # TODO: Handle when a processing server disconnect


def main():
    global input_server
    print("Input Server Address:", "192.168.1.126", 6787)

    # this address and port is for processing servers to connect.
    input_server.bind(("192.168.1.126", 1999))
    input_server.listen(5)

    num_of_processing_server = Value('i', 0)  # keep track of the number of processing servers

    image = Manager().list(
        [None])  # this is the global storage for images received from clients. It is shared across all processes.

    tasks_list = Manager().list()  # this is use to synchronize the task for processes that handle processing servers' sockets.

    # start coordinator process.
    Process(target=coordinator, args=(image, tasks_list, num_of_processing_server)).start()

    # Accept new connection from processsing server.
    while True:
        ps_socket, address = input_server.accept()  # address is a tuple ("IP", port)
        print("A processing_server " + str(address) + "connected")
        Process(target=handle_one_processing_server, args=(
        image, tasks_list, ps_socket, num_of_processing_server.value - 1, num_of_processing_server)).start()


if __name__ == '__main__':
    main()
