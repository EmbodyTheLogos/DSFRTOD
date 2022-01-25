
import cv2 as cv
import socket
import pickle
import imutils
import threading


"""
Server has three 3 Threads: (1) Accept connection
                            (2) Send information to clients
                            (3) Received processed information from clients
                            Thread (1) and (2) handle update (when there is a new connection or a client disconnect)
"""


#TODO: two problems. One is the interleaving messages and the other is client pause to wait for previous client to connect. Also not update to all clients

HEADERSIZE = 10
need_to_update = False
new_client_connected = False
clients = []
clients_display = []
num_of_clients = 1 #int(input("Enter the number of machines: "))

# socket tutorial: https://www.youtube.com/watch?v=Lbfe3-v7yE0
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # "AF_INET : IPv4" and "SOCKET_STREAM : TCP"
host = socket.gethostbyname(socket.gethostname())
s.bind((host, 2999))
print("Server's Address:", host, 2999)
s.listen(5)

# Display socket: purpose is to receive processed images from clients
display_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
display_socket.bind((host, 3999))
display_socket.listen(5)

success_msg = [] # need this to avoid receiving interleaving of packages from different images. Took me a long time to know what is wrong with my code...


# This is for displaying thread
def display_processed_images():
    while True:
        for i in range(len(clients_display)):
            try:
                msglen = 0
                full_msg = b''
                new_msg = True
                receive_msg_size = 32 * 1024
                while True:
                    # Receive and process data from server

                    msg = clients_display[i][0].recv(receive_msg_size)  # receive data. 32 * 1024 bytes at a time
                    if new_msg:
                        if receive_msg_size == 0:
                            break
                        header = msg[:HEADERSIZE].decode()
                        msglen = int(header)

                        new_msg = False

                    # receive incoming image
                    full_msg += msg
                    #ensure receiving full message
                    if msglen - len(full_msg) + HEADERSIZE < receive_msg_size:
                        receive_msg_size = msglen - len(full_msg) + HEADERSIZE

                    # Process fullly received message
                    if len(full_msg) - HEADERSIZE == msglen:

                        # check what type of message this is
                        processed_image = pickle.loads(full_msg[HEADERSIZE:])
                        cv.imshow("DSFRTOD", processed_image)

                        # ready to receive new image from other client
                        new_msg = True
                        full_msg = b''

                        # Exiting program
                        key = cv.waitKey(1) & 0xFF
                        if key == ord('q'):
                            break
            except OSError:
                break


def update_order():
    global success_msg
    clients_ip = []
    for i in range(len(clients)):
        clients_ip.append(clients[i][1][0]) #we only need to send the address, not the port
        #reset success_msg[]
        success_msg[i] = "Done"

    for i in range(len(clients)):
        try:
            order = []
            order.append(clients_ip)
            order.append(i)

            order = pickle.dumps(order)

            # success_msg[] prevent interleaving in packages

            if success_msg[i] == "Done":
                clients[i][0].sendall(f'{len(order):<{HEADERSIZE}}'.encode() + order)  # send information to the client.
                success_msg[i] = ''

            success_msg[i] = clients[i][0].recv(16)
            success_msg[i] = success_msg[i].decode("utf-8")
        # Handle the case when client disconnect from server.
        except (ConnectionResetError, ConnectionAbortedError):
            print("Order: A client got disconnected. It is the " + str(i) + " th client")
            del clients[i]
            del clients_display[i]
            del success_msg[i]
            break
    print("Update sent to all clients")


# This is for sending thread
def handle_all_clients():
    global success_msg
    global need_to_update
    cap = cv.VideoCapture(0)
    while True:
        for i in range(len(clients)):
            if need_to_update:
                update_order()
                need_to_update = False
            try:
                if success_msg[i] == "Done":
                    ret, frame = cap.read()
                    frame = imutils.resize(frame, width=320)
                    image = pickle.dumps(frame)  # encode image using pickle
                    image = f'{len(image):<{HEADERSIZE}}'.encode() + image
                    clients[i][0].sendall(image)  # send information to the client.
                    success_msg[i] = ''
                success_msg[i] = clients[i][0].recv(4)
                success_msg[i] = success_msg[i].decode("utf-8")

            # Handle the case when client disconnect from server.
            except (ConnectionResetError, ConnectionAbortedError):
                print("A client got disconnected. It is the " + str(i) + " th client")
                del clients[i]
                del clients_display[i]
                del success_msg[i]
                update_order()
                break

def accept_new_connections():
    global success_msg
    global need_to_update

    while True:
        clientsocket, address = s.accept()  # address is a tuple ("IP", port)
        client_display_socket, client_display_address = display_socket.accept()
        success_msg.append("Done")

        clients_display.append((client_display_socket, client_display_address))
        clients.append((clientsocket, address))
        print("A client "+ str(address) + "connected"  )
        need_to_update = True


def accept_connection():
    global success_msg
    global need_to_update
    clientsocket, address = s.accept() #address is a tuple ("IP", port)
    client_display_socket, client_display_address = display_socket.accept()  # address is a tuple ("IP", port)
    success_msg.append("Done")
    clients.append((clientsocket, address))
    clients_display.append((client_display_socket, client_display_address))
    print("A client connected")
    need_to_update = True

def main():
    # wait for all clients to connect
    for i in range(num_of_clients):
        accept_connection()

    print(f"Start Streaming")  # f"" is a literal string cause I'm a python noob

    threading.Thread(target=handle_all_clients).start()
    threading.Thread(target=accept_new_connections).start()
    threading.Thread(target=display_processed_images).start()



if __name__ == '__main__':
    main()


