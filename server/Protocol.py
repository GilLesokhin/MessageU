from enum import Enum
import struct

class MessageType(Enum):
    SYM_KEY_REQUEST = 1    # Symmetric key request
    SYM_KEY_RESPONSE = 2   # Symmetric key response
    TEXT = 3       # Text message
    DEFAULT = 0            # Default Message Type

class RequestCode(Enum):
    SIGN_USER = 600  # Request to sign in a user
    LIST_USERS = 601  # Request to retrieve the list of client names
    GET_PUBLIC_KEY = 602  # Request to obtain a public key
    SEND_MESSAGE = 603  # Request to send a message
    GET_MESSAGES = 604  # Request to retrieve messages

class ResponseCode(Enum):
    USER_SIGNED = 2100  # User successfully signed in
    USERS_LIST = 2101  # Retrieved client name list
    RETRIEVED_PUBLIC_KEY = 2102  # Retrieved public key
    MESSAGE_SENT = 2103  # Message ID response
    RETRIEVED_MESSAGES = 2104  # Sent message response
    ERROR_MESSAGE = 9000  # General ERROR_MESSAGE response

# Constants defining the byte sizes for various fields in the protocol
CLIENT_ID_BSIZE = 16  # Byte size for client ID
VERSION_BSIZE = 1     # Byte size for version
CODE_BSIZE = 2        # Byte size for request code
PAYLOAD_SIZE_BSIZE = 4  # Byte size for payload size
NAME_BSIZE = 255      # Byte size for name field
PUBLIC_KEY_BSIZE = 160  # Byte size for public key
MESSAGE_TYPE_BSIZE = 1  # Byte size for message type
MESSAGE_SIZE_BSIZE = 4  # Byte size for message size
MESSAGE_ID_BSIZE = 4    # Byte size for message ID

VERSION = 1

