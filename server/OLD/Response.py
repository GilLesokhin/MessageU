import struct

# Constants
CLIENT_ID_BSIZE = 16
VERSION_BSIZE = 1
CODE_BSIZE = 2
PAYLOAD_SIZE_BSIZE = 4
NAME_BSIZE = 255
PUBLIC_KEY_BSIZE = 160
MESSAGE_TYPE_BSIZE = 1
MESSAGE_SIZE_BSIZE = 4
MESSAGE_ID_BSIZE = 4


class Response:
    def __init__(self, version=0, code=0, other_client_id=0, client_name_list=b'', public_key=0, message_id=0, message_type=0, message_content=b''):
        self.version = version
        self.code = code

        # Payload
        self.payload_size = 0
        match self.code:
            case 2100:  # user successfully signed
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                return

            case 2101:  # get client name list
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                self.payload_size += NAME_BSIZE
                self.client_name_list = client_name_list
                return

            case 2102:  # get public key
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                self.payload_size += PUBLIC_KEY_BSIZE
                self.public_key = public_key
                return

            case 2103:  # message ID response
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                self.payload_size += MESSAGE_ID_BSIZE
                self.message_id = message_id
                return

            case 2104:  # send message response
                self.payload_size += CLIENT_ID_BSIZE
                self.other_client_id = other_client_id
                self.payload_size += MESSAGE_ID_BSIZE
                self.message_id = message_id
                self.payload_size += MESSAGE_TYPE_BSIZE
                self.message_type = message_type
                self.payload_size += MESSAGE_SIZE_BSIZE
                self.content_size = len(message_content)
                self.payload_size += self.content_size
                self.message_content = message_content
                return

            case 9000:  # error response
                return

    def serialize(self):
        # Header
        version_data = struct.pack('<B', self.version)
        code_data = struct.pack('<H', self.code)
        payload_size_data = struct.pack('<I', self.payload_size)

        # Payload
        payload_data = b''
        match self.code:
            case 2100:  # user successfully signed
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id.to_bytes(CLIENT_ID_BSIZE, 'little'))

            case 2101:  # get client name list
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id.to_bytes(CLIENT_ID_BSIZE, 'little'))
                payload_data += struct.pack(f'<{NAME_BSIZE}s', self.client_name_list + b'\0')

            case 2102:  # get public key
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id.to_bytes(CLIENT_ID_BSIZE, 'little'))
                payload_data += struct.pack(f'<{PUBLIC_KEY_BSIZE}s', self.public_key.to_bytes(PUBLIC_KEY_BSIZE, 'little'))

            case 2103:  # message ID response
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id.to_bytes(CLIENT_ID_BSIZE, 'little'))
                payload_data += struct.pack('<I', self.message_id)

            case 2104:  # send message response
                payload_data += struct.pack(f'<{CLIENT_ID_BSIZE}s', self.other_client_id.to_bytes(CLIENT_ID_BSIZE, 'little'))
                payload_data += struct.pack('<I', self.message_id)
                payload_data += struct.pack('<B', self.message_type)
                payload_data += struct.pack('<I', self.content_size)
                payload_data += struct.pack(f'<{self.content_size}s', self.message_content)

        return version_data + code_data + payload_size_data + payload_data

    def deserialize(self, raw_data):
        offset = 0
        # Header
        self.version = struct.unpack('<B', raw_data[offset:offset+VERSION_BSIZE])[0]
        offset += VERSION_BSIZE
        self.code = struct.unpack('<H', raw_data[offset:offset+CODE_BSIZE])[0]
        offset += CODE_BSIZE
        self.payload_size = struct.unpack('<I', raw_data[offset:offset+PAYLOAD_SIZE_BSIZE])[0]
        offset += PAYLOAD_SIZE_BSIZE

        # Payload
        match self.code:
            case 2100:  # user successfully signed
                self.other_client_id = int.from_bytes(struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0], 'little')
                offset += CLIENT_ID_BSIZE

            case 2101:  # get client name list
                self.other_client_id = int.from_bytes(struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0], 'little')
                offset += CLIENT_ID_BSIZE

                # Read the name up to the first '\0' character
                name_list_bytes = raw_data[offset:offset+NAME_BSIZE]
                null_index = name_list_bytes.find(b'\0')
                if null_index != -1:
                    self.client_name_list = name_list_bytes[:null_index]
                else:
                    self.client_name_list = name_list_bytes
                offset += NAME_BSIZE

            case 2102:  # get public key
                self.other_client_id = int.from_bytes(struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0], 'little')
                offset += CLIENT_ID_BSIZE
                self.public_key = int.from_bytes(struct.unpack(f'<{PUBLIC_KEY_BSIZE}s', raw_data[offset:offset+PUBLIC_KEY_BSIZE])[0], 'little')
                offset += PUBLIC_KEY_BSIZE

            case 2103:  # message ID response
                self.other_client_id = int.from_bytes(struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0], 'little')
                offset += CLIENT_ID_BSIZE
                self.message_id = struct.unpack('<I', raw_data[offset:offset+MESSAGE_ID_BSIZE])[0]
                offset += MESSAGE_ID_BSIZE

            case 2104:  # send message response
                self.other_client_id = int.from_bytes(struct.unpack(f'<{CLIENT_ID_BSIZE}s', raw_data[offset:offset+CLIENT_ID_BSIZE])[0], 'little')
                offset += CLIENT_ID_BSIZE
                self.message_id = struct.unpack('<I', raw_data[offset:offset+MESSAGE_ID_BSIZE])[0]
                offset += MESSAGE_ID_BSIZE
                self.message_type = struct.unpack('<B', raw_data[offset:offset+MESSAGE_TYPE_BSIZE])[0]
                offset += MESSAGE_TYPE_BSIZE
                self.content_size = struct.unpack('<I', raw_data[offset:offset+MESSAGE_SIZE_BSIZE])[0]
                offset += MESSAGE_SIZE_BSIZE
                self.message_content = struct.unpack(f'<{self.content_size}s', raw_data[offset:offset+self.content_size])[0]
                offset += self.content_size

        return self

    def __str__(self):
        output = (
            f"Response:\n"
            f"version={self.version}\n"
            f"code={self.code}\n"
            f"payload_size={self.payload_size}\n"
        )
        match self.code:
            case 2100:  # user successfully signed
                output += f"other_client_id={self.other_client_id}\n"
            case 2101:  # get client name list
                output += f"other_client_id={self.other_client_id}\n"
                output += f"client_name_list={self.client_name_list}\n"
            case 2102:  # get public key
                output += f"other_client_id={self.other_client_id}\n"
                output += f"public_key={self.public_key}\n"
            case 2103:  # message ID response
                output += f"other_client_id={self.other_client_id}\n"
                output += f"message_id={self.message_id}\n"
            case 2104:  # send message response
                output += f"other_client_id={self.other_client_id}\n"
                output += f"message_id={self.message_id}\n"
                output += f"message_type={self.message_type}\n"
                output += f"content_size={self.content_size}\n"
                output += f"message_content={self.message_content}\n"
        return output

    def __eq__(self, other):
        if not isinstance(other, Response):
            return NotImplemented
        match self.code:
            case 2100:  # user successfully signed
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id
                )
            case 2101:  # get client name list
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id and
                    self.client_name_list == other.client_name_list
                )
            case 2102:  # get public key
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id and
                    self.public_key == other.public_key
                )
            case 2103:  # message ID response
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id and
                    self.message_id == other.message_id
                )
            case 2104:  # send message response
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size and
                    self.other_client_id == other.other_client_id and
                    self.message_id == other.message_id and
                    self.message_type == other.message_type and
                    self.content_size == other.content_size and
                    self.message_content == other.message_content
                )
            case 9000:  # error response
                return (
                    self.version == other.version and
                    self.code == other.code and
                    self.payload_size == other.payload_size
                )
            

