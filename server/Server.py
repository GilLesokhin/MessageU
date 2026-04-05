import socket
import threading
from Protocol import Request, Response , RequestCode, ResponseCode
from DataBase import DataBase

DEFAULT_PORT = 1357
PORT_FILE = "myport.info"
HOST = '127.0.0.1'
DATA_MAX_SIZE = 1024

class Server:
    def __init__(self, host: str = HOST):
        self.host = host
        self.port = get_port()
        self.server_socket = None
        self.db = DataBase()

    def start(self):
        """Start the server and listen for incoming client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server started on {self.host}:{self.port}, waiting for clients...")

        # Accepting multiple clients
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address}")
            client_thread = threading.Thread(target=self._client_handler, args=(client_socket, client_address))
            client_thread.start()
    
    def _client_handler(self, client_socket, client_address):
        """Handle the client communication."""
        try:
            with client_socket:
                while True:
                    data = client_socket.recv(DATA_MAX_SIZE)
                    if not data:
                        print(f"Client {client_address} disconnected")
                        break
                    try:
                        handle_req = True
                        request = Request(data)
                    except Exception:
                        handle_req = False
                        response = Response(code = ResponseCode.ERROR_MESSAGE)
                    
                    if (handle_req):
                        try:
                            response = self._request_handler(request)
                            #print(self.db);
                        except Exception:
                            response = Response(code = ResponseCode.ERROR_MESSAGE)

                    client_socket.sendall(response.serialize())
                    
        except Exception:
            print(f"Client with the following details: {client_address} has disconnected")
        finally:
            print(f"Closing connection with {client_address}")
            client_socket.close()


    def _request_handler(self, req: Request):
        if req.validate() == False:
            return Response(code = ResponseCode.ERROR_MESSAGE)

        match req.get_code():
            case RequestCode.SIGN_USER:  # Sign a user
                resid = ResponseCode.USER_SIGNED
                try:
                    if self.db.user_exists(req.get_name()):
                        return Response(code = ResponseCode.ERROR_MESSAGE)
                    cid = self.db.add_user(req.get_name(), req.get_public_key())
                    return Response(code = resid, client_id = cid)
                except Exception:
                    return Response(code = ResponseCode.ERROR_MESSAGE)
                
            case RequestCode.LIST_USERS:  # Get users list
                fcid = req.get_client_id()
                resid = ResponseCode.USERS_LIST
                try:
                    u_list = self.db.get_users_list(fcid)
                    return Response(code = resid, client_name_list = u_list)
                except Exception:
                    return Response(code = ResponseCode.ERROR_MESSAGE)

            case RequestCode.GET_PUBLIC_KEY:  # Get public key
                tcid = req.get_other_client_id()
                resid = ResponseCode.RETRIEVED_PUBLIC_KEY
                try:
                    key = self.db.get_public_key(tcid)
                    return Response(code = resid, client_id = tcid, public_key= key)
                except Exception:
                    return Response(code = ResponseCode.ERROR_MESSAGE)
                    

            case RequestCode.SEND_MESSAGE:  # Send a message to another client
                fcid = req.get_client_id()
                tcid = req.get_other_client_id()
                mtype = req.get_message_type()
                cont = req.get_message_content()
                resid = ResponseCode.MESSAGE_SENT
                try:
                    mid = self.db.send_message(to_client_id = tcid, from_client_id = fcid, msg_type= mtype, content= cont)
                    return Response(code = resid, other_client_id = tcid, message_id = mid)
                except Exception:
                    return Response(code = ResponseCode.ERROR_MESSAGE)

            case RequestCode.GET_MESSAGES:
                fcid = req.get_client_id()
                resid = ResponseCode.RETRIEVED_MESSAGES
                try:
                    msg_list = self.db.get_messages(fcid)
                    return Response(code = resid, messages_list_payload= msg_list)
                except Exception:
                    return Response(code = ResponseCode.ERROR_MESSAGE)
            
            
    def stop(self):
        """Close the server socket."""
        if self.server_socket:
            self.server_socket.close()
            print("Server stopped.")

def get_port(filename = PORT_FILE):
    try:
        # Open the file and read the content
        with open(filename, 'r') as file:
            port_str = file.read().strip()  # Read and strip any surrounding whitespace

        # Try to convert the content to an integer
        port = int(port_str)
        
        # Check if the port is within a valid range (1-65535)
        if port < 1 or port > 65535:
            print("Warning: Port number is out of valid range (1-65535). Using default port: {DEFAULT_PORT}.")
            return DEFAULT_PORT
        
        return port
    except ValueError:
        # If the content is not a valid integer
        print("Warning: Invalid port file contents detected. Using default port: {DEFAULT_PORT}.")
        return DEFAULT_PORT
    
    except FileNotFoundError:
        # If the file doesn't exist
        print(f"Warning: File '{filename}' not found. Using default port: {DEFAULT_PORT}.")
        return DEFAULT_PORT

# To run the server
if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
        server.stop()
