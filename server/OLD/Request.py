import struct
import secrets

# Constants (assuming these are defined elsewhere in your code)
CLIENT_ID_BSIZE = 16
NAME_BSIZE = 255
PUBLIC_KEY_BSIZE = 160
MESSAGE_TYPE_BSIZE = 1
MESSAGE_SIZE_BSIZE = 4
VERSION_BSIZE = 1
CODE_BSIZE = 2
PAYLOAD_SIZE_BSIZE = 4


class HexBytes:
    def __init__(self, byte_string):
        # Store the byte string
        self.byte_string = byte_string

    def __str__(self):
        # Convert the byte string to a hexadecimal representation
        return " ".join(f"{byte:02x}" for byte in self.byte_string)

    def __repr__(self):
        # Optional: Define a representation for debugging
        return f"HexBytes({self.byte_string!r})"


class Request:
    def __init__(self, client_id=b'\x00' * CLIENT_ID_BSIZE, version=0, code=0, name=b'', public_key=b'\x00' * PUBLIC_KEY_BSIZE, other_client_id=b'\x00' * CLIENT_ID_BSIZE, message_type=0, message_content=b''):
        self.client_id = client_id
        self.version = version
        self.code = code

        # Payload
        self.payload_size = 0
        match self.code:
            case 600:  # sign a user
                self.payload_size += NAME_BSIZE
                self.name = name
                self.payload_size += PUBLIC_KEY_BSIZE
                self.public_key = public_key
                return

            case 601:  # Get users list
                return  # empty payload 

            case 602:  # Get public key
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                return

            case 603:  # send a message to other client
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                self.payload_size += MESSAGE_TYPE_BSIZE
                self.message_type = message_type
                self.payload_size += MESSAGE_SIZE_BSIZE
                self.content_size = len(message_content)
                self.payload_size += self.content_size
                self.message_content = message_content
                return

            case 604:
                return  # empty payload 

    def serialize(self):
        # Header
        client_id_data = struct.pack(f'<{CLIENT_ID_BSIZE}s', self.client_id)
        version_data = struct.pack('<B', self.version)
        code_data = struct.pack('<H', self.code)
        payload_size_data = struct.pack('<I', self.payload_size)

        # Payload
        payload_data = b''
        match self.code:
            case 600:  # sign a user
                payload_data += struct.pack(f'<{NAME_BSIZE}s', self.name + b'\0')
                payload_data += struct.pack(f'<{PUBLIC_KEY_BSIZE}s', self.public_key)

            case 602:  # Get public key
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id)

            case 603:  # send a message to other client
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id)
                payload_data += struct.pack('<B', self.message_type)
                payload_data += struct.pack('<I', self.content_size)
                payload_data += struct.pack(f'<{self.content_size}s', self.message_content)

        return client_id_data + version_data + code_data + payload_size_data + payload_data

    def deserialize(self, raw_data):
        offset = 0
        # Header
        self.client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
        offset += CLIENT_ID_BSIZE
        self.version = struct.unpack('<B', raw_data[offset:offset+VERSION_BSIZE])[0]
        offset += VERSION_BSIZE
        self.code = struct.unpack('<H', raw_data[offset:offset+CODE_BSIZE])[0]
        offset += CODE_BSIZE
        self.payload_size = struct.unpack('<I', raw_data[offset:offset+PAYLOAD_SIZE_BSIZE])[0]
        offset += PAYLOAD_SIZE_BSIZE

        # Payload
        match self.code:
            case 600:  # sign a user
                # Read the name up to the first '\0' character
                name_bytes = raw_data[offset:offset+NAME_BSIZE]
                null_index = name_bytes.find(b'\0')
                if null_index != -1:
                    self.name = name_bytes[:null_index]
                else:
                    self.name = name_bytes
                offset += NAME_BSIZE
                self.public_key = struct.unpack(f'<{PUBLIC_KEY_BSIZE}s', raw_data[offset:offset+PUBLIC_KEY_BSIZE])[0]
                offset += PUBLIC_KEY_BSIZE

            case 602:  # Get public key
                self.other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE

            case 603:  # send a message to other client
                self.other_client_id = struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0]
                offset += CLIENT_ID_BSIZE
                self.message_type = struct.unpack('<B', raw_data[offset:offset+MESSAGE_TYPE_BSIZE])[0]
                offset += MESSAGE_TYPE_BSIZE
                self.content_size = struct.unpack('<I', raw_data[offset:offset+MESSAGE_SIZE_BSIZE])[0]
                offset += MESSAGE_SIZE_BSIZE
                self.message_content = struct.unpack(f'<{self.content_size}s', raw_data[offset:offset+self.content_size])[0]
                offset += self.content_size

        return self

    def __str__(self):
        output = (
            f"Request:\n"
            f"client_id={HexBytes(self.client_id)}\n"
            f"version={self.version}\n"
            f"code={self.code}\n"
            f"payload_size={self.payload_size}\n"
        )
        match self.code:
            case 600:  # sign a user
                output += f"name= {self.name}\n"
                output += f"public_key= {HexBytes(self.public_key)}\n"
            case 602:  # Get public key
                output += f"other_client_id= {HexBytes(self.other_client_id)}\n"
            case 603:  # send a message to other client
                output += f"other_client_id= {HexBytes(self.other_client_id)}\n"
                output += f"message_type= {self.message_type}\n"
                output += f"content_size= {self.content_size}\n"
                output += f"message_content= {self.message_content}\n"
        return output

    def __eq__(self, other):
        if not isinstance(other, Request):
            return NotImplemented
        match self.code:
            case 600:  # sign a user
                return (
                    self.client_id == other.client_id and
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.name == other.name and
                    self.public_key == other.public_key
                )
            case 602:  # Get public key
                return (
                    self.client_id == other.client_id and
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id
                )
            case 603:  # send a message to other client
                return (
                    self.client_id == other.client_id and
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id and
                    self.message_type == other.message_type and
                    self.content_size == other.content_size and
                    self.message_content == other.message_content
                )
            case _:
                return (
                    self.client_id == other.client_id and
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size
                )

    def __ne__(self, other):
        return not self.__eq__(other)
    

