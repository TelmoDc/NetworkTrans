import socket
import cv2
import pickle
import struct
import threading
import time

# Client-side (Earth) configuration
HOST = '127.0.0.1'  # Address of the server (Rover on the Moon)
PORT = 12345         # Port to connect to
BUFFER_SIZE = 512    # Packet size for data transmission
LATENCY = 1.28       # Simulated Earth-Moon latency (1.28s)

def receive_video(conn):
    """Receives and displays the live video stream from the rover."""
    data = b""
    payload_size = struct.calcsize(">L")  # Defines the size of the message header

    while True:
        try:
            # Ensure we have enough data for the payload size
            while len(data) < payload_size:
                data += conn.recv(BUFFER_SIZE)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # Receive the full frame data
            while len(data) < msg_size:
                data += conn.recv(BUFFER_SIZE)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Deserialize and decode the image
            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("Live from the Moon", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break  # Exit if 'q' is pressed
        except:
            break

    cv2.destroyAllWindows()

def send_commands(conn):
    """Sends commands to the rover."""
    while True:
        command = input("Enter command (START_VIDEO, STOP_VIDEO, STOP): ")
        time.sleep(LATENCY)  # Simulate Earth-Moon delay
        conn.sendall(command.encode())  # Send command as bytes

        if command == "STOP":
            break

# Establish a TCP connection with the rover
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    threading.Thread(target=send_commands, args=(client,), daemon=True).start()
    receive_video(client)
