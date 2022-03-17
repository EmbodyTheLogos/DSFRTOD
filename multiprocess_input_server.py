import socket
from multiprocessing import Process, Manager, Value, Lock
import time
import sys
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
                    #print(e - s)
                    return full_msg

        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            del clients[client_id]
            return "client disconnected"
            break


# this method will be called from 'coordinator' process as a thread to accept new clients.
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
def coordinator(images, tasks_list, num_of_processing_servers, num_of_clients):
    global clients
    global new_client
    # this address and port is for clients to connect
    input_server.bind(("192.168.1.126", 2999))
    input_server.listen(5)

    Thread(target=accept_clients).start()  # start accepting clients

    # main task: receives images from clients and direct them (synchronously) to processing servers
    while True:
        if new_client:
            images.append(None)
            tasks_list.extend([True] * num_of_processing_servers.value)
            num_of_clients.value += 1
            new_client = False

        if clients:
            try:
                for k in range(0, len(tasks_list), num_of_processing_servers.value):
                    if all(tasks_list[k:k + num_of_processing_servers.value]):
                        try:
                            client_id = (len(tasks_list) // k) - 1
                        except ZeroDivisionError:
                            client_id = 0
                        message = receive_images(client_id)
                        if message != "client disconnected":
                            images[client_id] = message
                            try:
                                for i in range(k, k + num_of_processing_servers.value):  # this will raise IndexOutOfBound if num_of_processing_servers is updated before the task_list
                                    tasks_list[i] = False
                            except IndexError:
                                # when the task_list is updating, we allow Index out of bound error to occur during that time
                                pass
                        else:
                            # when a client disconnected, we want to update the task_list
                            for i in range(num_of_processing_servers.value):
                                tasks_list.pop()
                            # remove a spot from images list
                            images.pop()
            except ValueError:
                # for k in range(0, len(tasks_list), num_of_processing_servers.value):
                #           ValueError: range() arg 3 must not be zero
                # This means no processing servers is connected.
                pass


def handle_one_processing_server(images, tasks_list, ps_socket, process_id, num_of_processing_servers, lock_update):
    global HEADERSIZE

    print("hi")
    ps_socket.settimeout(10)
    while True:
        if tasks_list:
            client_id = 0
            for i in range(process_id, len(tasks_list), num_of_processing_servers.value):
                try:
                    if type(tasks_list[i]) is int:
                        # update process_id when a processing server disconnected
                        process_id = tasks_list[i]
                        print(process_id)
                        tasks_list[i] = False
                        break
                    if not tasks_list[i]:
                        if images[client_id] is not None:
                            message = images[client_id]
                            try:
                                ps_socket.send(message)
                            except socket.timeout:
                                try:
                                    ps_socket.settimeout(10)
                                    message = "skip".encode()
                                    header = f'{len(message):<{HEADERSIZE}}'.encode()
                                    message = header + message
                                    ps_socket.send(message)
                                    ps_socket.settimeout(0.1)
                                except socket.timeout:
                                    raise ConnectionResetError
                                except (ConnectionResetError, ConnectionAbortedError):
                                    print("A processing server disconnected", ps_socket)
                                    ps_socket.close()
                                    # ensure only one process can update at a time
                                    lock_update.acquire() # acquire the lock for updating

                                    # Update task_list
                                    # invalidate the cells that this processes currently occupied.
                                    for l in range(process_id, len(tasks_list), num_of_processing_servers.value):
                                        tasks_list[l] = None

                                    # inform other processes that has process_id greather than this process's id to decrease its process_id by 1
                                    for k in range(process_id + 1, num_of_processing_servers.value):
                                        tasks_list[k] = k - 1

                                    # give the other processes sometimes to update the process_id
                                    time.sleep(2)

                                    # delete the cells that this processes currently occupied.
                                    for l in reversed(range(process_id, len(tasks_list), num_of_processing_servers.value)):
                                        if l >= 0:
                                            del tasks_list[l]
                                    num_of_processing_servers.value -= 1
                                    lock_update.release() # release the lock
                                    sys.exit()

                            # TODO: Handle when a processing server disconnect
                            except (ConnectionResetError, ConnectionAbortedError):
                                print("A processing server disconnected", ps_socket)
                                ps_socket.close()

                                # ensure only one process can update at a time
                                lock_update.acquire()  # acquire the lock for updating

                                # Update task_list
                                # invalidate the cells that this processes currently occupied.
                                for l in range(process_id, len(tasks_list), num_of_processing_servers.value):
                                    tasks_list[l] = None

                                # inform other processes that has process_id greather than this process's id to move back an index in task_list
                                for k in range(process_id + 1, num_of_processing_servers.value):
                                    tasks_list[k] = k - 1

                                # give the other processes sometimes to update
                                time.sleep(2)

                                # delete the cells that this processes currently occupied.
                                for l in reversed(range(process_id, len(tasks_list), num_of_processing_servers.value)):
                                    if l >= 0:
                                        del tasks_list[l]
                                num_of_processing_servers.value -= 1
                                lock_update.release() # release the lock
                                sys.exit()

                            tasks_list[i] = True
                            client_id += 1
                except IndexError:
                    # when the task_list is updating, we allow Index out of bound error to occur during that time
                    pass


def main():
    global input_server
    print("Input Server Address:", "192.168.1.126", 6787)

    # this address and port is for processing servers to connect.
    input_server.bind(("192.168.1.126", 1999))
    input_server.listen(5)

    num_of_processing_servers = Value('i', 0)  # keep track of the number of processing servers
    num_of_clients = Value('i', 0) # keep track of the number of clients
    lock_update = Lock() # ensure only one process can update task_list when a processing servers disconnect

    images = Manager().list(
        [None])  # this is the global storage for images received from clients. It is shared across all processes.

    tasks_list = Manager().list()  # used for synchronization of processes that handle processing servers' sockets.

    # start coordinator process.
    Process(target=coordinator, args=(images, tasks_list, num_of_processing_servers, num_of_clients)).start()

    # Accept new connection from processing server.
    while True:
        ps_socket, address = input_server.accept()  # address is a tuple ("IP", port)
        print("A processing_server " + str(address) + "connected")
        print("process id", num_of_processing_servers.value)


        tasks_list.extend([True] * num_of_clients.value)
        print("task list length", len(tasks_list))
        num_of_processing_servers.value += 1
        Process(target=handle_one_processing_server, args=(
        images, tasks_list, ps_socket, num_of_processing_servers.value-1, num_of_processing_servers, lock_update)).start()


if __name__ == '__main__':
    main()
