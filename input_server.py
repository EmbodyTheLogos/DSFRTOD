import socket
from multiprocessing import Process, Manager, Value, Lock
import time
import sys
from threading import Thread

HEADERSIZE = 10

clients = []  # list of all connected clients
input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
# host = socket.gethostbyname(socket.gethostname())
host = "0.0.0.0"
new_client = False  # this tells whether a new client is connected

processing_servers = []  # list of all connected processing servers. Useful for updating information


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
                    # print(e - s)
                    return full_msg

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            print("Disconnected from input_server")
            del clients[client_id]
            return "client disconnected"
            break


# this method will be called from 'coordinator' process as a thread to accept new clients.
def accept_clients():
    global clients
    global input_server
    global new_client
    # this address and port is for processing servers to connect.
    input_server.bind((host, 6788))
    input_server.listen(5)
    while True:
        client_socket, addr1ess = input_server.accept()
        print("a client connected")
        if len(clients) == 0:
            clients.append(client_socket)
        else:
            clients[0] = client_socket
        time.sleep(1)
        new_client = True


# check if all elements in the list are true, except those who have None as values.
def all_true(tasks_done):
    for task in tasks_done:
        if task != None and task == False:
            return False
    return True


# this process handle communications from clients and direct them (synchronously) to all processing servers
def coordinator(images, tasks_done, num_of_processing_servers, num_of_clients):
    global clients
    global new_client  # bool

    # TODO: add id to each image received from all clients.
    image_id = 1  # use this to identify each images sent. Very useful for synchronizing the results in output_server.

    Thread(target=accept_clients).start()  # start accepting clients

    # main task: receives images from clients and direct them (synchronously) to processing servers
    while True:
        if new_client:
            images[0] = None
            new_client = False

        if clients:  # if clients is not empty
            # print(clients)
            if all_true(tasks_done):
                message = receive_images(0)
                # print("received message from client")
                if message != "client disconnected":
                    images[0] = message

                for i in range(len(tasks_done)):
                    if tasks_done[i] is not None:
                        tasks_done[i] = False
                # try:
                #     for i in range(num_of_processing_servers.value):  # this will raise IndexOutOfBound if num_of_processing_servers is updated before the tasks_done
                #         tasks_done[i] = False
                # except IndexError:
                #     # when the tasks_done is updating, we allow Index out of bound error to occur during that time
                #     pass


def handle_one_processing_server(images, tasks_done, ps_socket, process_id, num_of_processing_servers, lock_update):
    global HEADERSIZE
    
    time.sleep(1) # make sure the worker called recv() before sending data to the worker. This ensure no data lost.
                        # if send() is called before recv(), then recv() will not read the full message that has been sent.

    ps_socket.settimeout(10)  # max time to send each image
    while True:
        if not tasks_done[process_id]:
            if images[0] is not None:
                message = images[0]  # this will still throw exception since it could happen that immediately after the if statement, images[0] is set to None by coordinator
                try:
                    ps_socket.send(message)
                except socket.timeout:
                    pass
                except TypeError:
                    print("image cannot be None")
                except ConnectionResetError or BrokenPipeError or ConnectionAbortedError:
                    print("worker", process_id, "disconnected")
                    num_of_processing_servers.value -= 1
                    tasks_done[process_id] = None
                    return
            tasks_done[process_id] = True
            # TODO: when a processor disconnect


#     while True:
#         if tasks_done:
#             client_id = 0
#             for i in range(process_id, len(tasks_done), num_of_processing_servers.value):
#                 try:
#                     if type(tasks_done[i]) is int:
#                         # update process_id when a processing server disconnected
#                         process_id = tasks_done[i]
#                         print(process_id)
#                         tasks_done[i] = False
#                         break
#                     if not tasks_done[i]:
#                         if images[client_id] is not None:
#                             message = images[client_id]
#                             try:
#                                 ps_socket.send(message)
#                             except socket.timeout:
#                                 try:
#                                     #ps_socket.settimeout(10)
#                                     message = "skip".encode()
#                                     header = f'{len(message):<{HEADERSIZE}}'.encode()
#                                     message = header + message
#                                     ps_socket.send(message)
#                                     #ps_socket.settimeout(10)
#                                 except socket.timeout:

#                                     # disconnect a processing server after 2 seconds of no response
#                                     print("A processing server disconnected (timeout)", ps_socket)
#                                     ps_socket.shutdown(socket.SHUT_RDWR)
#                                     ps_socket.close()
#                                     # ensure only one process can update at a time
#                                     lock_update.acquire()  # acquire the lock for updating

