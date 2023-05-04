'''
    Program Structure:
    1. Received annotations results from processing servers.
    2. Process and merge those annotation and convert them to appropriate format
    3. Send the final result back to client.
'''

import socket
import pickle
from multiprocessing import Process, Manager, Value, Lock
import time
import copy
import sys
from threading import Thread

server_for_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
server_for_processing_servers = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port_for_client = 6790
port_for_processing_server = 6789

host = "146.186.64.174"

HEADERSIZE = 10

# this method handle one processing server.
# It receive the result from a processing server, then added to the result list
# The result list will then be processed by the coordinator method, and send it to the client.

def handle_one_process(ps_socket, process_id, tasks_done, results_list, num_of_processing_servers, client_connected):
    # tasks_done.extend([False])  # False means the task of the process is not done yet.

    global HEADERSIZE
    full_msg = bytearray()
    new_msg = True
    receive_msg_size = HEADERSIZE
    header = ''
    while True:
        if not bool(client_connected.value):
            full_msg = bytearray()
            new_msg = True
            receive_msg_size = HEADERSIZE
            header = ''
            msg = ps_socket.recv(1024) #clear old messages
            print("nani??")
            # print(client_connected.value)
        if not tasks_done[process_id]:  # only receive next message once everyone else finished with the current one.
            try:
                
                # if receive_msg_size < 0:
                #     # new_msg = True
                #     header = full_msg[receive_msg_size:]
                #     print(header)
                #     full_msg = bytearray()
                #     full_msg.extend(header)
                #     header=header.decode()
                #     receive_msg_size = HEADERSIZE + receive_msg_size
                #     msg = ps_socket.recv(receive_msg_size)
                #     full_msg.extend(msg)
                
                # print(receive_msg_size)
                
                msg = ps_socket.recv(receive_msg_size)
                
                # when the worker node crashed but no exception is raised
                if len(msg) == 0 and receive_msg_size != 0:
                    raise ConnectionResetError
                
                full_msg.extend(msg)
                if new_msg:
                    # make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                    header += msg.decode()
                    if len(header) < HEADERSIZE:
                        receive_msg_size = HEADERSIZE - len(header)
                        # print("Current message size:", receive_msg_size)
                    else:
                        msglen = int(header)
                        new_msg = False
                        receive_msg_size = 0 # (*) this solved negative message size error in receive buffer
                else:
                    # ensure receiving full message
                    
                    remaining_len = msglen + HEADERSIZE - len(full_msg)
                    
                    receive_msg_size = remaining_len
                    # Process fullly received message
                    if len(full_msg) - HEADERSIZE == msglen:
                        
                        result = full_msg[HEADERSIZE:]
                        print("result:", result)
                        # print("remaining len:", remaining_len)
                        result = pickle.loads(result)
                        
                        result = copy.deepcopy(result)
                        results_list.extend(result)
                        new_msg = True
                        full_msg = bytearray()
                        receive_msg_size = HEADERSIZE
                        header = ''
                        tasks_done[process_id] = True


            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                num_of_processing_servers.value -= 1
                tasks_done[process_id] = None
                # del tasks_done[process_id]
                print("A processing server disconnected")
                ps_socket.close()
                return

        
# check if all elements in the list are true, except those who have None as values.
def all_true(tasks_done):
    for task in tasks_done:
        if task is not None and task == False:
                return False
    return True
    
    

# help synchronize results received from all processing servers.
def coordinator(server_for_client, tasks_done, results_list, num_of_processing_servers, client_connected):
    # accept client
    print("Wait for client to connect")
    client_socket, addr = server_for_client.accept()
    print("client connected")
    client_connected.value = 1
    
    time.sleep(1) # make sure the client called recv() before sending data to the client.
                    # This ensure no data lost.
                    # if send() is called before recv(), then recv() will not read the full message that has been sent.

    client_socket.settimeout(3)
    # process the results
    
    while True:
        
        if all_true(tasks_done):
            reset = False # flag to see if the tasks_done is reset or not
            # process the result
            result = list(results_list) # the multiprocess list to a normal list
            result = pickle.dumps(result)
            header = f'{len(result):<{HEADERSIZE}}'.encode()
            message = header + result

            try:
                # send the result to the client
                client_socket.send(message)
            except ConnectionResetError or ConnectionRefusedError or ConnectionAbortedError or socket.timeout:
                print("client disconnected")
                client_connected.value = 0
                print("Accepting new client")
                #client_socket = accept_client()
                client_socket, addr = server_for_client.accept()
                print("a client connected")
                client_connected.value = 1
                
                time.sleep(1) # make sure the client called recv() before sending data to the client.
                                #This ensure no data lost.
                                # if send() is called before recv(), then recv() will not read the full message that has been sent.
                
                #reset tasks_done
                for i in range(len(tasks_done)):
                    if tasks_done[i] is not None:
                        tasks_done[i] = False
                reset = True

                

            # reset results_list. Cannot simply do Manager().list() since it will make results_list non-sharable between processes.
            while len(results_list) > 0:
                del results_list[0]

            # reset tasks_done
            if not reset:
                for i in range(len(tasks_done)):
                    if tasks_done[i] is not None:
                        tasks_done[i] = False
                reset = True





def main():
    # initialize socket for client to connect
    server_for_client.bind((host, port_for_client))
    server_for_client.listen(5)

    # initialize socket for processing servers to connect
    server_for_processing_servers.bind((host, port_for_processing_server))
    server_for_processing_servers.listen(5)


    # used for synchronization of processes that handle processing servers' sockets.
    tasks_done = Manager().list()

    # List of all results received from all processes.
    results_list = Manager().list()

    # keep track of the number of processing servers
    num_of_processing_servers = Value('i', 0)
    
    # whether or not the client connnected. This make sure we reset our message receiver.
    new_client_connected = Value('i', False)

    # Start coordinator process
    Process(target=coordinator, args=(server_for_client, tasks_done, results_list, num_of_processing_servers, new_client_connected)).start()

    # Accept connections from processing servers
    process_id = 0
    while True:
        ps_socket, address = server_for_processing_servers.accept()
        # process_id = num_of_processing_servers.value
        tasks_done.append(False)
        Process(target=handle_one_process, args=(ps_socket, process_id, tasks_done, results_list, num_of_processing_servers, new_client_connected)).start()
        num_of_processing_servers.value += 1
        process_id += 1
        print("a worker server connected")

if __name__ == '__main__':
    main()
