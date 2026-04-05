from enum import Enum
from Utilities import HexBytes
import struct

class MessageType(Enum):
    SYM_KEY_REQUEST = 1    # Symmetric key request
    SYM_KEY_RESPONSE = 2   # Symmetric key response
    TEXT_MESSAGE = 3       # Text message
    FILE_MESSAGE = 4       # File message
    DEFAULT = 0  # Default Message Type

class RequestCode(Enum):
    SIGN_USER = 600  # Request to sign in a user
    LIST_USERS = 601  # Request to retrieve the list of client names
    GET_PUBLIC_KEY = 602  # Request to obtain a public key
    SEND_MESSAGE = 603  # Request to send a message
    GET_MESSAGES = 604  # Request to retrieve messages
    DEFAULT = 0  # Default request code

class ResponseCode(Enum):
    USER_SIGNED = 2100  # User successfully signed in
    USER_LIST = 2101  # Retrieved client name list
    SEND_PUBLIC_KEY = 2102  # Retrieved public key
    MESSAGE_SENT = 2103  # Message ID response
    MESSAGES_RETRIEVED = 2104  # Sent message response
    ERROR_MESSAGE = 9000  # General ERROR_MESSAGE response
    DEFAULT = 0  # Default response

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
    def __init__(self, client_id=b'', code=None, name=b'', public_key=b'', 
                 other_client_id=b'', message_type=None, message_content=b''):
        self._client_id = client_id
        self._version = VERSION
        self._code = code
        self._payload_size = 0
        self._name = name
        self._public_key = public_key
        self._other_client_id = other_client_id
        self._message_type = message_type
        self._message_content = message_content
        self._content_size = len(message_content)

        if self._code:
            match self._code:
                case RequestCode.SIGN_USER:
                    self._payload_size += NAME_BSIZE + PUBLIC_KEY_BSIZE
                case RequestCode.LIST_USERS:
                    pass
                case RequestCode.GET_PUBLIC_KEY:
                    self._payload_size += CLIENT_ID_BSIZE
                case RequestCode.SEND_MESSAGE:
                    self._payload_size += CLIENT_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE + self._content_size
                case RequestCode.GET_MESSAGES:
                    pass
    def validate(self):
        return True                    
    # Getters
    def get_client_id(self):
        return self._client_id
    
    def get_version(self):
        return self._version
    
    def get_code(self):
        return self._code
    
    def get_payload_size(self):
        return self._payload_size
    
    def get_name(self):
        return self._name
    
    def get_public_key(self):
        return self._public_key
    
    def get_other_client_id(self):
        return self._other_client_id
    
    def get_message_type(self):
        return self._message_type
    
    def get_message_content(self):
        return self._message_content
    
    def get_content_size(self):
        return self._content_size

    def serialize(self):
        client_id_data = struct.pack(f'<{CLIENT_ID_BSIZE}s', self._client_id)
        version_data = struct.pack('<B', self._version)
        code_data = struct.pack('<H', self._code.value)
        payload_size_data = struct.pack('<I', self._payload_size)

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

        return client_id_data + version_data + code_data + payload_size_data + payload_data

    def deserialize(self, raw_data):
        offset = 0
        self._client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
        offset += CLIENT_ID_BSIZE
        self._version = struct.unpack('<B', raw_data[offset:offset+VERSION_BSIZE])[0]
        offset += VERSION_BSIZE
        code_value = struct.unpack('<H', raw_data[offset:offset+CODE_BSIZE])[0]
        self._code = RequestCode(code_value)
        offset += CODE_BSIZE
        self._payload_size = struct.unpack('<I', raw_data[offset:offset+PAYLOAD_SIZE_BSIZE])[0]
        offset += PAYLOAD_SIZE_BSIZE

        match self._code:
            case RequestCode.SIGN_USER:

                name_bytes = raw_data[offset:offset+NAME_BSIZE]
                self._name = name_bytes.split(b'\0')[0] + b'\0'
                
                offset += NAME_BSIZE
                self._public_key = struct.unpack(f'<{PUBLIC_KEY_BSIZE}s', raw_data[offset:offset+PUBLIC_KEY_BSIZE])[0]
            case RequestCode.GET_PUBLIC_KEY:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
            case RequestCode.SEND_MESSAGE:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                message_type_value = struct.unpack('<B', raw_data[offset:offset+MESSAGE_TYPE_BSIZE])[0]
                self._message_type = MessageType(message_type_value)
                offset += MESSAGE_TYPE_BSIZE
                self._content_size = struct.unpack('<I', raw_data[offset:offset+MESSAGE_SIZE_BSIZE])[0]
                offset += MESSAGE_SIZE_BSIZE
                self._message_content = struct.unpack(f'<{self._content_size}s', raw_data[offset:offset+self._content_size])[0]

        return self

    def __str__(self):
        output = (
            f"Request:\n"
            f"client_id={HexBytes(self._client_id)}\n"
            f"version={self._version}\n"
            f"code={self._code}\n"
            f"payload_size={self._payload_size}\n"
        )
        match self._code:
            case RequestCode.SIGN_USER:
                output += f"name={self._name}\n"
                output += f"public_key={HexBytes(self._public_key)}\n"
            case RequestCode.GET_PUBLIC_KEY:
                output += f"other_client_id={HexBytes(self._other_client_id)}\n"
            case RequestCode.SEND_MESSAGE:
                output += f"other_client_id={HexBytes(self._other_client_id)}\n"
                output += f"message_type={self._message_type}\n"
                output += f"content_size={self._content_size}\n"
                output += f"message_content={self._message_content}\n"
        return output

    def __eq__(self, other):
        if not isinstance(other, Request):
            return NotImplemented
        match self._code:
            case RequestCode.SIGN_USER:
                return (self._client_id == other._client_id and self._version == other._version and
                        self._code == other._code and self._payload_size == other._payload_size and
                        self._name == other._name and self._public_key == other._public_key)
            case RequestCode.GET_PUBLIC_KEY:
                return (self._client_id == other._client_id and self._version == other._version and
                        self._code == other._code and self._payload_size == other._payload_size and
                        self._other_client_id == other._other_client_id)
            case RequestCode.SEND_MESSAGE:
                return (self._client_id == other._client_id and self._version == other._version and
                        self._code == other._code and self._payload_size == other._payload_size and
                        self._other_client_id == other._other_client_id and self._message_type == other._message_type and
                        self._content_size == other._content_size and self._message_content == other._message_content)
            case _:
                return (self._client_id == other._client_id and self._version == other._version and
                        self._code == other._code and self._payload_size == other._payload_size)

    def __ne__(self, other):
        return not self.__eq__(other)

