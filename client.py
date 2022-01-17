import socket
import pickle
import cv2 as cv
import threading

HEADERSIZE = 10

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP

previous_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP
previous_client.bind((socket.gethostbyname(socket.gethostname()), 1999))
previous_client.listen(5)  # 5 clients can wait for the connection if the server is busy
previous_client_socket = ()
previous_client_connected = False

next_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP


def accept_connection():
    global previous_client
    global previous_client_socket
    global previous_client_connected
    while True:
        try:
            previous_client_socket = previous_client.accept()
        # this terminate the thread when closing the program by pressing 'q'
        except OSError:
            break
        else:
            print("Previous client connected!")
            print(previous_client_socket)
            previous_client_connected = True


def update_order(order):
    global server
    global next_client
    next_client.close()
    # reset next_client socket
    next_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # order[0]: all of clients' ip in correct order
    # order[1]: index of current client in order[0]

    num_of_clients = len(order[0])
    current_index = order[1]
    print(order)

    # Determine and connect to the next client
    if num_of_clients == 2:
        while True:
            if current_index == 0:
                try:
                    next_client.connect((order[0][1], 1999))
                except ConnectionRefusedError:
                    # Keep trying to connect to server
                    pass
                else:
                    print("connected to " + str((order[0][1])))
                    break

            else:
                try:
                    next_client.connect((order[0][0], 1999))
                except ConnectionRefusedError:
                    # Keep trying to connect to server
                    pass
                else:
                    print("connected to " + str((order[0][0])))
                    break


    if num_of_clients > 2:
        while True:
            try:
                next_client.connect((order[0][current_index - num_of_clients + 1], 1999))
            except ConnectionRefusedError:
                # Keep trying to connect to server
                pass
            else:
                break


    print("Order of clients updated")


# socket tutorial: https://www.youtube.com/watch?v=Lbfe3-v7yE0
def main():
    global previous_client_socket
    global previous_client_connected

    # Accept connection from previous client
    # Run one thread at a time for socket.accept()

    threading.Thread(target=accept_connection).start()


    # Connect to server
    global server
    server_address = str(input("Enter server's ip adress: "))
    server_port = int(input("Enter server's port number: "))
    while True:
        try:
            print("connecting to server")
            server.connect((server_address, server_port))
        except ConnectionRefusedError:
            # Keep trying to connect to server
            pass
        else:
            print("connected to server")
            break
    full_msg = b''
    new_msg = True


    while True:

        try:
            # Receive and process data from server
            msg = server.recv(32 * 1024)  # receive data. 32 * 1024 bytes at a time


            if new_msg:
                header = msg[:HEADERSIZE].decode()
                msglen = int(header)
                new_msg = False

            # receive incoming image
            full_msg += msg


            # Process fullly received message
            if len(full_msg) - HEADERSIZE == msglen:
                # inform server that the image has been received
                server.send("Done".encode())

                # check what type of message this is
                decoded_data = pickle.loads(full_msg[HEADERSIZE:])
                if isinstance(decoded_data, list):
                    # the message is an update message
                    update_order(decoded_data)
                else:
                    # the message is an image
                    cv.imshow("hi", decoded_data)

                    # ready to receive new mesaage from server
                new_msg = True
                full_msg = b''


                # Exiting program
                key = cv.waitKey(1) & 0xFF
                if key == ord('q'):
                    # this will raise an OSError, thus terminate any threads that still wait for previous_client.accept()
                    previous_client.close()
                    break
        except (ConnectionResetError, ConnectionAbortedError):
            print("Disconnected from server")
            # this will raise an OSError, thus terminate any threads that still wait for previous_client.accept()
            previous_client.close()
            break

        # Handle when previous client disconnect
        try:
            if previous_client_connected:
                previous_client_socket[0].send("Hi".encode())
        except (ConnectionResetError, ConnectionAbortedError):
            print("previous client disconnected")
            previous_client_socket = ()
            previous_client_connected = False
    cv.destroyAllWindows()  # destroys the window showing image


if __name__ == '__main__':
    main()
