import socket
import threading
import json
import os
import base64

HOST = '127.0.0.1'
PORT = 12345
MEDIA_DIR = 'SERVER_MEDIA'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST, PORT))

server_socket.listen()
print(f"Server is listening on {HOST}:{PORT}")

connected_clients = {}

def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address}")

    while True:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            break

        try:
            message = json.loads(data)
            message_type = message.get('type')

            if message_type == "connect":
                handle_connection(client_socket, message)
            elif message_type == "message":
                handle_message(client_socket, message)
            elif message_type == "upload":
                handle_upload(client_socket, message)
            elif message_type == "download":
                handle_download(client_socket, message)  # Handle the "download" command here
        except json.JSONDecodeError:
            print("Invalid JSON received from client.")

    if client_socket in connected_clients:
        del connected_clients[client_socket]

    client_socket.close()

def handle_connection(client_socket, message):
    client_name = message['payload']['name']
    room_name = message['payload']['room']

    connected_clients[client_socket] = {
        'name': client_name,
        'room': room_name
    }

    response = {
        "type": "connect_ack",
        "payload": {
            "message": "Connected to the room."
        }
    }
    client_socket.send(json.dumps(response).encode('utf-8'))

def handle_message(client_socket, message):
    sender = connected_clients[client_socket]['name']
    room_name = connected_clients[client_socket]['room']
    text = message['payload']['text']

    for client, info in connected_clients.items():
        if info['room'] == room_name:
            response = {
                "type": "message",
                "payload": {
                    "sender": sender,
                    "room": room_name,
                    "text": text
                }
            }
            client.send(json.dumps(response).encode('utf-8'))

    print(f"Broadcasted message from {sender} in room {room_name}: {text}")

def handle_upload(client_socket, message):
    file_path = message.get('payload', {}).get('path', '')
    sender = connected_clients[client_socket]['name']

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            file_data = file.read()
            file_name = os.path.basename(file_path)
            with open(os.path.join(MEDIA_DIR, file_name), 'wb') as server_file:
                server_file.write(file_data)

            response = {
                "type": "notification",
                "payload": {
                    "message": f"User {sender} uploaded the {file_name} file."
                }
            }
            broadcast_message(response)
    else:
        response = {
            "type": "notification",
            "payload": {
                "message": f"File {file_path} doesn't exist."
            }
        }
        client_socket.send(json.dumps(response).encode('utf-8'))

def handle_download(client_socket, message):
    file_name = message.get('payload', {}).get('name', '')
    client_name = connected_clients[client_socket]['name']

    if file_name:
        file_path = os.path.join(MEDIA_DIR, file_name)
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_data_base64 = base64.b64encode(file_data).decode('utf-8')  # Encode file data as base64
                response = {
                    "type": "download",
                    "payload": {
                        "file_name": file_name,
                        "file_data": file_data_base64
                    }
                }
                client_socket.send(json.dumps(response).encode('utf-8'))
        except FileNotFoundError:
            response = {
                "type": "notification",
                "payload": {
                    "message": f"The {file_name} doesn't exist."
                }
            }
            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            response = {
                "type": "notification",
                "payload": {
                    "message": f"Error while downloading {file_name}: {str(e)}"
                }
            }
            client_socket.send(json.dumps(response).encode('utf-8'))


def broadcast_message(message):
    for client, info in connected_clients.items():
        client.send(json.dumps(message).encode('utf-8'))

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

while True:
    client_socket, client_address = server_socket.accept()

    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()