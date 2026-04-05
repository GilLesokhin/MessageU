#include "Protocol.h"

using namespace std;

// Request class implementation just to create an object
Request::Request() {
    this->client_id = { 0 };                      
    this->version = VERSION;                    
    this->code = RequestCode::DEFAULT;          
    this->payload_size = 0;                     
    this->name = { 0 };                           
    this->public_key = { 0 };                     
    this->other_client_id = { 0 };               
    this->message_type = MessageType::DEFAULT;  
    this->content_size = 0;                     
    this->message_content = { 0 };               
}


// Real constractors that will be used based on Code
Request::Request(vector<uint8_t>& client_id, RequestCode code) {
    if (code != RequestCode::LIST_USERS && code != RequestCode::GET_MESSAGES) {
        throw exception("Invalid code: expected LIST_USERS or GET_MESSAGES");
    }
    *this = Request();            // Initialize with default constructor
    this->client_id = client_id;  // Set client ID
    this->version = VERSION;      // Set version
    this->code = code;            // Set request code
    this->payload_size = 0;       // No payload for these requests
}

Request::Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& name, vector<uint8_t>& public_key) {
    if (code != RequestCode::SIGN_USER) {
        throw exception("Invalid code: expected SIGN_USER");
    }
    *this = Request();                                   // Initialize with default constructor
    this->client_id = client_id;                         // Set client ID
    this->version = VERSION;                             // Set version
    this->code = code;                                   // Set request code
    this->payload_size = NAME_BSIZE + PUBLIC_KEY_BSIZE;  // Calculate payload size
    this->name = name;                                   // Set name
    this->public_key = public_key;                       // Set public key
}

Request::Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& other_client_id) {
    if (code != RequestCode::GET_PUBLIC_KEY) {
        throw exception("Invalid code: expected GET_PUBLIC_KEY");
    }
    *this = Request();                        // Initialize with default constructor
    this->client_id = client_id;              // Set client ID
    this->version = VERSION;                  // Set version
    this->code = code;                        // Set request code
    this->payload_size = CLIENT_ID_BSIZE;     // Payload size for other client ID
    this->other_client_id = other_client_id;  // Set other client ID
}

Request::Request(vector<uint8_t>& client_id, RequestCode code, vector<uint8_t>& other_client_id, MessageType message_type,
    vector<uint8_t>& message_content) {
    if (code != RequestCode::SEND_MESSAGE) {
        throw exception("Invalid code: expected SEND_MESSAGE");
    }
    *this = Request();            // Initialize with default constructor
    this->client_id = client_id;  // Set client ID
    this->version = VERSION;      // Set version
    this->code = code;            // Set request code
    this->payload_size =
        CLIENT_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE + uint32_t(message_content.size());  // Calculate payload size
    this->other_client_id = other_client_id;                                                           // Set other client ID
    this->message_type = message_type;                                                                 // Set message type
    this->content_size = static_cast<uint32_t>(message_content.size());                                // Set content size
    this->message_content = message_content;                                                           // Set message content
}

vector<uint8_t> Request::serialize() const {
    vector<uint8_t> serialized_data;

    // Lambda to pack raw bytes (Simular to the functionality of Python pack)
    auto pack_raw = [&serialized_data](const void* value, size_t size) {
        const uint8_t* bytes = static_cast<const uint8_t*>(value);
        serialized_data.insert(serialized_data.end(), bytes, bytes + size);
        };
    // Lambda function to pack vectors with padding at the end if needed (Simular to the functionality of Python pack)
    auto pack_vector = [&serialized_data](const vector<uint8_t>& vec, size_t fixed_size) {
        serialized_data.insert(serialized_data.end(), vec.begin(), vec.begin() + min(vec.size(), fixed_size));
        if (vec.size() < fixed_size) {
            serialized_data.insert(serialized_data.end(), fixed_size - vec.size(), '0');
        }
        };

    // Serialize header based on request code
    pack_vector(this->client_id, CLIENT_ID_BSIZE);                                          
    uint8_t version_le = boost::endian::native_to_little(this->version);                    
    pack_raw(&version_le, VERSION_BSIZE);                                                   
    uint16_t code_le = boost::endian::native_to_little(static_cast<uint16_t>(this->code));  
    pack_raw(&code_le, CODE_BSIZE);                                                      
    uint32_t payload_size_le = boost::endian::native_to_little(this->payload_size);       
    pack_raw(&payload_size_le, PAYLOAD_SIZE_BSIZE);                                       

    uint8_t message_type_le;
    uint32_t content_size_le;

    // Serialize payload based on request code
    switch (this->code) {
    case RequestCode::SIGN_USER:
        pack_vector(this->name, NAME_BSIZE);              
        pack_vector(this->public_key, PUBLIC_KEY_BSIZE);  
        break;
    case RequestCode::GET_PUBLIC_KEY:
        pack_vector(this->other_client_id, CLIENT_ID_BSIZE);  
        break;
    case RequestCode::SEND_MESSAGE:
        pack_vector(this->other_client_id, CLIENT_ID_BSIZE);                                          
        message_type_le = boost::endian::native_to_little(static_cast<uint8_t>(this->message_type)); 
        pack_raw(&message_type_le, MESSAGE_TYPE_BSIZE);                                               
        content_size_le = boost::endian::native_to_little(this->content_size);                       
        pack_raw(&content_size_le, MESSAGE_SIZE_BSIZE);                                              
        pack_vector(this->message_content, this->content_size);                                       
        break;
    case RequestCode::LIST_USERS:
    case RequestCode::GET_MESSAGES:
        break;  // No payload
    default:
        return {};
    }
    return serialized_data;
}

