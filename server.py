import socket
import sqlite3
import threading

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345

# List to store online clients
online_clients = []

def handle_client(client_socket):
    # Connect to SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create table for users if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

    username = None
    while True:
        # Receive data
        data = client_socket.recv(1024).decode().strip()

        # Parse message and extract command
        message_parts = data.split(" ")
        command = message_parts[0].upper()

        # Define responses for different commands
        response = ""
        if command == "REGISTER":
            # Register new user
            if len(message_parts) < 3:
                response = "Usage: REGISTER <username> <password>"
            else:
                username, password = message_parts[1], message_parts[2]
                try:
                    cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                    conn.commit()
                    response = "Registration successful."
                except sqlite3.IntegrityError:
                    response = "Username already taken."
        elif command == "LOGIN":
            # Authenticate user
            if len(message_parts) < 3:
                response = "Usage: LOGIN <username> <password>"
            else:
                username, password = message_parts[1], message_parts[2]
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                if cursor.fetchone() is not None:
                    response = "Login successful."
                    username = message_parts[1]
                    online_clients.append(username)
                else:
                    response = "Invalid username or password."
        elif command == "WHO":
            # Send list of online clients
            response = ", ".join(online_clients)
        elif command == "HELLO":
            response = f"Hello, client from {client_address[0]}!"
        elif command == "QUIT":
            # Close connection
            response = "Goodbye!"
            client_socket.send(response.encode())
            client_socket.close()
            break
        else:
            # Unknown command
            response = f"Unknown command: '{command}'"
    
        # Send response
        client_socket.send((response + '\n').encode())
        
    # Close connection
    client_socket.close()

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen()

print(f"Server listening on: {SERVER_HOST}:{SERVER_PORT}")
while True:
    # Accept connection
    client_socket, client_address = server_socket.accept()

    # start a new thread to handle the client
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()

