import socket
import threading
import json
import os
import base64

HOST = '127.0.0.1'
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

client_socket.connect((HOST, PORT))
print(f"Connected to {HOST}:{PORT}")

# Unique media folder for each client
MEDIA_DIR = f'CLIENT_MEDIA_{os.getpid()}'
os.makedirs(MEDIA_DIR, exist_ok=True)

def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            try:
                message = json.loads(data)
                message_type = message.get('type')

                if message_type == "connect_ack":
                    handle_connection_ack(message)
                elif message_type == "message":
                    handle_message(message)
                elif message_type == "notification":
                    handle_notification(message)
                elif message_type == "download":
                    handle_download(message)
                else:
                    print("Received an unknown message type from the server:", message_type)
            except json.JSONDecodeError:
                print("Invalid JSON received from server.")
        except ConnectionResetError:
            print("Server disconnected.")
            break

def handle_connection_ack(message):
    message_text = message['payload']['message']
    print(f"Server: {message_text}")

def handle_message(message):
    sender = message['payload']['sender']
    room = message['payload']['room']
    text = message['payload']['text']
    print(f"{room} - {sender}: {text}")

def handle_notification(message):
    notification_text = message['payload']['message']
    print(f"Notification: {notification_text}")

def handle_download(message):
    file_name = message['payload']['file_name']
    file_data_base64 = message['payload']['file_data']

    if file_data_base64:
        try:
            file_data = base64.b64decode(file_data_base64)
            with open(os.path.join(MEDIA_DIR, file_name), 'wb') as file:
                file.write(file_data)
                print(f"Downloaded file: {file_name}")
        except Exception as e:
            print(f"Download failed for {file_name}: {str(e)}")
    else:
        print(f"Download failed for {file_name}")


receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

name = input("Enter your name: ")
room = input("Enter the room name: ")

connect_message = {
    "type": "connect",
    "payload": {
        "name": name,
        "room": room
    }
}

client_socket.send(json.dumps(connect_message).encode('utf-8'))

def send_file(file_path):
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            file_data = file.read()
            file_data_base64 = base64.b64encode(file_data).decode('utf-8')  # Encode file data as base64
            message = {
                "type": "upload",
                "payload": {
                    "path": file_path
                }
            }
            client_socket.send(json.dumps(message).encode('utf-8'))
    else:
        print(f"File {file_path} doesn't exist.")

while True:
    message_text = input("Enter a message (or 'exit' to quit) or file path: ")

    if message_text.lower() == 'exit':
        break

    if message_text.startswith("upload: "):
        file_path = message_text.split("upload: ")[1]
        send_file(file_path)
    elif message_text.startswith("download: "):
        # Send the "download" command to the server
        download_command = {
            "type": "download",
            "payload": {
                "name": message_text.split("download: ")[1]
            }
        }
        client_socket.send(json.dumps(download_command).encode('utf-8'))
    else:
        message = {
            "type": "message",
            "payload": {
                "sender": name,
                "room": room,
                "text": message_text
            }
        }
        client_socket.send(json.dumps(message).encode('utf-8'))

client_socket.close()
