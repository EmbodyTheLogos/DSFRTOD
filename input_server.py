import cv2 as cv
import socket
import pickle
import imutils
import threading
import time

HEADERSIZE = 10
need_to_update = False
new_client_connected = False
processing_servers = []
video_input = cv.VideoCapture(0)

# socket tutorial: https://www.youtube.com/watch?v=Lbfe3-v7yE0
input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
host = socket.gethostbyname(socket.gethostname())
input_server.bind((host, 2999))
input_server.listen(5)

output_server = None #socket
output_server_address = None

def update_order():
    processing_server_ips = []
    for i in range(len(processing_servers)):
        processing_server_ips.append(processing_servers[i][1][0])  # we only need to send the address, not the port

    for i in range(len(processing_servers)):
        try:
            order = (processing_server_ips, i)
            order = pickle.dumps(order)
            print(len(order))
            processing_servers[i][0].sendall(f'{len(order):<{HEADERSIZE}}'.encode() + order)
        except (ConnectionResetError, ConnectionAbortedError):
            print("Order: A client got disconnected. It is the " + str(i) + " th client")
            del processing_servers[i]
            #del success_msg[i]
            break
    print("Update sent to all processing_servers")

def handle_all_processing_servers():
    global need_to_update
    global video_input
    global output_server
    while True:
        if len(processing_servers) > 0:
            ret, frame = video_input.read()
            frame = imutils.resize(frame, width=640)
            image = pickle.dumps(frame)  # encode image using pickle
            image = f'{len(image):<{HEADERSIZE}}'.encode() + image
            output_server.sendall(image) #send image to output server

            for i in range(len(processing_servers)):
                if need_to_update:
                    update_order()
                    need_to_update = False
                try:
                    start_time = time.time()
                    processing_servers[i][0].sendall(image)  # send information to the client.
                    end_time = time.time()
                    total_time = end_time - start_time
                    print("Sending time to processing server", i, )
                    if total_time > 1:
                        raise TimeoutError("A processing server take too long to response")
                    key = cv.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break

                # Handle the case when processing servers disconnect from input input_server.
                except TimeoutError:
                    print("__________Timeout error____________")
                    print("A processing server got disconnected due to timeout. It is ", processing_servers[i][1])

                    processing_servers[i][0].shutdown(2)
                    processing_servers[i][0].close()
                    del processing_servers[i]
                    update_order()
                    break
                except (ConnectionResetError, ConnectionAbortedError):
                    print("----------Connection Error-------------")
                    print("A processing server got disconnected. It is ", processing_servers[i][1])
                    del processing_servers[i]
                    update_order()
                    break

def accept_output_server():
    global output_server
    global output_server_address
    print("Waiting for output_server to connect")
    output_server, output_server_address = input_server.accept()  # address is a tuple ("IP", port)
    print("Output server connected")

def accept_new_connections():
    global need_to_update
    global output_server
    while True:
        processing_server_socket, address = input_server.accept()  # address is a tuple ("IP", port)
        processing_servers.append((processing_server_socket, address))
        print("A processing_server " + str(address) + "connected")
        #output_server.recv(72) # wait to see if the newly added processing server is connected to the output_server or not
        need_to_update = True

def main():
    print("Input Server Address:", host, 2999)
    accept_output_server()
    threading.Thread(target=handle_all_processing_servers).start()
    threading.Thread(target=accept_new_connections).start()

if __name__ == '__main__':
    main()