def test_response_class():
    # Test case 1: Code 2100 (User successfully signed)
    response_2100 = Response(version=1, code=2100, other_client_id=123)
    serialized_2100 = response_2100.serialize()
    deserialized_2100 = Response().deserialize(serialized_2100)
    assert response_2100 == deserialized_2100, "Test case 2100 failed"

    # Test case 2: Code 2101 (Get client name list)
    response_2101 = Response(version=1, code=2101, other_client_id=123, client_name_list=b"Alice")
    serialized_2101 = response_2101.serialize()
    deserialized_2101 = Response().deserialize(serialized_2101)

    print(response_2101)
    print(deserialized_2101)
    assert response_2101 == deserialized_2101, "Test case 2101 failed"

    # Test case 3: Code 2102 (Get public key)
    response_2102 = Response(version=1, code=2102, other_client_id=123, public_key=456)
    serialized_2102 = response_2102.serialize()
    deserialized_2102 = Response().deserialize(serialized_2102)
    assert response_2102 == deserialized_2102, "Test case 2102 failed"

    # Test case 4: Code 2103 (Message ID response)
    response_2103 = Response(version=1, code=2103, other_client_id=123, message_id=789)
    serialized_2103 = response_2103.serialize()
    deserialized_2103 = Response().deserialize(serialized_2103)
    assert response_2103 == deserialized_2103, "Test case 2103 failed"

    # Test case 5: Code 2104 (Send message response)
    response_2104 = Response(version=1, code=2104, other_client_id=123, message_id=789, message_type=1, message_content=b"Hello, World!")
    serialized_2104 = response_2104.serialize()
    deserialized_2104 = Response().deserialize(serialized_2104)
    assert response_2104 == deserialized_2104, "Test case 2104 failed"

    # Test case 6: Code 9000 (Error response)
    response_9000 = Response(version=1, code=9000)
    serialized_9000 = response_9000.serialize()
    deserialized_9000 = Response().deserialize(serialized_9000)
    assert response_9000 == deserialized_9000, "Test case 9000 failed"

    print("All test cases passed!")

# Run the test function
test_response_class()