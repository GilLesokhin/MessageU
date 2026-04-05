import socket
import threading
import logging
import queue
import time
from typing import Dict, Optional, List, Callable, Any, Tuple

HOST = '127.0.0.1'
DEFAULT_PORT = 1357


class Server:
    """
    A base server class that can handle multiple clients simultaneously.
    Uses threading to work around Python's GIL limitations.
    """
    
    def __init__(self, host: str = HOST, port: int = DEFAULT_PORT):
        """
        Initialize the server with host and port.
        
        Args:
            host: Host IP to bind the server to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.clients: Dict[str, socket.socket] = {}
        self.client_lock = threading.Lock()
        self.message_queue = queue.Queue()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start the server and begin accepting connections."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen()  # No backlog limit specified
            self.running = True
            self.logger.info(f"Server started on {self.host}:{self.port}")
            
            # Start the worker thread for processing messages
            worker_thread = threading.Thread(target=self._process_messages)
            worker_thread.daemon = True
            worker_thread.start()
            
            # Accept client connections
            self._accept_connections()
        except OSError as e:
            self.logger.error(f"Server error: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop the server and close all connections."""
        self.running = False
        
        # Close all client connections
        with self.client_lock:
            for client_id, client_socket in list(self.clients.items()):
                try:
                    client_socket.close()
                    self.logger.info(f"Closed connection to client {client_id}")
                except Exception as e:
                    self.logger.error(f"Error closing client {client_id}: {e}")
            self.clients.clear()
        
        # Close server socket
        if self.sock:
            self.sock.close()
            self.sock = None
        
        self.logger.info("Server stopped")
    
    def _accept_connections(self) -> None:
        """Accept incoming client connections."""
        self.logger.info("Waiting for client connections...")
        
        while self.running:
            try:
                client_socket, addr = self.sock.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                
                self.logger.info(f"New connection from {client_id}")
                
                with self.client_lock:
                    self.clients[client_id] = client_socket
                
                # Create a new thread to handle this client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_id)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_id: str) -> None:
        """
        Handle communication with a connected client.
        
        Args:
            client_socket: Socket connection to the client
            client_id: Unique identifier for the client
        """
        self.on_client_connected(client_id)
        
        buffer_size = 4096
        
        try:
            while self.running:
                try:
                    data = client_socket.recv(buffer_size)
                    if not data:
                        break
                    
                    # Add message to processing queue
                    self.message_queue.put((client_id, data))
                    
                except ConnectionResetError:
                    self.logger.warning(f"Connection reset by client {client_id}")
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving data from client {client_id}: {e}")
                    break
        finally:
            # Clean up when client disconnects
            with self.client_lock:
                if client_id in self.clients:
                    self.clients.pop(client_id)
                    client_socket.close()
            
            self.on_client_disconnected(client_id)
            self.logger.info(f"Client {client_id} disconnected")
    
    def _process_messages(self) -> None:
        """Process messages from the queue to avoid GIL contention."""
        while self.running:
            try:
                if not self.message_queue.empty():
                    client_id, data = self.message_queue.get(block=False)
                    self.on_message_received(client_id, data)
                    self.message_queue.task_done()
                else:
                    # Sleep briefly to reduce CPU usage
                    time.sleep(0.01)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    def send_to_client(self, client_id: str, message: bytes) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: Identifier of the client to send to
            message: Message bytes to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.client_lock:
            if client_id in self.clients:
                try:
                    self.clients[client_id].send(message)
                    return True
                except Exception as e:
                    self.logger.error(f"Error sending to client {client_id}: {e}")
        return False
    
    def broadcast(self, message: bytes, exclude: Optional[List[str]] = None) -> None:
        """
        Send a message to all connected clients.
        
        Args:
            message: Message bytes to send
            exclude: List of client IDs to exclude from broadcast
        """
        if exclude is None:
            exclude = []
        
        with self.client_lock:
            for client_id, client_socket in list(self.clients.items()):
                if client_id not in exclude:
                    try:
                        client_socket.send(message)
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to client {client_id}: {e}")
    
    def get_client_count(self) -> int:
        """Get the number of connected clients."""
        with self.client_lock:
            return len(self.clients)
    
    def get_client_list(self) -> List[str]:
        """Get a list of connected client IDs."""
        with self.client_lock:
            return list(self.clients.keys())
    
    # Override these methods in subclasses to customize behavior
    
    def on_client_connected(self, client_id: str) -> None:
        """
        Called when a new client connects.
        
        Args:
            client_id: ID of the newly connected client
        """
        self.logger.info(f"Client {client_id} connected")
    
    def on_client_disconnected(self, client_id: str) -> None:
        """
        Called when a client disconnects.
        
        Args:
            client_id: ID of the disconnected client
        """
        self.logger.info(f"Client {client_id} disconnected")
    
    def on_message_received(self, client_id: str, data: bytes) -> None:
        """
        Called when a message is received from a client.
        
        Args:
            client_id: ID of the client that sent the message
            data: Message data received
        """
        self.logger.info(f"Message from {client_id}: {data[:100]}...")
        # Echo the message back by default
        self.send_to_client(client_id, data)


# Example usage
if __name__ == "__main__":
    class EchoServer(Server):
        def on_message_received(self, client_id: str, data: bytes) -> None:
            message = data.decode('utf-8').strip()
            self.logger.info(f"Received from {client_id}: {message}")
            
            # Echo back to all clients
            response = f"Client {client_id}: {message}\n".encode('utf-8')
            self.broadcast(response)
    
    server = EchoServer(port=8000)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()