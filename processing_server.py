import socket
import pickle
import cv2 as cv
import time
import threading
from collections import deque
from threading import Thread

"""
A client establishes 2 sockets connection to the input_server:
    (1) a socket for receiving message from input_server to be processed
    (2) a socket for sending the processed message to the input_server
"""

HEADERSIZE = 10

input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP
output_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
raw_images = deque([])


def update_order(order):
    global input_server

    # order[0]: all of processing_servers' ip in correct order
    # order[1]: index of current client in order[0]

    num_of_clients = len(order[0])
    current_index = order[1]
    print(order)
    print("Order of processing_servers updated")

def receive_message():
    global input_server
    global raw_images
    full_msg = b''
    new_msg = True
    receive_msg_size = HEADERSIZE
    while True:
        try:
            # Receive and process data from input_server
            msg = input_server.recv(receive_msg_size)
            if new_msg:
                header = msg.decode()
                msglen = int(header)
                new_msg = False

            full_msg += msg
            receive_msg_size = msglen
            print(len(msg))

            # ensure receiving full message
            if msglen + HEADERSIZE - len(full_msg) < receive_msg_size:
                receive_msg_size = msglen + HEADERSIZE - len(full_msg)

            # Process fullly received message
            if len(full_msg) - HEADERSIZE == msglen:
                time.sleep(1)
                receive_msg_size = HEADERSIZE
                # check what type of message this is
                decoded_data = pickle.loads(full_msg[HEADERSIZE:])
                if isinstance(decoded_data, tuple):
                    # the message is an update message
                    update_order(decoded_data)
                else:
                    # the message is an image
                    raw_images.append(decoded_data)
                new_msg = True
                full_msg = b''

        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            break


def process_images():
    global raw_images
    global output_server
    generic_result = [[(8, 2, 1, 3), "dog"], [(8, 23, 11, 33), "cat"], [(7, 52, 21, 13), "horse"]]
    while True:
        #print("I'm still processing")
        if len(raw_images) > 0:
            #time.sleep(0.03)
            raw_images.popleft()
            result = pickle.dumps(generic_result)
            output_server.sendall(f'{len(result):<{HEADERSIZE}}'.encode() + result)


# socket tutorial: https://www.youtube.com/watch?v=Lbfe3-v7yE0
def main():
    # Connect to input_server
    global input_server
    global output_server
    input_server_address = str(input("Enter input_server's ip address and port (ex: 192.168.1.100:2999): "))
    output_server_address = str(input("Enter output_server's ip address and port (ex: 192.168.1.100:2999): "))
    input_server_port = int(input_server_address.split(':')[1])
    input_server_address = input_server_address.split(':')[0]
    output_server_port = int(output_server_address.split(':')[1])
    output_server_address = output_server_address.split(':')[0]

    # connecting to input_server
    while True:
        try:
            print("connecting to input_server")
            input_server.connect((input_server_address, input_server_port))  # receving image port
            # output_server.connect((input_server_address, 3999))  # sending image port

        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break
    #connecting to output_server
    while True:
        try:
            print("connecting to output_server")
            output_server.connect((output_server_address, output_server_port))  # receving image port
            # output_server.connect((input_server_address, 3999))  # sending image port

        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to output_server")
            break

    Thread(target=receive_message).start()
    Thread(target=process_images).start()


if __name__ == '__main__':
    main()