def test_request_class():
    # Generate a random 16-byte client_id
    randomized_id = secrets.token_bytes(CLIENT_ID_BSIZE)

    # Test case 1: Code 600 (Sign a user)
    request_600 = Request(client_id=randomized_id, version=1, code=600, name=b"Alice", public_key=secrets.token_bytes(PUBLIC_KEY_BSIZE))
    serialized_600 = request_600.serialize()
    deserialized_600 = Request().deserialize(serialized_600)
    print("serialized_600:")
    print(HexBytes(serialized_600),'\n')
    print(deserialized_600)
    assert request_600 == deserialized_600, "Test case 600 failed"

    # Test case 2: Code 601 (Get users list)
    request_601 = Request(client_id=randomized_id, version=1, code=601)
    serialized_601 = request_601.serialize()
    deserialized_601 = Request().deserialize(serialized_601)
    print("serialized_601:")
    print(HexBytes(serialized_601),'\n')
    print(deserialized_601)
    assert request_601 == deserialized_601, "Test case 601 failed"

    # Test case 3: Code 602 (Get public key)
    request_602 = Request(client_id=randomized_id, version=1, code=602, other_client_id=secrets.token_bytes(CLIENT_ID_BSIZE))
    serialized_602 = request_602.serialize()
    deserialized_602 = Request().deserialize(serialized_602)
    print("serialized_602:")
    print(HexBytes(serialized_602),'\n')
    print(deserialized_602)
    assert request_602 == deserialized_602, "Test case 602 failed"

    # Test case 4: Code 603 (Send a message to another client)
    request_603 = Request(client_id=randomized_id, version=1, code=603, other_client_id=secrets.token_bytes(CLIENT_ID_BSIZE), message_type=1, message_content=b"Hello, World!")
    serialized_603 = request_603.serialize()
    deserialized_603 = Request().deserialize(serialized_603)
    print("serialized_603:")
    print(HexBytes(serialized_603),'\n')
    print(deserialized_603)
    assert request_603 == deserialized_603, "Test case 603 failed"

    # Test case 5: Code 604 (Empty payload)
    request_604 = Request(client_id=randomized_id, version=1, code=604)
    serialized_604 = request_604.serialize()
    deserialized_604 = Request().deserialize(serialized_604)
    print("serialized_604:")
    print(HexBytes(serialized_604),'\n')
    print(deserialized_604)
    assert request_604 == deserialized_604, "Test case 604 failed"

    print("All test cases passed!")

# Run the test function
if __name__ == "__main__":
    test_request_class()