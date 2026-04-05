#ifndef PROTOCOL_H
#define PROTOCOL_H

using namespace std;

#include <boost/endian/conversion.hpp>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <tuple>
#include <vector>

// Message type enumeration
enum class MessageType : uint8_t { SYM_KEY_REQUEST = 1, SYM_KEY_RESPONSE = 2, TEXT_MESSAGE = 3, DEFAULT = 0 };

// Request codes for client actions
enum class RequestCode : uint16_t {
    SIGN_USER = 600,
    LIST_USERS = 601,
    GET_PUBLIC_KEY = 602,
    SEND_MESSAGE = 603,
    GET_MESSAGES = 604,
    DEFAULT = 0
};

// Response codes from server
enum class ResponseCode : uint16_t {
    USER_SIGNED = 2100,
    USERS_LIST = 2101,
    RETRIEVED_PUBLIC_KEY = 2102,
    MESSAGE_SENT = 2103,
    RETRIEVED_MESSAGES = 2104,
    ERROR_MESSAGE = 9000,
    DEFAULT = 0
};

// Protocol constants
static uint8_t VERSION = 1;
static uint32_t CLIENT_ID_BSIZE = 16;
static uint32_t VERSION_BSIZE = 1;
static uint32_t CODE_BSIZE = 2;
static uint32_t PAYLOAD_SIZE_BSIZE = 4;
static uint32_t NAME_BSIZE = 255;
static uint32_t USER_LIST_BSIZE = 255;
static uint32_t PUBLIC_KEY_BSIZE = 160;
static uint32_t MESSAGE_TYPE_BSIZE = 1;
static uint32_t MESSAGE_SIZE_BSIZE = 4;
static uint32_t MESSAGE_ID_BSIZE = 4;

// Request class for client-to-server messages
class Request {
private:
    vector<uint8_t> client_id;
    uint8_t version;
    RequestCode code;
    uint32_t payload_size;
    vector<uint8_t> name;
    vector<uint8_t> public_key;
    vector<uint8_t> other_client_id;
    MessageType message_type;
    uint32_t content_size;
    vector<uint8_t> message_content;

public:
    // Constructors for different request types
    Request();
    Request(vector<uint8_t>& client_id, RequestCode code);                                                      // For 601, 604
    Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& name, vector<uint8_t>& public_key);  // For 600
    Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& other_client_id);                    // For 602
    Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& other_client_id, MessageType message_type,
        vector<uint8_t>& message_content);  // For 603

    vector<uint8_t> serialize() const;
};

// Response class for server-to-client messages
class Response {
private:
    vector<uint8_t> raw;
    uint8_t version;
    ResponseCode code;
    uint32_t payload_size;
    vector<uint8_t> client_id;
    vector<uint8_t> other_client_id;
    vector<tuple<vector<uint8_t>, vector<uint8_t>>> client_name_list;
    vector<uint8_t> public_key;
    uint32_t message_id;
    vector<tuple<vector<uint8_t>, uint32_t, uint8_t, vector<uint8_t>>> messages_list;

public:
    // Getters
    const vector<uint8_t>& getRaw() const { return raw; }
    uint8_t getVersion() const { return version; }
    ResponseCode getCode() const { return code; }
    uint32_t getPayloadSize() const { return payload_size; }
    const vector<uint8_t>& getClientId() const { return client_id; }
    const vector<uint8_t>& getOtherClientId() const { return other_client_id; }
    const vector<tuple<vector<uint8_t>, vector<uint8_t>>>& getClientNameList() const { return client_name_list; }
    const vector<uint8_t>& getPublicKey() const { return public_key; }
    uint32_t getMessageId() const { return message_id; }
    const vector<tuple<vector<uint8_t>, uint32_t, uint8_t, vector<uint8_t>>>& getMessagesList() const { return messages_list; }

    // Constructors and validation
    Response();
    Response(vector<uint8_t>& raw_data);
    Response deserialize(const vector<uint8_t>& serialized_data);
    bool validate() const;
};

// Stream operators
ostream& operator<<(ostream& os, const vector<uint8_t>& data);

#endif  // PROTOCOL_H