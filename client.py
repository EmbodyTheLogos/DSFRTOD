from Cryptodome.Cipher import AES
import random
import time
import cv2
import pickle
import sys
import lz4.frame
import json
import socket
from threading import Thread
from collections import deque
import argparse
import os
import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = str(FILE.parents[0]) + "\yolov5"  # YOLOv5 root directory
ROOT = Path(ROOT)
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

import yolov5.utils.plots as plots


HEADERSIZE = 10

# these variables are relating to socket
input_server_address = sys.argv[2]
input_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET means IPv4, SOCKET_STREAM means TCP
output_server_address = sys.argv[3]
output_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET means IPv4, SOCKET_STREAM means TCP

# these variables are relating to the input video
input_video = 0  # default is camera.
save_result = False  # whether or not the client save the result after receive it from output_server.
save_result_path = ""
display_input = False  # whether or not the client display the input video
video_frames_queue = deque([])  # this queue stores the video frames in order.
# the queue will popleft() when it receive a result from output server


video_source = sys.argv[1]
cap = cv2.VideoCapture(video_source)
def send_to_input_server():
    global cap
    global input_server_address
    while True:
        try:
            print("connecting to input_server")
            input_server_socket.connect((input_server_address, 6788))  # receving images port
            # output_server.connect((input_server_address, 3999))  # sending images port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break

    input_server_socket.settimeout(2)  # if there is nothing to receive after 2 second, timeout exception occurs
    down_width = 640
    down_height = 640
    down_points = (down_width, down_height)
    while True:
        ret, frame = cap.read()
        if ret:
            try:
                resized_down = cv2.resize(frame, down_points, interpolation=cv2.INTER_LINEAR)

                message = cv2.imencode('.jpg', resized_down)[
                    1].tobytes()  # this thing convert cv2 images into binary byte (similar to file.read(),
                # which decrease about 10 times in size

                header = f'{len(message):<{HEADERSIZE}}'.encode()
                message = header + message
                input_server_socket.send(message)
                video_frames_queue.append(resized_down)  # add frame to queue
                # cv2.imshow("Hi", frame)
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q'):
                    break
            except socket.timeout:
                print("Skip frame")

        else:
            cap = cv2.VideoCapture(video_source)


def receive_from_output_server():
    global HEADERSIZE
    global output_server_address
    while True:
        try:
            print("connecting to input_server")
            output_server_socket.connect((output_server_address, 6790))  # receving images port
            # output_server.connect((input_server_address, 3999))  # sending images port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to output_server")
            break

    full_msg = bytearray()
    new_msg = True
    receive_msg_size = HEADERSIZE
    header = ''
    while True:
        try:
            if receive_msg_size < 0:
                # new_msg = True
                header = full_msg[receive_msg_size:]
                print(header)
                full_msg = bytearray()
                full_msg.extend(header)
                header = header.decode()
                receive_msg_size = HEADERSIZE + receive_msg_size
                msg = output_server_socket.recv(receive_msg_size)
                full_msg.extend(msg)

            msg = output_server_socket.recv(receive_msg_size)
            full_msg.extend(msg)
            if new_msg:
                # make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                print(msg)
                header += msg.decode()
                if len(header) < HEADERSIZE:
                    receive_msg_size = HEADERSIZE - len(header)

                else:
                    msglen = int(header)
                    receive_msg_size = 0
                    new_msg = False
            else:
                # ensure receiving full message
                remaining_len = msglen + HEADERSIZE - len(full_msg)

                receive_msg_size = remaining_len
                print("Current message size:", receive_msg_size)
                # Process fullly received message
                if len(full_msg) - HEADERSIZE == msglen:
                    # convert the image to appropriate format
                    results = pickle.loads(full_msg[HEADERSIZE:])
                    # annotate the image
                    annotate_image(results)
                    #print(results)
                    new_msg = True
                    full_msg = bytearray()
                    receive_msg_size = HEADERSIZE
                    header = ''

        except (ConnectionResetError, ConnectionAbortedError):
            print("Output server disconnected")
            return


def annotate_image(results):
    # results is a list that contains tuples. Each tuples contain information about a detected object.
    image = video_frames_queue.popleft()
    annotator = plots.Annotator(image, line_width=3)

    print(type(results))
    print(results)
    # for every detection in the result
    for object in results:
        xyxy = object[0] #bounding box
        label = object[1] # what the object is
        color = object[2] # color of the bounding box
        annotator.box_label(xyxy, label, color=plots.colors(color, True))
    im0 = annotator.result()

    cv2.imshow("hi", im0)
    cv2.waitKey(1)  # 1 millisecond

def main():
    # take care of input server
    Thread(target=send_to_input_server).start()


    # take care of output server
    Thread(target=receive_from_output_server).start()


'''
    Message format: f'{len(header):<{HEADERSIZE}}'.encode() + header + message
    header = (len(message), ("client_ip","client_port), frame_id)
    message = image
'''

if __name__ == '__main__':
    main()
