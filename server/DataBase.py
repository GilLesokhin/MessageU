from Protocol import MessageType, NAME_BSIZE, PUBLIC_KEY_BSIZE, CLIENT_ID_BSIZE
import uuid
import threading

PUBLIC_KEY_INDEX = 1
MAX_UINT4 = 4294967295

class DataBase:
    def __init__(self):
        # Dictionary for users: (client_id, public_key) -> (username)
        self._users = {}
        # Dictionary for messages: (message_id, to_client_id) -> (from_client_id, msg_type, content)
        self._messages = {}
        # Initialize lock for thread safety
        self._lock = threading.Lock()

    # 600
    def add_user(self, username, public_key):
        if len(username) > NAME_BSIZE:
            raise ValueError(f"Username must not exceed {NAME_BSIZE} bytes")
        if len(public_key) != PUBLIC_KEY_BSIZE:
            raise ValueError(f"Public key must be exactly {PUBLIC_KEY_BSIZE} bytes")

        # Generate random 16-byte client_id
        client_id = uuid.uuid4().bytes  
        while client_id in self._users:
            client_id = uuid.uuid4().bytes
        
        with self._lock:
            self._users[client_id] = (username, public_key)
            return client_id
    
    def user_exists(self, username):
        if len(username) > NAME_BSIZE:
            raise ValueError(f"Username must not exceed {NAME_BSIZE} bytes")
        with self._lock:
            for (name, _) in self._users.values():
                if name == username:
                    return True
            return False
        
    # 601
    def get_users_list(self, client_id):
        if len(client_id) != CLIENT_ID_BSIZE:
            raise ValueError(f"Client ID must be {CLIENT_ID_BSIZE} bytes")
        with self._lock:
            users_list = []
            for cid, (uname, _) in self._users.items():
                if cid != client_id:
                    users_list.append((cid, uname))
            users_list.sort(key=lambda x: x[0])
            return users_list

    # 602
    def get_public_key(self, client_id):
        if len(client_id) != CLIENT_ID_BSIZE:
            raise ValueError(f"Client ID must be {CLIENT_ID_BSIZE} bytes")
        
        with self._lock:
            if client_id not in self._users:
                raise ValueError("Invalid client ID")
            return self._users[client_id][PUBLIC_KEY_INDEX]  
    
    # 603
    def send_message(self, to_client_id, from_client_id, msg_type, content):
        if len(to_client_id) != CLIENT_ID_BSIZE or len(from_client_id) != CLIENT_ID_BSIZE:
            raise ValueError(f"Client IDs must be {CLIENT_ID_BSIZE} bytes")
        if not isinstance(msg_type, MessageType):
            raise ValueError("Message type must be a MessageType enum value")
        
        with self._lock:
            if to_client_id not in self._users or from_client_id not in self._users:
                raise ValueError("Invalid client ID")
            
            message_id = -1
            for (msg_id, tcid) in self._messages:
                if tcid == to_client_id:
                    message_id = max(msg_id, message_id)
            message_id += 1
        
            self._messages[(message_id, to_client_id)] = (from_client_id, msg_type, content)
            return message_id

    # 604
    def get_messages(self, to_client_id):
        """
        Retrieve all messages for a specific client.
        """
        if len(to_client_id) != CLIENT_ID_BSIZE:
            raise ValueError(f"Client ID must be {CLIENT_ID_BSIZE} bytes")
        
        with self._lock:
            if to_client_id not in self._users:
                raise ValueError("Invalid client ID")

            # Collect all messages for the specified to_client_id
            messages = []
            del_list = []
            for (msg_id, tcid), (fcid, msg_type, content) in self._messages.items():
                if tcid == to_client_id:
                    messages.append((fcid, msg_id, msg_type, content))
                    del_list.append((msg_id, tcid))
            
            # Sort messages by msg_id
            messages.sort(key=lambda x: x[1])
            for key in del_list:
                del self._messages[key]
            return messages
    
    def delete_message(self, message_id, to_client_id):
        if not (0 <= message_id <= MAX_UINT4):
            raise ValueError(f"Message ID must be between 0 and {MAX_UINT4}")
        
        with self._lock:
            key = (message_id, to_client_id)
            if key in self._messages:
                del self._messages[key]
            else:
                raise KeyError(f"Message with ID {message_id} not found")
            
            
    def __str__(self):
        """
        Returns a string representation of the database, including all users and messages.
        Thread-safe implementation using the database lock.
        """
        with self._lock:
            # Build the string representation
            output = []
            
            # Users section
            output.append("=== Users ===")
            if not self._users:
                output.append("No users in database")
            else:
                for client_id, (username, public_key) in self._users.items():
                    output.append(f"Client ID: {client_id.hex()}")
                    output.append(f"  Username: {username}")
                    output.append(f"  Public Key: {public_key.hex()}")
                    output.append("")

            # Messages section
            output.append("=== Messages ===")
            if not self._messages:
                output.append("No messages in database")
            else:
                for (msg_id, to_client_id), (from_client_id, msg_type, content) in self._messages.items():
                    output.append(f"Message ID: {msg_id}")
                    output.append(f"  To Client ID: {to_client_id.hex()}")
                    output.append(f"  From Client ID: {from_client_id.hex()}")
                    output.append(f"  Message Type: {msg_type.name}")
                    output.append(f"  Content: {content.hex()}")
                    output.append("")

            # Join all lines with newlines
            return "\n".join(output).rstrip()  # rstrip removes trailing newline