// Response class implementation just to create an object
Response::Response() {
    this->version = VERSION;
    this->code = ResponseCode::DEFAULT;
    this->payload_size = 0;
    this->public_key = {};
    this->message_id = 0;
    this->client_id = {};
    this->other_client_id = {};
    this->client_name_list = {};
    this->messages_list = {};
}
// Real constractors that will be used based on Code
Response::Response(vector<uint8_t>& raw_data) {
    *this = deserialize(raw_data);
    this->raw = raw_data;
}

// Function to deserialize Raw data from server
Response Response::deserialize(const vector<uint8_t>& data) {
    size_t payload_end;
    if (data.size() < (VERSION_BSIZE + CODE_BSIZE + PAYLOAD_SIZE_BSIZE)) {
        return Response();
    }
    Response response;
    size_t offset = 0;

    // Lambda to unpack raw bytes
    auto unpack_raw = [&data, &offset](void* value, size_t size) {
        if (offset + size > data.size()) {
            throw exception("Invalid data: insufficient size for raw unpack");
        }
        memcpy(value, data.data() + offset, size);
        offset += size;
        };
    // Lambda to unpack vectors
    auto unpack_vector = [&data, &offset](vector<uint8_t>& vec, size_t fixed_size) {
        if (offset + fixed_size > data.size()) {
            throw exception("Invalid data: insufficient size for vector unpack");
        }
        vec.assign(data.begin() + offset, data.begin() + offset + fixed_size);
        offset += fixed_size;
        };

    uint8_t version_raw;
    unpack_raw(&version_raw, VERSION_BSIZE);                          // Unpack version
    response.version = boost::endian::little_to_native(version_raw);  // Convert to native

    uint16_t code_raw;
    unpack_raw(&code_raw, CODE_BSIZE);                                                     // Unpack code
    response.code = static_cast<ResponseCode>(boost::endian::little_to_native(code_raw));  // Convert to native

    uint32_t payload_size_raw;
    unpack_raw(&payload_size_raw, PAYLOAD_SIZE_BSIZE);                          // Unpack payload size
    response.payload_size = boost::endian::little_to_native(payload_size_raw);  // Convert to native

    // Unpack payload based on response code
    switch (response.code) {
    case ResponseCode::USER_SIGNED:
        unpack_vector(response.client_id, CLIENT_ID_BSIZE);  // Unpack client ID
        break;
    case ResponseCode::USERS_LIST:
        payload_end = offset + response.payload_size;  // Calculate payload size
        while (offset < payload_end) {
            // Unpack
            vector<uint8_t> client_id;
            unpack_vector(client_id, CLIENT_ID_BSIZE);
            vector<uint8_t> name;
            unpack_vector(name, NAME_BSIZE);
            response.client_name_list.emplace_back(client_id, name);  // Add to list
        }
        break;
    case ResponseCode::RETRIEVED_PUBLIC_KEY:
        unpack_vector(response.other_client_id, CLIENT_ID_BSIZE);  // Unpack other client ID
        unpack_vector(response.public_key, PUBLIC_KEY_BSIZE);      // Unpack public key
        break;
    case ResponseCode::MESSAGE_SENT:
        unpack_vector(response.other_client_id, CLIENT_ID_BSIZE);               // Unpack other client ID
        uint32_t message_id_raw;                                                // Temp message ID
        unpack_raw(&message_id_raw, MESSAGE_ID_BSIZE);                          // Unpack message ID
        response.message_id = boost::endian::little_to_native(message_id_raw);  // Convert to native
        break;
    case ResponseCode::RETRIEVED_MESSAGES:
        payload_end = offset + response.payload_size;  // Calculate payload size
        while (offset < payload_end) {
            // Unpack content
            vector<uint8_t> client_id;
            unpack_vector(client_id, CLIENT_ID_BSIZE);
            uint32_t message_id_raw;
            unpack_raw(&message_id_raw, MESSAGE_ID_BSIZE);
            uint32_t message_id = boost::endian::little_to_native(message_id_raw);
            uint8_t message_type;
            unpack_raw(&message_type, MESSAGE_TYPE_BSIZE);
            uint32_t content_len_raw;
            unpack_raw(&content_len_raw, MESSAGE_SIZE_BSIZE);
            uint32_t content_len = boost::endian::little_to_native(content_len_raw);
            vector<uint8_t> content;
            unpack_vector(content, content_len);
            response.messages_list.emplace_back(client_id, message_id, message_type, content);  // Add to list
        }
        break;
    case ResponseCode::ERROR_MESSAGE:
        break;
    }
    // Check for extra bytes
    if (offset != data.size()) {
        throw exception("Invalid data: extra bytes found after expected end");
    }

    return response;
}

