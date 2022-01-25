import socket
import pickle
import cv2 as cv
import threading

"""
A client establishes 2 sockets connection to the server:
    (1) a socket for receiving message from server to be processed
    (2) a socket for sending the processed message to the server
"""

HEADERSIZE = 10

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET : IPv4 and SOCKET_STREAM : TCP
display_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def update_order(order):
    global server

    # order[0]: all of clients' ip in correct order
    # order[1]: index of current client in order[0]

    num_of_clients = len(order[0])
    current_index = order[1]
    print(order)
    print("Order of clients updated")


# socket tutorial: https://www.youtube.com/watch?v=Lbfe3-v7yE0
def main():

    # Connect to server
    global server
    global display_server
    server_address = str(input("Enter server's ip adress: "))
    while True:
        try:
            print("connecting to server")
            server.connect((server_address, 2999)) #receving image port
            display_server.connect((server_address, 3999)) #sending image port

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
                server.sendall("Done".encode())

                # check what type of message this is
                decoded_data = pickle.loads(full_msg[HEADERSIZE:])
                if isinstance(decoded_data, list):
                    # the message is an update message
                    update_order(decoded_data)
                else:
                    # the message is an image
                    #cv.imshow("hi", decoded_data)

                    processed_image = pickle.dumps(decoded_data)
                    display_server.sendall(f'{len(processed_image):<{HEADERSIZE}}'.encode() + processed_image)

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

    cv.destroyAllWindows()  # destroys the window showing image


if __name__ == '__main__':
    main()
