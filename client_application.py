import socket

# Define the server host and port
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345

# Create a TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_HOST, SERVER_PORT))

while True:
    # Get user input
    command = input("> ")

    # Send command to the server
    client_socket.send(command.encode())

    # Receive and print the server's response
    response = client_socket.recv(1024).decode()
    print(response)

    # If the command was QUIT, close the connection and break the loop
    if command.upper() == "QUIT":
        client_socket.close()
        break