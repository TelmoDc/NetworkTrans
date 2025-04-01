import socket
import cv2
import pickle
import struct
import threading
import time

# Server-side (Rover) configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 12345      # Port to listen for connections
BUFFER_SIZE = 512 # Packet size for data transmission
LATENCY = 1.28    # Simulated Earth-Moon latency (1.28s)
is_camera_active = False  # Flag to control video streaming

def send_video(conn):
    """Captures and sends video frames to the client with simulated latency."""
    global is_camera_active
    cap = cv2.VideoCapture(0)  # Open the default camera

    # Reduce video resolution to optimize transmission
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        time.sleep(LATENCY)  # Simulate latency even in case of failure
        conn.sendall(b"Camera not available")
        return

    is_camera_active = True
    try:
        while is_camera_active:
            ret, frame = cap.read()
            if not ret:
                break

            # Compress the frame to reduce size before transmission
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            data = pickle.dumps(buffer)

            time.sleep(LATENCY)  # Simulate Earth-Moon delay

            # Send frame size followed by the frame data
            conn.sendall(struct.pack(">L", len(data)))
            
            # Send the actual frame data in chunks
            # This is to ensure that we do not exceed the buffer size
            for i in range(0, len(data), BUFFER_SIZE):
                conn.sendall(data[i:i+BUFFER_SIZE])
    finally:
        cap.release()
        is_camera_active = False
        print("Video streaming stopped.")

def handle_client(conn, addr):
    """Handles incoming client connections and commands."""
    global is_camera_active
    print(f"Connected to {addr}")

    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE).decode()  # Receive and decode the command
                if not data:
                    break

                print(f"Command received: {data}")

                if data == "START_VIDEO" and not is_camera_active:
                    threading.Thread(target=send_video, args=(conn,), daemon=True).start()

                if data == "STOP_VIDEO":
                    is_camera_active = False

                if data == "STOP":
                    break

            except ConnectionResetError:
                break

# Start the TCP server to listen for connections
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen()
    print(f"Rover waiting for connection on {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
