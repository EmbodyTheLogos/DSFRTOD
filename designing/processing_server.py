import socket
import time
import queue
import pickle
import cv2 as cv
from threading import Thread

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

                    #decoded_data = lz4.frame.decompress(full_msg[HEADERSIZE:])
                    #decoded_data = lz4.frame.decompress(decoded_data)
                    decoded_data = pickle.loads(full_msg[HEADERSIZE:])


                    cv.imshow("original images", decoded_data)

                    new_msg = True
                    full_msg = bytearray()
                    header = ''

                    key = cv.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            break
    cv.destroyAllWindows()  # destroys the window showing images


def main():
    while True:
        try:
            print("connecting to input_server")
            input_server.connect(("192.168.1.126", 6786))  # receving images port
            # output_server.connect((input_server_address, 3999))  # sending images port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break
    Thread(target=receive_images).start()

if __name__ == '__main__':
    main()

