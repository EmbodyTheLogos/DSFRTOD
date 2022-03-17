from Cryptodome.Cipher import AES
import random
import time
import cv2
import pickle
import sys
import lz4.frame
import socket
from collections import deque

HEADERSIZE = 10

# these variables are relating to socket
input_server_address = '' #[ip]:[port]
input_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET means IPv4, SOCKET_STREAM means TCP
output_server_address = '' #[ip]:[port]
output_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET means IPv4, SOCKET_STREAM means TCP

# these variables are relating to the input video
input_video = 0 # default is camera.
save_result = False # whether or not the client save the result after receive it from output_server.
save_result_path = ""
display_input = False # whether or not the client display the input video
video_frames_queue = deque([])  # this queue stores the video frames in order.
                                # the queue will popleft() when it receive a result from output server

# these variables is for fast_encryption method
use_fast_encryption = False # whether or not to use fast encryption method. This is useful if the frame you're sending is very large in size.
num_of_swap = 1000 # number of times swapping two random positions in the bytearray of the data.

# this is for generating a random key for authentication and encryption
available_chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '{', '}', '[', ']', '|', '\\', ';', ':', "'", '"', '<', '>', ',', '.', '?', '/', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

# this is the encryption key's length
key_length = 16 # key's length is a multiple of 16


'''
    This method takes in the bytearray of data and randomly pick two positions in it, then swap them. Repeat this process for at least 1000 times.
    The swapped sequence is saved to swapped_positions, and will be encrypted. Then the encrypted sequence is appended to the end of data
'''
def fast_encryption(data, key):
    swapped_positions = [] # a list of 2-tuples that keep track of the swapping sequence of the data modified by fast_encryption
    global num_of_swap
    num_of_swap = max(1000, num_of_swap) # swap at least 1000 times

    # shuffle the data by swapping 2 random positions, num_of_swap times
    for i in range(num_of_swap):
        a = random.randint(0, len(data) - 1)
        b = random.randint(0, len(data) - 1)
        temp = data[a]
        data[a] = data[b]
        data[b] = temp
        swapped_positions.append((a,b))

    # encrypt swapped_positions and add to the end of data
    swapped_positions = pickle.dumps(swapped_positions)
    encrypt = AES.new(key, AES.MODE_OCB, nonce=key[:15])
    encrypted_sequence, mac = encrypt.encrypt_and_digest(swapped_positions)
    data.extend(bytearray(encrypted_sequence))
    return data, mac

def fast_decryption(data, sequence, key):
    pass

def generate_key():
    # key length is a multiple of 16
    global available_chars
    global key_length
    key = ''
    for i in range(key_length):
        key += random.choice(available_chars)
    return key

def encrypt_data(data, key):
    if (use_fast_encryption is False):
        encrypt = AES.new(key, AES.MODE_OCB, nonce=key[:15])
        return encrypt.encrypt_and_digest(data)
    return fast_encryption(data, key)

def decrypt_data(data, key, mac):
    decrypt = AES.new(key, AES.MODE_OCB, nonce=key[:15])
    return decrypt.decrypt_and_verify(data, mac)

def annotate_image(result):
    pass

def authenticate():
    pass

def process_arguments():
    global input_video
    global display_input
    global save_result
    global save_result_path
    global use_fast_encryption
    global num_of_swap
    global key_length
    global input_server_address
    global output_server_address

    args = sys.argv
    for i in range(1, len(args)):
        if args[i] == "--source":
            input_video = args[i+1]
        elif args[i] == "--display_input":
            display_input = True
        elif args[i] == "--save":
            save_result = True
            save_result_path = args[i+1]
        elif args[i] == "--fast_encryption":
            num_of_swap = int(args[i+1]) # specify the number of swapping 2 random positions in fast_encryption algorithm
        elif args[i] == "--key_length":
            key_length = args[i+1]
        elif args[i] == "--input_server":
            input_server_address = args[i+1]
        elif args[i] == "--output_server":
            output_server_address = args[i+1]
        elif args[i] == "--help":
            print("Display help usage")

def connect():
    global input_server_address
    global input_server_socket
    global output_server_address
    global output_server_socket

    # separate input server's ip and port
    input_ip = input_server_address.split(":")[0]
    input_port = input_server_address.split(":")[1]

    # separate output server's ip and port
    output_ip = output_server_address.split(":")[0]
    output_port = output_server_address.split(":")[1]

    # connecting to input_server
    while True:
        try:
            print("connecting to input_server")
            input_server_socket.connect((input_ip, input_port))
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break

    # connecting to output_server
    # while True:
    #     try:
    #         print("connecting to input_server")
    #         output_server_socket.connect((output_ip, output_port))
    #     except ConnectionRefusedError:
    #         # Keep trying to connect to input_server
    #         pass
    #     else:
    #         print("connected to input_server")
    #         break

def program_structure():

    # Main thread:
        # Process arguments

        # Connect to input and output servers

    # Thread 1: Send frames to input_server
        # Read frame from input video, and put each frame in a global queue: video_frames_queue

        # Compress the frame

        # Encrypt the frame

        # Prepare a message with the encrypted frame and additional information to send to input server

        # Send the message to the input server

    # Thread 2: Process results from output server
        # Receive result from output server

        # Once received, popleft() the global queue video_frames_queue to get the frame.

        # Annotated the newly popped frame with the result.

        # Display the annotated frame if user did not use --no_display_result.

        # Save the result if the user has specified it
        pass

def main():

    while True:
        try:
            print("connecting to input_server")
            input_server_socket.connect(("127.0.0.1", 2999))  # receving image port
            # output_server.connect((input_server_address, 3999))  # sending image port
        except ConnectionRefusedError:
            # Keep trying to connect to input_server
            pass
        else:
            print("connected to input_server")
            break

    cap = cv2.VideoCapture(0)
    input_server_socket.settimeout(0.1) #if there is nothing to receive after 1 second, timeout exception occurs
    while True:
        ret, frame = cap.read()

        if ret:
            try:
                message = cv2.imencode('.jpg', frame)[1].tobytes()    # this thing convert cv2 image into binary byte (similar to file.read(),
                                                                    # which decrease about 10 times in size
                header = f'{len(message):<{HEADERSIZE}}'.encode()
                message = header + message
                input_server_socket.send(message)
            except socket.timeout:
                print("Skip frame")
        else:
            cap = cv2.VideoCapture("wow.mp4")
        # encrypt the video frame
        #key = generate_key().encode()
        #nonce = get_random_bytes(15)
        #s = time.time()
        #encrypted_data, mac = encrypt_data(frame, key)
        #e = time.time()
        #print("Encryption time:", e-s)



if __name__ == '__main__':
    main()