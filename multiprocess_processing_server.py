import socket
import time
import queue
import pickle
import cv2 as cv
from threading import Thread
import numpy as np

input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
HEADERSIZE = 10

def receive_images():
    global input_server
    global HEADERSIZE
    full_msg = bytearray()
    new_msg = True
    receive_msg_size = HEADERSIZE
    header = ''
    while True:
        try:
            msg = input_server.recv(receive_msg_size)
            full_msg.extend(msg)
            if new_msg:
                header += msg.decode()

                # make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                if len(header) < HEADERSIZE:
                    print("header not completely received")
                    receive_msg_size = HEADERSIZE - len(header)
                else:
                    msglen = int(header)
                    print(header)
                    receive_msg_size = 0 # (*) this solved negative message size error in receive buffer below.
                    new_msg = False

            else:
                # ensure receiving full message
                remaining_len = msglen + HEADERSIZE - len(full_msg) # (*) this can cause negative message size in receive buffer error since full_msg will always be updated after every loop.
                                                                    # We ensure full_message is not updated right after we are done with the header by setting the receive_message_size to 0
                                                                    # See (*) above
                print(remaining_len)
                receive_msg_size = remaining_len
                # Process fullly received message
                if len(full_msg) - HEADERSIZE == msglen:
                    receive_msg_size = HEADERSIZE
                    decoded_data = cv.imdecode(np.frombuffer(full_msg[HEADERSIZE:], np.uint8), 1)

                    # check what type of message this is
                    if type(decoded_data)is not np.ndarray:
                        decoded_data = full_msg[HEADERSIZE:].decode()
                        if decoded_data == "skip":
                            # TODO: send empty annotation to output server
                            pass
                        else:
                            # this is an update message
                            # TODO: handle update
                            pass
                    else:
                        # TODO: pass the image into YOLOv5 algorithm and get the annotated information
                        cv.imshow("hi", decoded_data)
                        # TODO: send the result to output server

                    new_msg = True
                    full_msg = bytearray()
                    header = ''

                    key = cv.waitKey(10) & 0xFF
                    if key == ord('q'):
                        break
        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            break
    cv.destroyAllWindows()  # destroys the window showing image


def main():
    while True:
        try:
            print("connecting to input_server")
            input_server.connect(("127.0.0.1", 1999))  # receving image port
            # output_server.connect((input_server_address, 3999))  # sending image port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break
    Thread(target=receive_images).start()

if __name__ == '__main__':
    main()

