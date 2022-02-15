import socket
import pickle
import sys
import cv2 as cv
import numpy
from threading import Thread
import time
import gc  # garbage collector
from collections import deque

HEADERSIZE = 10

input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP
output_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
host = socket.gethostbyname(socket.gethostname())
output_server.bind((host, 3999))
output_server.listen(5)

processing_servers = []  # list of tuples. A tuple contain the socket for a processing input_server and its address i.e. (processing_server_socket, address).
received_success = []  # keep track of whether or not we received the result from a processing input_server or not

raw_images = deque([])  # contains 100 raw images received from input_server. Act like a buffer.
fully_annotated = []  # use to determine if an image is fully annotated or not. len(fully_annotated == len(processing_servers).


def accept_new_connection():
    global input_server
    while True:
        processing_server_socket, address = output_server.accept()
        processing_servers.append((processing_server_socket, address))
        fully_annotated.append(False)

        # confirm with input_server that the processing server successfully connected to the output_server
        # input_server.send("success".encode())
        received_success.append(False)

        #Thread(target=receive_result, args=(
        #len(processing_servers) - 1,)).start()  # start a thread new thread to handle to new processing server
        print("A processing server " + str(address) + "connected")


def receive_raw_image():

    global input_server
    global raw_images
    global HEADERSIZE
    full_msg = b''
    new_msg = True
    receive_msg_size = HEADERSIZE
    header = ''
    while True:
        #time.sleep(0.1)
        try:
            msg = input_server.recv(receive_msg_size)
            full_msg += msg
            if new_msg:
                #make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                header += msg.decode()
                print(header)
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
                    receive_msg_size = HEADERSIZE
                    # check what type of message this is
                    decoded_data = pickle.loads(full_msg[HEADERSIZE:])
                    #raw_images.append(decoded_data)
                    #if isinstance(decoded_data, numpy.ndarray):
                       #cv.imshow("original image", decoded_data)
                    #image = raw_images.popleft()
                    cv.imshow("original images", decoded_data)

                    new_msg = True
                    full_msg = b''
                    header = ''

                    key = cv.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            break
    cv.destroyAllWindows()  # destroys the window showing image


def receive_result(ps_id):
    global processing_servers
    global raw_images
    full_msg = b''
    new_msg = True
    receive_msg_size = HEADERSIZE
    while True:
        if len(raw_images) > 0:
            try:
                # Receive and process data from input_server
                msg = processing_servers[ps_id][0].recv(receive_msg_size)
                if new_msg:
                    header = msg.decode()
                    print(header)
                    msglen = int(header)
                    new_msg = False
                full_msg += msg
                receive_msg_size = msglen
                print(len(full_msg))

                # ensure receiving full message
                if msglen + HEADERSIZE - len(full_msg) < receive_msg_size:
                    receive_msg_size = msglen + HEADERSIZE - len(full_msg)

                # Process fully received message
                if len(full_msg) - HEADERSIZE == msglen:
                    receive_msg_size = HEADERSIZE
                    decoded_data = pickle.loads(full_msg[HEADERSIZE:])
                    # image = raw_images.popleft()
                    # cv.imshow("After processed", image)

                    new_msg = True
                    full_msg = b''

                    key = cv.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break

            # Handle the case when processing servers disconnect from output_server.
            except (ConnectionResetError, ConnectionAbortedError):
                print("----------Connection Error-------------")
                print("A processing server got disconnected. It is ", processing_servers[ps_id][1])
                del processing_servers[ps_id]
                update_order()
                break
    cv.destroyAllWindows()  # destroys the window showing image


def main():
    input_server_address = str(input("Enter input input_server's ip adress: "))
    while True:
        try:
            print("connecting to input_server")
            input_server.connect((input_server_address, 2999))  # receving image port
            # output_server.connect((input_server_address, 3999))  # sending image port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break

    print("Output Server Address:", host, 3999)
    Thread(target=receive_raw_image).start()
    Thread(target=accept_new_connection).start()


if __name__ == '__main__':
    main()

#
#  Freaking error receiving raw images
# 921775
# 921775
# 921775
# 19
# 19
# Exception in thread Thread-1:
# Traceback (most recent call last):
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 932, in _bootstrap_inner
#     self.run()
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 870, in run
#     self._target(*self._args, **self._kwargs)
#   File "C:/Users/lnguy/Documents/Graduate Study/Spring 2022/DSFRTOD/output_server.py", line 76, in receive_raw_image
#     decoded_data = pickle.loads(full_msg[HEADERSIZE:])
# _pickle.UnpicklingError: pickle data was truncated
# [[[116 106  80]
#   [116 106  80]
#   [112 106  91]
#   ...
#   [144 163 181]
#   [136 164 181]
#   [136 164 181]]
#
#  [[114 104  89]
#   [114 104  89]
#   [112 104  89]
#   ...
#   [138 161 177]
#   [135 160 181]
#   [135 160 181]]
#
#  [[109 103  88]
#   [109 103  88]
#   [113 103  88]
#   ...
#   [137 159 175]
#   [131 159 175]
#   [129 157 173]]
#
#  ...
#
#  [[ 41  35  31]
#   [ 46  40  36]
#   [ 42  34  30]
#   ...
#   [ 82  74  70]
#   [ 82  75  66]
#   [ 82  75  66]]
#
#  [[ 49  37  38]
#   [ 51  40  41]
#   [ 49  40  41]
#   ...
#   [ 78  74  70]
#   [ 80  74  68]
#   [ 80  74  68]]
#
#  [[ 48  40  36]
#   [ 47  39  35]
#   [ 44  38  34]
#   ...
#   [ 86  78  74]
#   [ 88  79  76]
#   [ 88  79  76]]]


# Print with header
# 921765
# 921775
# 921775
# 921765
# 921775
# 921775
# 92176
# Exception in thread Thread-1:
# Traceback (most recent call last):
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 932, in _bootstrap_inner
#     self.run()
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 870, in run
#     self._target(*self._args, **self._kwargs)
#   File "C:/Users/lnguy/Documents/Graduate Study/Spring 2022/DSFRTOD/output_server.py", line 77, in receive_raw_image
#     decoded_data = pickle.loads(full_msg[HEADERSIZE:])
# _pickle.UnpicklingError: pickle data was truncated
# 92186
# 92186


# attempting to fix the above error
# 10
# 921765
# 921775
# 921775
# 10
# 921
# Exception in thread Thread-1:
# Traceback (most recent call last):
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 932, in _bootstrap_inner
#     self.run()
#   File "C:\Users\lnguy\AppData\Local\Programs\Python\Python38\lib\threading.py", line 870, in run
#     self._target(*self._args, **self._kwargs)
#   File "C:/Users/lnguy/Documents/Graduate Study/Spring 2022/DSFRTOD/output_server.py", line 58, in receive_raw_image
#     header += msg.decode()
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 7: invalid start byte