#                                     # Update tasks_done
#                                     # invalidate the cells that this processes currently occupied.
#                                     for l in range(process_id, len(tasks_done), num_of_processing_servers.value):
#                                         tasks_done[l] = None

#                                     # inform other processes that has process_id greather than this process's id to decrease its process_id by 1
#                                     for k in range(process_id + 1, num_of_processing_servers.value):
#                                         tasks_done[k] = k - 1

#                                     # give the other processes sometimes to update the process_id
#                                     time.sleep(2)

#                                     # delete the cells that this processes currently occupied.
#                                     for l in reversed(
#                                             range(process_id, len(tasks_done), num_of_processing_servers.value)):
#                                         if l >= 0:
#                                             del tasks_done[l]
#                                     num_of_processing_servers.value -= 1
#                                     lock_update.release()  # release the lock
#                                     sys.exit()

#                                 except (ConnectionResetError, ConnectionAbortedError):
#                                     print("A processing server disconnected", ps_socket)
#                                     ps_socket.close()
#                                     # ensure only one process can update at a time
#                                     lock_update.acquire() # acquire the lock for updating

#                                     # Update tasks_done
#                                     # invalidate the cells that this processes currently occupied.
#                                     for l in range(process_id, len(tasks_done), num_of_processing_servers.value):
#                                         tasks_done[l] = None

#                                     # inform other processes that has process_id greather than this process's id to decrease its process_id by 1
#                                     for k in range(process_id + 1, num_of_processing_servers.value):
#                                         tasks_done[k] = k - 1

#                                     # give the other processes sometimes to update the process_id
#                                     time.sleep(2)

#                                     # delete the cells that this processes currently occupied.
#                                     for l in reversed(range(process_id, len(tasks_done), num_of_processing_servers.value)):
#                                         if l >= 0:
#                                             del tasks_done[l]
#                                     num_of_processing_servers.value -= 1
#                                     lock_update.release() # release the lock
#                                     sys.exit()

#                             # TODO: Handle when a processing server disconnect
#                             except (ConnectionResetError, ConnectionAbortedError):
#                                 print("A processing server disconnected", ps_socket)
#                                 ps_socket.close()

#                                 # ensure only one process can update at a time
#                                 lock_update.acquire()  # acquire the lock for updating

#                                 # Update tasks_done
#                                 # invalidate the cells that this processes currently occupied.
#                                 for l in range(process_id, len(tasks_done), num_of_processing_servers.value):
#                                     tasks_done[l] = None

#                                 # inform other processes that has process_id greather than this process's id to move back an index in tasks_done
#                                 for k in range(process_id + 1, num_of_processing_servers.value):
#                                     tasks_done[k] = k - 1

#                                 # give the other processes sometimes to update
#                                 time.sleep(2)

#                                 # delete the cells that this processes currently occupied.
#                                 for l in reversed(range(process_id, len(tasks_done), num_of_processing_servers.value)):
#                                     if l >= 0:
#                                         del tasks_done[l]
#                                 num_of_processing_servers.value -= 1
#                                 lock_update.release() # release the lock
#                                 sys.exit()

#                             tasks_done[i] = True
#                             client_id += 1
#                 except IndexError:
#                     # when the tasks_done is updating, we allow Index out of bound error to occur during that time
#                     pass


def main():
    global input_server
    global host
    print("Input Server Address:", host, 6787)

    input_server_worker = socket.socket(socket.AF_INET,
                                        socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
    host = "146.186.64.174"

    # this address and port is for workers to connect
    input_server_worker.bind((host, 6787))
    input_server_worker.listen(5)

    num_of_processing_servers = Value('i', 0)  # keep track of the number of processing servers
    num_of_clients = Value('i', 0)  # keep track of the number of clients
    lock_update = Lock()  # ensure only one process can update tasks_done when a processing servers disconnect

    images = Manager().list(
        [None])  # this is the global storage for images received from clients. It is shared across all processes.

    tasks_done = Manager().list()  # used for synchronization of processes that handle processing servers' sockets.

    # start coordinator process.
    Process(target=coordinator, args=(images, tasks_done, num_of_processing_servers, num_of_clients)).start()

    # Accept new connection from processing server.
    process_id = 0
    while True:
        ps_socket, address = input_server_worker.accept()  # address is a tuple ("IP", port)
        print("A worker server " + str(address) + "connected")
        print("process id", num_of_processing_servers.value)

        tasks_done.append(False)
        print("task list length", len(tasks_done))
        num_of_processing_servers.value += 1
        
        
        Process(target=handle_one_processing_server, args=(
            images, tasks_done, ps_socket, process_id, num_of_processing_servers, lock_update)).start()
        
        process_id += 1


if __name__ == '__main__':
    main()
