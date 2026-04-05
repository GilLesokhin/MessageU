import socket
from Protocol import Request, Response
from Utilities import HexBytes

HOST = '127.0.0.1'
PORT = 1234
DATA_MAX_SIZE = 1024

def start_server():
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        
        # Bind the socket to the PORT
        server_socket.bind((HOST, PORT))
        # Listen for incoming connections
        server_socket.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        # Accept a connection
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        
        with client_socket:
            while True:
                # Receive data from the client
                data = client_socket.recv(DATA_MAX_SIZE)
                if not data:
                    # If no data is received, the client has disconnected
                    print(f"Client {client_address} disconnected")
                    break
                
                print(f"Received message:\n{HexBytes(data)}")
                deserialized_req = Request().deserialize(data)
                print(f"Received message deserialized:\n{deserialized_req}")

                # Prepare and send the response
                response = deserialized_req.serialize()
                client_socket.send(response)
                print(f"Sent response: {HexBytes(response)}\n\n\n")

if __name__ == "__main__":
    start_server()