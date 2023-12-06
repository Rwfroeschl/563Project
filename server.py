"""
This code was written by Robert Froeschl and Michael Mudd. 

The project is a simple chat server that allows users to register, log in, and send messages to each other. 

"""
import socket
import sqlite3
import threading

# The IP address that the server will listen on. 
# "0.0.0.0" means it will accept connections from any network interface on the machine.
SERVER_HOST = "0.0.0.0"

# The port that the server will listen on.
SERVER_PORT = 12345

# A list that will store the usernames of clients that are currently connected to the server.
online_clients = []
# A dictionary that will map usernames to their corresponding client sockets.
client_sockets = {}

# This function will be run in a new thread for each client that connects to the server.
def handle_client(client_socket):
    # Establish a new SQLite database connection for this thread.
    # Each thread must have its own connection because SQLite doesn't allow connections to be shared between threads.
    conn = sqlite3.connect('users.db')
    
    # Create a new cursor for executing SQL commands.
    cursor = conn.cursor()

    # Execute a SQL command that creates a new table for storing user data, if it doesn't already exist.
    # The table has two columns: "username" and "password".
    # The "username" column is the primary key, so it must contain unique values.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    
    # initialize username to None. This will be set to the username of the client if they successfully log in.
    username = None
    # start a loop that will run until the client disconnects
    while True:
        # Receive data from the client, decode it from bytes to a string, and remove any whitespace.
        data = client_socket.recv(1024).decode().strip()

        # Split the received data into parts using space as the separator.
        # The first part is assumed to be the command, and the rest are the arguments to the command.
        message_parts = data.split(" ")
        command = message_parts[0].upper()

        # Initialize the response message as an empty string.
        response = ""

        # Handle the command.
        if command == "REGISTER":
            # The REGISTER command is for registering a new user.
            # It should be followed by a username and a password.
            if len(message_parts) < 3:
                response = "Usage: REGISTER <username> <password>"
            else:
                username, password = message_parts[1], message_parts[2]
                try:
                    # Try to insert the new user into the users table.
                    cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                    conn.commit()
                    response = "Registration successful."
                except sqlite3.IntegrityError:
                    # If insertion fails due to an IntegrityError, it means the username is already taken.
                    response = "Username already taken."
        elif command == "LOGIN":
            # The LOGIN command is for logging in a user.
            # It should be followed by a username and a password.
            if len(message_parts) < 3:
                # If a row is returned, it means the username and password are correct.
                response = "Usage: LOGIN <username> <password>"
            else:
                # If a row is returned, it means the username and password are correct.
                username, password = message_parts[1], message_parts[2]
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                if cursor.fetchone() is not None:
                    response = "Login successful."
                    username = message_parts[1]
                    online_clients.append(username)
                    # Add the client's socket to the dictionary, mapping from the username.
                    # This will be used later to send messages to the client.
                    client_sockets[username] = client_socket 
                else:
                    # If no row is returned, it means the username and password are incorrect.
                    response = "Invalid username or password."
        elif command == "MESSAGE":
            # The MESSAGE command is for sending a message to another user.
            # It should be followed by a username and the message.
            if len(message_parts) < 3:
                response = "Usage: MESSAGE <username> <message>"
            else:
                # Extract the target username and the message from the command.
                target_username, message = message_parts[1], " ".join(message_parts[2:])
                # Check if the target user is online (i.e., in the client_sockets dictionary).
                if target_username in client_sockets:
                    # If the user is online, send them the message and inform the sender that the message has been sent.
                    client_sockets[target_username].send(f"{username}: {message}".encode())
                    response = "Message sent."
                else:
                    # If the user is not online, inform the sender.
                    response = "The specified user is not online."
        elif command == "WHO":
             # The WHO command is for retrieving a list of online clients.
            response = ", ".join(online_clients)
        elif command == "QUIT":
            # The QUIT command is for disconnecting the client.
            response = "Goodbye!"
            client_socket.send(response.encode())
            client_socket.close()
            # Check if the username is in the list of online clients
            if username in online_clients:  
                # If the user is online, remove them from the list of online clients
                online_clients.remove(username)
                # Also remove their socket from the dictionary of client sockets
                del client_sockets[username]
            break
        else:
            # If the command is not recognized, inform the client.
            response = f"Unknown command: '{command}'"
    
        # Send response
        client_socket.send((response + '\n').encode())
        
    # Close the client socket connection. This is done when the client sends a "QUIT" command or disconnects.
    client_socket.close()

# Create a new TCP/IP socket. This will be used to listen for incoming client connections.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to a specific network interface and port number.
# SERVER_HOST and SERVER_PORT are defined earlier in the code.
server_socket.bind((SERVER_HOST, SERVER_PORT))
# Put the socket into server mode. It can now accept incoming connections.
server_socket.listen()

print(f"Server listening on: {SERVER_HOST}:{SERVER_PORT}")
# Start an infinite loop to continuously accept new client connections.
while True:
    # Wait for a client to connect. This is a blocking call.
    # When a client connects, it returns a new socket object representing the connection, and the address of the client.
    client_socket, client_address = server_socket.accept()

    # Start a new thread to handle the client connection.
    # The target of the thread is the handle_client function, and we pass the client socket as an argument.
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()