class Request:   
    def __init__(self, raw_data=b''):
        self._client_id = b''
        self._version = VERSION
        self._code = None
        self._payload_size = 0
        self._name = b''
        self._public_key = b''
        self._other_client_id = b''
        self._message_type = None
        self._message_content = b''
        self._content_size = 0

        if not raw_data==b'':
            self.deserialize(raw_data)
                   
    def serialize(self):
        client_id_data = struct.pack(f'<{CLIENT_ID_BSIZE}s', self._client_id)
        version_data = struct.pack('<B', self._version)
        code_data = struct.pack('<H', self._code.value)
        payload_size_data = struct.pack('<I', self._payload_size)

        header_data = client_id_data + version_data + code_data + payload_size_data

        payload_data = b''
        match self._code:
            case RequestCode.SIGN_USER:
                payload_data += struct.pack(f'<{NAME_BSIZE}s', self._name)
                payload_data += struct.pack(f'<{PUBLIC_KEY_BSIZE}s', self._public_key)
            case RequestCode.GET_PUBLIC_KEY:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
            case RequestCode.SEND_MESSAGE:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack('<B', self._message_type.value)
                payload_data += struct.pack('<I', self._content_size)
                payload_data += struct.pack(f'<{self._content_size}s', self._message_content)

        return header_data + payload_data

    def deserialize(self, raw_data):
        offset = 0
        min_length = CLIENT_ID_BSIZE + VERSION_BSIZE + CODE_BSIZE + PAYLOAD_SIZE_BSIZE
        if len(raw_data) < min_length:
            raise ValueError(f"raw_data too short: expected at least {min_length} bytes, got {len(raw_data)}")

        self._client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset + CLIENT_ID_BSIZE])[0]
        offset += CLIENT_ID_BSIZE

        self._version = struct.unpack('<B', raw_data[offset:offset + VERSION_BSIZE])[0]
        offset += VERSION_BSIZE

        code_value = struct.unpack('<H', raw_data[offset:offset + CODE_BSIZE])[0]
        self._code = RequestCode(code_value)
        offset += CODE_BSIZE

        self._payload_size = struct.unpack('<I', raw_data[offset:offset + PAYLOAD_SIZE_BSIZE])[0]
        offset += PAYLOAD_SIZE_BSIZE

        remaining_data = len(raw_data) - offset
        if self._payload_size != remaining_data:
            raise ValueError(f"Payload size mismatch: expected {self._payload_size} bytes, but {remaining_data} bytes remain")
        
        # Validate remaining data based on RequestCode
        match self._code:
            case RequestCode.SIGN_USER:
                if len(raw_data) < offset + NAME_BSIZE + PUBLIC_KEY_BSIZE:
                    raise ValueError("Insufficient data for SIGN_USER payload")
                self._name = raw_data[offset:offset + NAME_BSIZE]
                offset += NAME_BSIZE
                self._public_key = struct.unpack(f'<{PUBLIC_KEY_BSIZE}s', raw_data[offset:offset + PUBLIC_KEY_BSIZE])[0]
            case RequestCode.GET_PUBLIC_KEY:
                if len(raw_data) < offset + CLIENT_ID_BSIZE:
                    raise ValueError("Insufficient data for GET_PUBLIC_KEY payload")
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset + CLIENT_ID_BSIZE])[0]
            case RequestCode.SEND_MESSAGE:
                if len(raw_data) < offset + CLIENT_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE:
                    raise ValueError("Insufficient data for SEND_MESSAGE header")
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset + CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                message_type_value = struct.unpack('<B', raw_data[offset:offset + MESSAGE_TYPE_BSIZE])[0]
                self._message_type = MessageType(message_type_value)
                offset += MESSAGE_TYPE_BSIZE
                self._content_size = struct.unpack('<I', raw_data[offset:offset + MESSAGE_SIZE_BSIZE])[0]
                offset += MESSAGE_SIZE_BSIZE
                if len(raw_data) < offset + self._content_size:
                    raise ValueError(f"Insufficient data for message content: expected {self._content_size} bytes")
                if self._content_size < 0:  # Optional: sanity check
                    raise ValueError(f"Invalid content size: {self._content_size}")
                self._message_content = struct.unpack(f'<{self._content_size}s', raw_data[offset:offset + self._content_size])[0]

        return self
    
    def get_client_id(self):
        """Returns the client ID as bytes."""
        return self._client_id
    
    def get_code(self):
        """Returns the client ID as bytes."""
        return self._code

    def get_name(self):
        """Returns the name as bytes."""
        return self._name

    def get_public_key(self):
        """Returns the public key as bytes."""
        return self._public_key

    def get_other_client_id(self):
        """Returns the other client ID as bytes."""
        return self._other_client_id

    def get_message_type(self):
        """Returns the message type (MessageType enum)."""
        return self._message_type

    def get_message_content(self):
        """Returns the message content as bytes."""
        return self._message_content

    def validate(self):
        """
        Validates the request data based on protocol requirements.
        Returns True if valid, False otherwise.
        """
        # Check if code is valid
        if not self._code or not isinstance(self._code, RequestCode):
            return False
        
        # Check version
        if self._version != VERSION:
            return False
        
        # Check client_id is bytes and correct length
        if not isinstance(self._client_id, bytes) or len(self._client_id) != CLIENT_ID_BSIZE:
            return False
        
        # Validate based on specific request code
        match self._code:
            case RequestCode.SIGN_USER:
                # Check name is bytes, exists, isn't too long, and contains null terminator
                if not isinstance(self._name, bytes) or not self._name or len(self._name) != NAME_BSIZE:
                    return False
                if b'\0' not in self._name:
                    return False
                self._name = self._name.split(b'\0')[0]
                if not self._name:  # Empty string before null is invalid
                    return False
                # Check if name contains only ASCII characters
                if not all(0 <= char < 128 for char in self._name):
                    return False
                self._name += b'\0'
                # Check public key is bytes and correct length
                if not isinstance(self._public_key, bytes) or not self._public_key or len(self._public_key) != PUBLIC_KEY_BSIZE:
                    return False
                # Check payload size
                expected_size = NAME_BSIZE + PUBLIC_KEY_BSIZE
                if self._payload_size != expected_size:
                    return False
                    
            case RequestCode.LIST_USERS:
                # No additional payload expected
                if self._payload_size != 0:
                    return False
                    
            case RequestCode.GET_PUBLIC_KEY:
                # Check other_client_id is bytes and correct length
                if not isinstance(self._other_client_id, bytes) or not self._other_client_id or len(self._other_client_id) != CLIENT_ID_BSIZE:
                    return False
                # Check payload size
                if self._payload_size != CLIENT_ID_BSIZE:
                    return False
                    
            case RequestCode.SEND_MESSAGE:
                # Check other_client_id is bytes and correct length
                if not isinstance(self._other_client_id, bytes) or not self._other_client_id or len(self._other_client_id) != CLIENT_ID_BSIZE:
                    return False
                # Check message type
                if not self._message_type or not isinstance(self._message_type, MessageType):
                    return False
                # Check message content is bytes and size matches
                if not isinstance(self._message_content, bytes) or self._message_content is None or self._content_size != len(self._message_content):
                    return False
                # Check payload size
                expected_size = CLIENT_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE + self._content_size
                if self._payload_size != expected_size:
                    return False
                    
            case RequestCode.GET_MESSAGES:
                # No additional payload expected
                if self._payload_size != 0:
                    return False
                    
            case _:
                return False
        return True
    
    def __str__(self):
        return str(self.serialize().hex())
    
    def __eq__(self, other):
        if self is None:
            False
        return str(self.serialize()) == str(other.serialize())

    def __ne__(self, other):
        return not self.__eq__(other)
    
