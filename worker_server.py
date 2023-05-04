import socket
import sys
import time
import queue
import pickle
import cv2 as cv
from threading import Thread
import numpy as np
import cv2
from multiprocessing import Manager, Process
# For yolov5
s = time.time()
import yolov5.detect_ds as yolo
e = time.time()
print("yolo import time:", e-s)


if len(sys.argv) == 0:
    print("Please specify the model (\"example.pt\")")
    sys.exit()
    
model = sys.argv[1]

input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
output_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

input_server_ip = "146.186.64.174"
output_server_ip = "146.186.64.174"

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
            if msg == b'' and receive_msg_size > 0:
                print("Input server disconnected")
                # TODO: attempt to reconnect to input server
                input_server.close()
                input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                input_server.connect((input_server_ip, 6787))

                #break
            full_msg.extend(msg)
            if new_msg:
                print(msg)
                header += msg.decode()
                # make sure to receive full header before convert it to int (sometimes, only part of the header is received)
                if len(header) < HEADERSIZE:
                    #print("header not completely received")
                    print(receive_msg_size)
                    receive_msg_size = HEADERSIZE - len(header)
                else:
                    msglen = int(header)
                    #print(header)
                    receive_msg_size = 0 # (*) this solved negative message size error in receive buffer below.
                    new_msg = False

            else:
                # ensure receiving full message
                remaining_len = msglen + HEADERSIZE - len(full_msg) # (*) this can cause negative message size in receive buffer error since full_msg will always be updated after every loop.
                                                                    # We ensure full_message is not updated right after we are done with the header by setting the receive_message_size to 0
                                                                    # See (*) above
                #print(remaining_len)
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
                            print("skip")
                            pass
                        else:
                            # this is an update message
                            # TODO: handle update
                            pass
                    else:
                        # TODO: pass the images into YOLOv5 algorithm and get the annotated information
                        result = yolo.run(model, decoded_data, conf_thres = 0.50)
                        new_result = []
                        #[
                        #(
                        #[
                        #tensor(625., device='cuda:0'), tensor(127., device='cuda:0'), tensor(847., device='cuda:0'), tensor(471., device='cuda:0')
                        #], 'person 0.44', 0
                        #)
                        #] 
                        
                        for each_result in result:
                            new_box = []
                            box = each_result[0]
                            # print("each result", each_result)
                            for point in box:
                                new_box.append(point.tolist()) # convert cuda to cpu result so we can pickle it properly
                            a_result=(new_box, each_result[1], each_result[2])
                            # print("result after converted", a_result)
                            new_result.append(a_result)
                        print("old result", result)
                        print("new result", new_result)
                        # new_result = str(new_result)
                        # new_result = "HIHIHIHIHIHIHI"


                        # TODO: send to output server
                        message = pickle.dumps(new_result)
                        header = f'{len(message):<{HEADERSIZE}}'.encode()
                        print(len(header))
                        message = header + message
                        output_server.send(message)
                        print("sent to output server")
                        

                        # Put the image in a queue to be processed
                        #cv.imshow("hi", decoded_data)
                        # TODO: send the result to output server

                    new_msg = True
                    full_msg = bytearray()
                    header = ''

                    key = cv.waitKey(10) & 0xFF
                    if key == ord('q'):
                        break
        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from input_server")
            return

    cv.destroyAllWindows()  # destroys the window showing images

def main():
    yolo.initialize(model) # this make sure we only initilized the model once.
    print("finished initilized yolov5")
    # connect to input_server
    while True:
        try:
            print("connecting to input_server")
            input_server.connect((input_server_ip, 6787))  # receving images port


        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break
            
    # connect to output server
    while True:
        try:
            # output_server.connect((input_server_address, 3999))  # sending images port
            print("connecting to output_server")
            output_server.connect((output_server_ip, 6789))  # receving images port

        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to output_server")
            break
    Thread(target=receive_images).start()


    # TODO: Make a coordinator and processes for handling the models. This is YOLOv5
    # TODO: Make receive_images a different process instead of thread

if __name__ == '__main__':
    main()

