import unittest
import struct
from unittest.mock import Mock

from Protocol import Request, Response, RequestCode, ResponseCode, MessageType, CLIENT_ID_BSIZE, VERSION, NAME_BSIZE, PUBLIC_KEY_BSIZE, MESSAGE_ID_BSIZE
import uuid
from DataBase import DataBase
from Server import Server

DEFAULT_PORT = 1357
PORT_FILE = "myport.info"

class TestRequestHandler(unittest.TestCase):
    def setUp(self):
        # Initialize Server with a mock database
        self.server = Server()
        self.server.db = Mock(spec=DataBase)
        
    def test_invalid_request(self):
        # Test case for invalid request validation
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = False
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.ERROR_MESSAGE)

    def test_sign_user_success(self):
        # Test successful user signing
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.SIGN_USER
        mock_request.get_name.return_value = b"testuser\n"
        mock_request.get_public_key.return_value = b"public_key"
        
        self.server.db.user_exists.return_value = False
        self.server.db.add_user.return_value = b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04'
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.USER_SIGNED)
        self.assertEqual(response._client_id, b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04')
        self.server.db.add_user.assert_called_once_with(b"testuser\n", b"public_key")

    def test_sign_user_already_exists(self):
        # Test signing user that already exists
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.SIGN_USER
        mock_request.get_name.return_value = b"testuser\n"
        
        self.server.db.user_exists.return_value = True
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.ERROR_MESSAGE)
        self.server.db.add_user.assert_not_called()

    def test_list_users_success(self):
        # Test successful user list retrieval
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.LIST_USERS
        mock_request.get_client_id.return_value = b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04'
        
        mock_user_list = ["user1", "user2"]
        self.server.db.get_users_list.return_value = mock_user_list
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.USERS_LIST)
        self.assertEqual(response._client_name_list, mock_user_list)
        self.server.db.get_users_list.assert_called_once_with(b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04')

    def test_get_public_key_success(self):
        # Test successful public key retrieval
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.GET_PUBLIC_KEY
        mock_request.get_other_client_id.return_value = b"target_id_456"
        
        self.server.db.get_public_key.return_value = b"public_key_456"
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.RETRIEVED_PUBLIC_KEY)
        self.assertEqual(response._public_key, b"public_key_456")
        self.server.db.get_public_key.assert_called_once_with(b"target_id_456")

    def test_send_message_success(self):
        # Test successful message sending
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.SEND_MESSAGE
        mock_request.get_client_id.return_value = b"from_id_123"
        mock_request.get_other_client_id.return_value = b"to_id_456"
        mock_request.get_message_type.return_value = MessageType.TEXT
        mock_request.get_message_content.return_value = b"hello"
        
        self.server.db.send_message.return_value = 789
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.MESSAGE_SENT)
        self.assertEqual(response._other_client_id, b"to_id_456")
        self.assertEqual(response._message_id, 789)
        self.server.db.send_message.assert_called_once_with(
            to_client_id=b"to_id_456",
            from_client_id=b"from_id_123",
            msg_type=MessageType.TEXT,
            content=b"hello"
        )

    def test_get_messages_success(self):
        # Test successful messages retrieval
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.GET_MESSAGES
        mock_request.get_client_id.return_value = b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04'
        
        mock_messages = [(b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04', 0 , MessageType.TEXT, b'hello world!')]
        self.server.db.get_messages.return_value = mock_messages
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.RETRIEVED_MESSAGES)
        self.server.db.get_messages.assert_called_once()

    def test_database_error(self):
        # Test case where database throws an exception
        mock_request = Mock(spec=Request)
        mock_request.validate.return_value = True
        mock_request.get_code.return_value = RequestCode.LIST_USERS
        mock_request.get_client_id.return_value = b'\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04\x01\x02\x03\x04'
        
        self.server.db.get_users_list.side_effect = Exception("Database error")
        
        response = self.server._request_handler(mock_request)
        
        self.assertEqual(response._code, ResponseCode.ERROR_MESSAGE)


class TestDataBase(unittest.TestCase):
    def setUp(self):
        """Set up a fresh database instance before each test"""
        self.db = DataBase()
        # Sample data for testing
        self.username1 = b"alice\0"
        self.username2 = b"bob\0"
        self.public_key1 = b'1' * PUBLIC_KEY_BSIZE
        self.public_key2 = b'2' * PUBLIC_KEY_BSIZE
        self.content = b"Hello, World!"

    def test_add_user(self):
        """Test adding users to the database"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        self.assertEqual(len(client_id1), CLIENT_ID_BSIZE)
        self.assertEqual(self.db._users[client_id1], (self.username1, self.public_key1))

        # Test duplicate username (should still work with different client_id)
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        self.assertNotEqual(client_id1, client_id2)

        # Test invalid username length
        with self.assertRaises(ValueError):
            self.db.add_user("a" * (NAME_BSIZE + 1), self.public_key1)

        # Test invalid public key length
        with self.assertRaises(ValueError):
            self.db.add_user(self.username1, b'1' * (PUBLIC_KEY_BSIZE - 1))

    def test_user_exists(self):
        """Test checking if a user exists in the database"""
        # Test 1: Empty database - should return False
        self.assertFalse(self.db.user_exists("alice"), "Expected False for non-existent user in empty database")

        # Test 2: Add a user and check if it exists
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        self.assertTrue(self.db.user_exists(self.username1), "Expected True for existing user 'alice'")

        # Test 3: Check a different username that doesn't exist
        self.assertFalse(self.db.user_exists("bob"), "Expected False for non-existent user 'bob'")

        # Test 4: Add another user and verify both exist
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        self.assertTrue(self.db.user_exists(self.username1), "Expected True for existing user 'alice'")
        self.assertTrue(self.db.user_exists(self.username2), "Expected True for existing user 'bob'")

        # Test 5: Test with username exceeding NAME_BSIZE
        long_username = "a" * (NAME_BSIZE + 1)
        with self.assertRaises(ValueError) as context:
            self.db.user_exists(long_username)
        self.assertEqual(str(context.exception), f"Username must not exceed {NAME_BSIZE} bytes")

        # Test 6: Case sensitivity test (assuming usernames are case-sensitive)
        self.assertFalse(self.db.user_exists("Alice"), "Expected False for 'Alice' when 'alice' exists")

    def test_get_users_list(self):
        """Test retrieving the users list"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        
        users_list = self.db.get_users_list(client_id1)
        self.assertEqual(len(users_list), 1)  # Should only show other users
        self.assertEqual(users_list[0], (client_id2, self.username2))

        # Test invalid client_id length
        with self.assertRaises(ValueError):
            self.db.get_users_list(b'1' * (CLIENT_ID_BSIZE - 1))

    def test_get_public_key(self):
        """Test retrieving a user's public key"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        
        public_key = self.db.get_public_key(client_id1)
        self.assertEqual(public_key, self.public_key1)

        # Test invalid client_id
        with self.assertRaises(ValueError):
            self.db.get_public_key(uuid.uuid4().bytes)

        # Test invalid client_id length
        with self.assertRaises(ValueError):
            self.db.get_public_key(b'1' * (CLIENT_ID_BSIZE - 1))

    def test_send_message(self):
        """Test sending messages between users"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        
        msg_id = self.db.send_message(client_id2, client_id1, MessageType.TEXT, self.content)
        self.assertEqual(msg_id, 0)
        self.assertEqual(self.db._messages[(0, client_id2)], (client_id1, MessageType.TEXT, self.content))

        # Test second message to same client
        msg_id2 = self.db.send_message(client_id2, client_id1, MessageType.TEXT, self.content)
        self.assertEqual(msg_id2, 1)

        # Test invalid client_ids
        with self.assertRaises(ValueError):
            self.db.send_message(uuid.uuid4().bytes, client_id1, MessageType.TEXT, self.content)

        # Test invalid message type
        with self.assertRaises(ValueError):
            self.db.send_message(client_id2, client_id1, "not_a_type", self.content)

    def test_get_messages(self):
        """Test retrieving messages for a client"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        
        self.db.send_message(client_id2, client_id1, MessageType.TEXT, self.content)
        messages = self.db.get_messages(client_id2)
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], (client_id1, 0, MessageType.TEXT, self.content))
        
        # Verify message was deleted after retrieval
        self.assertEqual(len(self.db._messages), 0)

        # Test invalid client_id
        with self.assertRaises(ValueError):
            self.db.get_messages(uuid.uuid4().bytes)

    def test_delete_message(self):
        """Test deleting a message"""
        client_id1 = self.db.add_user(self.username1, self.public_key1)
        client_id2 = self.db.add_user(self.username2, self.public_key2)
        
        msg_id = self.db.send_message(client_id2, client_id1, MessageType.TEXT, self.content)
        self.db.delete_message(msg_id, client_id2)
        
        self.assertNotIn((msg_id, client_id2), self.db._messages)

        # Test deleting non-existent message
        with self.assertRaises(KeyError):
            self.db.delete_message(999, client_id2)

        # Test invalid message_id
        with self.assertRaises(ValueError):
            self.db.delete_message(-1, client_id2)

    def test_thread_safety(self):
        """Basic test for thread safety"""
        import threading
        
        def add_users():
            for i in range(10):
                self.db.add_user(f"user{i}", bytes([i] * PUBLIC_KEY_BSIZE))
        
        threads = [threading.Thread(target=add_users) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(self.db._users), 30)  # 3 threads * 10 users each


class TestProtocol(unittest.TestCase):
    def setUp(self):
        # Common test data
        self.client_id = b'client1234567890'  # 16 bytes
        self._other_client_id = b'otherclient12345'  # 16 bytes
        self.name = b"testuser\0" + b'\0' + b'\x00' * (NAME_BSIZE - 9)  # 255 bytes with null terminator
        self.public_key = b'p' * PUBLIC_KEY_BSIZE  # 160 bytes
        self.message_content = b"Hello, world!"
        self.message_id = b'msg1'  # 4 bytes

    # Test Request class
    def test_request_sign_user_serialize_deserialize(self):
        req = Request()
        req._client_id = self.client_id
        req._code = RequestCode.SIGN_USER
        req._name = self.name
        req._public_key = self.public_key
        req._payload_size = NAME_BSIZE + PUBLIC_KEY_BSIZE

        serialized = req.serialize()
        deserialized = Request()  # Create a new instance
        deserialized.deserialize(serialized)  # Deserialize into it

        self.assertEqual(req, deserialized)
        self.assertTrue(deserialized.validate())
        self.assertEqual(deserialized.get_client_id(), self.client_id)
        self.assertEqual(deserialized.get_code(), RequestCode.SIGN_USER)
        self.assertEqual(deserialized.get_name(), b"testuser\0" )
        self.assertEqual(deserialized.get_public_key(), self.public_key)

    def test_request_get_public_key(self):
        req = Request()
        req._client_id = self.client_id
        req._code = RequestCode.GET_PUBLIC_KEY
        req._other_client_id = self._other_client_id
        req._payload_size = CLIENT_ID_BSIZE

        serialized = req.serialize()
        deserialized = Request()
        deserialized.deserialize(serialized)

        self.assertEqual(req, deserialized)
        self.assertTrue(deserialized.validate())
        self.assertEqual(deserialized.get_other_client_id(), self._other_client_id)

    def test_request_send_message(self):
        req = Request()
        req._client_id = self.client_id
        req._code = RequestCode.SEND_MESSAGE
        req._other_client_id = self._other_client_id
        req._message_type = MessageType.TEXT
        req._message_content = self.message_content
        req._content_size = len(self.message_content)
        req._payload_size = CLIENT_ID_BSIZE + 1 + 4 + len(self.message_content)

        serialized = req.serialize()
        deserialized = Request()
        deserialized.deserialize(serialized)

        self.assertEqual(req, deserialized)
        self.assertTrue(deserialized.validate())
        self.assertEqual(deserialized.get_message_type(), MessageType.TEXT)
        self.assertEqual(deserialized.get_message_content(), self.message_content)

    def test_request_invalid_payload_size(self):
        req = Request()
        req._client_id = self.client_id
        req._code = RequestCode.SIGN_USER
        req._name = self.name
        req._public_key = self.public_key
        req._payload_size = NAME_BSIZE  # Incorrect payload size

        self.assertFalse(req.validate())

    def test_request_deserialize_insufficient_data(self):
        req = Request()
        raw_data = b'123'  # Too short
        with self.assertRaises(ValueError):
            req.deserialize(raw_data)

    # Test Response class
    def test_response_user_signed(self):
        resp = Response(
            code=ResponseCode.USER_SIGNED,
            client_id=self.client_id
        )
        serialized = resp.serialize()
        self.assertEqual(len(serialized), 7 + CLIENT_ID_BSIZE)  # Header + client_id
        self.assertEqual(serialized[0], VERSION)
        self.assertEqual(struct.unpack('<H', serialized[1:3])[0], ResponseCode.USER_SIGNED.value)

    def test_response_users_list(self):
        client_name_list = [(self.client_id, self.name), (self._other_client_id, self.name)]
        resp = Response(
            code=ResponseCode.USERS_LIST,
            client_name_list=client_name_list
        )
        serialized = resp.serialize()
        expected_size = 7 + len(client_name_list) * (CLIENT_ID_BSIZE + NAME_BSIZE)
        self.assertEqual(len(serialized), expected_size)

    def test_response_retrieved_public_key(self):
        resp = Response(
            code=ResponseCode.RETRIEVED_PUBLIC_KEY,
            client_id=self.client_id,
            public_key=self.public_key
        )
        serialized = resp.serialize()
        self.assertEqual(len(serialized), 7 + CLIENT_ID_BSIZE + PUBLIC_KEY_BSIZE)

    def test_response_message_sent(self):
        resp = Response(
            code=ResponseCode.MESSAGE_SENT,
            other_client_id=self._other_client_id,
            message_id=self.message_id
        )
        serialized = resp.serialize()
        self.assertEqual(len(serialized), 7 + CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE)

    def test_response_retrieved_messages(self):
        messages_list = [
            (self.client_id, 1, MessageType.TEXT, self.message_content),
            (self._other_client_id, 2, MessageType.SYM_KEY_REQUEST, b"key")
        ]
        resp = Response(
            code=ResponseCode.RETRIEVED_MESSAGES,
            messages_list_payload=messages_list
        )
        serialized = resp.serialize()
        expected_size = 7
        for _, _, _, content in messages_list:
            expected_size += CLIENT_ID_BSIZE + 4 + 1 + 4 + len(content)
        self.assertEqual(len(serialized), expected_size)

    def test_response_equality(self):
        resp1 = Response(code=ResponseCode.USER_SIGNED, client_id=self.client_id)
        resp2 = Response(code=ResponseCode.USER_SIGNED, client_id=self.client_id)
        resp3 = Response(code=ResponseCode.ERROR_MESSAGE)
        self.assertEqual(resp1, resp2)
        self.assertNotEqual(resp1, resp3)

if __name__ == '__main__':
    unittest.main()