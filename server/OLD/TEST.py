import unittest
import uuid
from Protocol import MessageType
from Utilities import HexBytes
from Protocol import RequestCode, ResponseCode, Request, Response,MessageType, CLIENT_ID_BSIZE, NAME_BSIZE, PUBLIC_KEY_BSIZE



class TestProtocol(unittest.TestCase):

    def test_request_serialization_deserialization(self):
        # Test data
        client_id = b'\x01' * CLIENT_ID_BSIZE
        version = 1
        name = b'\xAA' * (NAME_BSIZE - 1) + b'\0'
        public_key = b'\x02' * PUBLIC_KEY_BSIZE
        other_client_id = b'\x03' * CLIENT_ID_BSIZE
        message_type = MessageType.SYM_KEY_REQUEST
        message_content = b'Hello, World!'

        # Test each request type
        request_codes = [
            (RequestCode.SIGN_USER, {'name': name, 'public_key': public_key}),
            (RequestCode.LIST_USERS, {}),
            (RequestCode.GET_PUBLIC_KEY, {'other_client_id': other_client_id}),
            (RequestCode.SEND_MESSAGE, {'other_client_id': other_client_id, 'message_type': message_type, 'message_content': message_content}),
            (RequestCode.GET_MESSAGES, {})
        ]

        for code, payload in request_codes:
            with self.subTest(code=code):
                # Create request
                request = Request(client_id=client_id, code=code, **payload)
                request.validate()
                # Serialize
                serialized = request.serialize()
                # Deserialize
                deserialized_request = Request().deserialize(serialized)
                deserialized_request.validate()
                # Check equality
                self.assertEqual(request, deserialized_request)

    def test_response_serialization_deserialization(self):
        # Test data
        version = 1
        other_client_id = b'\x01' * CLIENT_ID_BSIZE
        client_name_list = b'\xAA' * (NAME_BSIZE - 1) + b'\0'
        public_key = b'\x02' * PUBLIC_KEY_BSIZE
        message_id = 12345
        message_type = MessageType.SYM_KEY_REQUEST
        message_content = b'Hello, World!'

        # Test each response type
        response_codes = [
            (ResponseCode.USER_SIGNED, {'other_client_id': other_client_id}),
            (ResponseCode.USER_LIST, {'other_client_id': other_client_id, 'client_name_list': client_name_list}),
            (ResponseCode.SEND_PUBLIC_KEY, {'other_client_id': other_client_id, 'public_key': public_key}),
            (ResponseCode.MESSAGE_SENT, {'other_client_id': other_client_id, 'message_id': message_id}),
            (ResponseCode.MESSAGES_RETRIEVED, {'other_client_id': other_client_id, 'message_id': message_id, 'message_type': message_type, 'message_content': message_content}),
            (ResponseCode.ERROR_MESSAGE, {})
        ]


        for code, payload in response_codes:
            with self.subTest(code=code):
                # Create response
                response = Response(code=code, **payload)
                # Serialize
                serialized = response.serialize()
                # Deserialize
                deserialized_response = Response().deserialize(serialized)
                # Check equality

                self.assertEqual(response, deserialized_response)

if __name__ == '__main__':
    unittest.main()