// Validate the data received
bool Response::validate() const {
    if (version != VERSION) {
        return false;
    }

    uint32_t expected_payload_size = 0;

    switch (code) {
    case ResponseCode::USER_SIGNED:
        // Check for length *shouldnt happen if code works as intended
        expected_payload_size = CLIENT_ID_BSIZE;
        if (client_id.size() != CLIENT_ID_BSIZE || payload_size != expected_payload_size) {
            return false;
        }
        return true;

    case ResponseCode::USERS_LIST:
        // Check for length *shouldnt happen if code works as intended
        expected_payload_size = static_cast<uint32_t>(client_name_list.size() * (CLIENT_ID_BSIZE + NAME_BSIZE));
        if (payload_size != expected_payload_size) {
            return false;
        }
        for (const auto& pair : client_name_list) {
            if (get<0>(pair).size() != CLIENT_ID_BSIZE || get<1>(pair).size() != NAME_BSIZE) {
                return false;
            }

            // Get the name vector as a copy
            vector<uint8_t> name = get<1>(pair);
            bool end_char = false;

            // Check each character using range-based for loop
            for (uint8_t c : name) {
                // Check if character is valid ASCII
                if (c > 127) {
                    return false;
                }
                if (c == '\0') {
                    end_char = true;
                    break;
                }
            }

            // If no null terminator was found, return false
            if (!end_char) {
                return false;
            }
        }

        return true;

    case ResponseCode::RETRIEVED_PUBLIC_KEY:
        expected_payload_size = CLIENT_ID_BSIZE + PUBLIC_KEY_BSIZE;
        if (other_client_id.size() != CLIENT_ID_BSIZE || public_key.size() != PUBLIC_KEY_BSIZE ||
            payload_size != expected_payload_size) {
            return false;
        }
        return true;

    case ResponseCode::MESSAGE_SENT:
        expected_payload_size = CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE;
        if (other_client_id.size() != CLIENT_ID_BSIZE || payload_size != expected_payload_size) {
            return false;
        }
        return true;

    case ResponseCode::RETRIEVED_MESSAGES:
        expected_payload_size = 0;
        for (const auto& message : messages_list) {
            if (get<0>(message).size() != CLIENT_ID_BSIZE) {
                return false;
            }

            // Check message type is a valid MessageType value
            uint8_t msg_type = get<2>(message);
            switch (static_cast<MessageType>(msg_type)) {
            case MessageType::SYM_KEY_REQUEST:
            case MessageType::SYM_KEY_RESPONSE:
            case MessageType::TEXT_MESSAGE:
                break;
            case MessageType::DEFAULT:
            default:
                return false;  // Invalid message type
            }

            // Add sizes: client_id + message_id + message_type + content_size + content
            expected_payload_size += CLIENT_ID_BSIZE + MESSAGE_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE +
                static_cast<uint32_t>(get<3>(message).size());
        }
        if (payload_size != expected_payload_size) {
            return false;
        }
        return true;

    case ResponseCode::ERROR_MESSAGE:
        expected_payload_size = 0;
        if (payload_size != expected_payload_size) {
            return false;
        }
        return true;

    default:
        return false;
    }
}

// Stream output for vector<uint8_t> for printing a vector
ostream& operator<<(ostream& os, const vector<uint8_t>& data) {
    for (auto byte : data) {
        os << hex << setw(2) << setfill('0') << static_cast<int>(byte);
    }
    return os;
}