class Response:
    def __init__(self, code=None, client_id=b'', other_client_id=b'', client_name_list= [], 
                 public_key=b'', message_id = b'', messages_list_payload = []):
        self._version = VERSION
        self._code = code
        self._payload_size = 0
        self._client_id = client_id
        self._other_client_id = other_client_id
        self._client_name_list = client_name_list
        self._public_key = public_key
        self._message_id = message_id
        self._messages_list = messages_list_payload

        if self._code:
            match self._code:
                case ResponseCode.USER_SIGNED:
                    self._payload_size = CLIENT_ID_BSIZE
                case ResponseCode.USERS_LIST:
                    self._payload_size = len(client_name_list) * (CLIENT_ID_BSIZE + NAME_BSIZE)

                case ResponseCode.RETRIEVED_PUBLIC_KEY:
                    self._payload_size = CLIENT_ID_BSIZE + PUBLIC_KEY_BSIZE

                case ResponseCode.MESSAGE_SENT:
                    self._payload_size = CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE

                case ResponseCode.RETRIEVED_MESSAGES:
                    for (_, _, _, content) in self._messages_list:
                        self._payload_size += CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE + len(content)

                case ResponseCode.ERROR_MESSAGE:
                    pass

    def serialize(self):
        version_data = struct.pack('<B', self._version)
        code_data = struct.pack('<H', self._code.value)
        payload_size_data = struct.pack('<I', self._payload_size)
        payload_data = b''
        header_data = version_data + code_data + payload_size_data

        match self._code:
            case ResponseCode.USER_SIGNED:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._client_id)

            case ResponseCode.USERS_LIST:
                for (other_client_id, client_name) in self._client_name_list:
                    payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', other_client_id)
                    payload_data += struct.pack(f'<{NAME_BSIZE}s', client_name)
            
            case ResponseCode.RETRIEVED_PUBLIC_KEY:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._client_id)
                payload_data += struct.pack(f'<{PUBLIC_KEY_BSIZE}s', self._public_key)
                
            case ResponseCode.MESSAGE_SENT:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack('<I', self._message_id)
            
            case ResponseCode.RETRIEVED_MESSAGES:
                for (fcid, msg_id, msg_type, content) in self._messages_list:
                    payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', fcid)
                    payload_data += struct.pack('<I', msg_id)
                    payload_data += struct.pack('<B', msg_type.value)
                    payload_data += struct.pack('<I', len(content))
                    payload_data += struct.pack(f'<{len(content)}s', content)

        return header_data + payload_data

    def __str__(self):
        return str(self.serialize().hex())
    
    def __eq__(self, other):
        return str(self.serialize()) == str(other.serialize())

    def __ne__(self, other):
        return not self.__eq__(other)