class Response:
    def __init__(self, code=None, other_client_id=b'', client_name_list=b'', 
                 public_key=b'', message_id=0, message_type=0, message_content=b''):
        self._version = VERSION
        self._code = code
        self._payload_size = 0
        self._other_client_id = other_client_id
        self._client_name_list = client_name_list
        self._public_key = public_key
        self._message_id = message_id
        self._message_type = message_type
        self._message_content = message_content
        self._content_size = len(message_content)

        if self._code:
            match self._code:
                case ResponseCode.USER_SIGNED:
                    self._payload_size += CLIENT_ID_BSIZE
                case ResponseCode.USER_LIST:
                    self._payload_size += CLIENT_ID_BSIZE + NAME_BSIZE
                case ResponseCode.SEND_PUBLIC_KEY:
                    self._payload_size += CLIENT_ID_BSIZE + PUBLIC_KEY_BSIZE
                case ResponseCode.MESSAGE_SENT:
                    self._payload_size += CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE
                case ResponseCode.MESSAGES_RETRIEVED:
                    self._payload_size += (CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE + 
                                         MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE + self._content_size)
                case ResponseCode.ERROR_MESSAGE:
                    pass

    # Getters
    def get_version(self):
        return self._version
    
    def get_code(self):
        return self._code
    
    def get_payload_size(self):
        return self._payload_size
    
    def get_other_client_id(self):
        return self._other_client_id
    
    def get_client_name_list(self):
        return self._client_name_list
    
    def get_public_key(self):
        return self._public_key
    
    def get_message_id(self):
        return self._message_id
    
    def get_message_type(self):
        return self._message_type
    
    def get_message_content(self):
        return self._message_content
    
    def get_content_size(self):
        return self._content_size


    def serialize(self):
        version_data = struct.pack('<B', self._version)
        code_data = struct.pack('<H', self._code.value)
        payload_size_data = struct.pack('<I', self._payload_size)
        payload_data = b''
        
        match self._code:
            case ResponseCode.USER_SIGNED:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
            case ResponseCode.USER_LIST:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack(f'<{NAME_BSIZE}s', self._client_name_list)
            case ResponseCode.SEND_PUBLIC_KEY:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack(f'<{PUBLIC_KEY_BSIZE}s', self._public_key)
            case ResponseCode.MESSAGE_SENT:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack('<I', self._message_id)
            case ResponseCode.MESSAGES_RETRIEVED:
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self._other_client_id)
                payload_data += struct.pack('<I', self._message_id)
                payload_data += struct.pack('<B', self._message_type.value)
                payload_data += struct.pack('<I', self._content_size)
                payload_data += struct.pack(f'<{self._content_size}s', self._message_content)
        
        return version_data + code_data + payload_size_data + payload_data

    def deserialize(self, raw_data):
        offset = 0
        self._version = struct.unpack('<B', raw_data[offset:offset+VERSION_BSIZE])[0]
        offset += VERSION_BSIZE
        code_value = struct.unpack('<H', raw_data[offset:offset+CODE_BSIZE])[0]
        self._code = ResponseCode(code_value)
        offset += CODE_BSIZE
        self._payload_size = struct.unpack('<I', raw_data[offset:offset+PAYLOAD_SIZE_BSIZE])[0]
        offset += PAYLOAD_SIZE_BSIZE

        match self._code:
            case ResponseCode.USER_SIGNED:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
            case ResponseCode.USER_LIST:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE

                name_list_bytes = raw_data[offset:offset+NAME_BSIZE]
                null_index = name_list_bytes.find(b'\0')
                self._client_name_list = name_list_bytes[:null_index] if null_index != -1 else name_list_bytes

            case ResponseCode.SEND_PUBLIC_KEY:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                self._public_key = struct.unpack(f'<{PUBLIC_KEY_BSIZE}s', raw_data[offset:offset+PUBLIC_KEY_BSIZE])[0]
            case ResponseCode.MESSAGE_SENT:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                self._message_id = struct.unpack('<I', raw_data[offset:offset+MESSAGE_ID_BSIZE])[0]
            case ResponseCode.MESSAGES_RETRIEVED:
                self._other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                self._message_id = struct.unpack('<I', raw_data[offset:offset+MESSAGE_ID_BSIZE])[0]
                offset += MESSAGE_ID_BSIZE
                message_type_value = struct.unpack('<B', raw_data[offset:offset+MESSAGE_TYPE_BSIZE])[0]
                self._message_type = MessageType(message_type_value)
                offset += MESSAGE_TYPE_BSIZE
                self._content_size = struct.unpack('<I', raw_data[offset:offset+MESSAGE_SIZE_BSIZE])[0]
                offset += MESSAGE_SIZE_BSIZE
                self._message_content = struct.unpack(f'<{self._content_size}s', raw_data[offset:offset+self._content_size])[0]

        return self

    def __str__(self):
        output = (
            f"Response:\n"
            f"version={self._version}\n"
            f"code={self._code.name} ({self._code.value})\n"
            f"payload_size={self._payload_size}\n"
        )
        
        match self._code:
            case ResponseCode.USER_SIGNED:
                output += f"other_client_id={self._other_client_id.hex()}\n"
            case ResponseCode.USER_LIST:
                output += f"other_client_id={self._other_client_id.hex()}\n"
                output += f"client_name_list={self._client_name_list}\n"
            case ResponseCode.SEND_PUBLIC_KEY:
                output += f"other_client_id={self._other_client_id.hex()}\n"
                output += f"public_key={self._public_key.hex()}\n"
            case ResponseCode.MESSAGE_SENT:
                output += f"other_client_id={self._other_client_id.hex()}\n"
                output += f"message_id={self._message_id}\n"
            case ResponseCode.MESSAGES_RETRIEVED:
                output += f"other_client_id={self._other_client_id.hex()}\n"
                output += f"message_id={self._message_id}\n"
                output += f"message_type={self._message_type.value}\n"
                output += f"content_size={self._content_size}\n"
                output += f"message_content={self._message_content}\n"

        return output

    def __eq__(self, other):
        if not isinstance(other, Response):
            return NotImplemented
        match self._code:
            case ResponseCode.USER_SIGNED:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size and self._other_client_id == other._other_client_id)
            case ResponseCode.USER_LIST:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size and self._other_client_id == other._other_client_id and
                        self._client_name_list == other._client_name_list)
            case ResponseCode.SEND_PUBLIC_KEY:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size and self._other_client_id == other._other_client_id and
                        self._public_key == other._public_key)
            case ResponseCode.MESSAGE_SENT:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size and self._other_client_id == other._other_client_id and
                        self._message_id == other._message_id)
            case ResponseCode.MESSAGES_RETRIEVED:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size and self._other_client_id == other._other_client_id and
                        self._message_id == other._message_id and self._message_type == other._message_type and
                        self._content_size == other._content_size and self._message_content == other._message_content)
            case ResponseCode.ERROR_MESSAGE:
                return (self._version == other._version and self._code == other._code and
                        self._payload_size == other._payload_size)

    def __ne__(self, other):
        return not self.__eq__(other)