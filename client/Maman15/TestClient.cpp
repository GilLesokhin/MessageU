#include "TestClient.h"
#include <fstream>
#include <algorithm>
#include <iomanip>
#include <array>

using namespace std;
using boost::asio::ip::tcp;

const int DEFAULT_PORT = 1234;
const size_t DATA_MAX_SIZE = 1024;

TestClient::TestClient(const string& host, int port)
    : host_(host), port_(port ? port : getPort()), socket_(io_context_) {
}

TestClient::~TestClient() {
    disconnect();
}

int TestClient::getPort(const string& filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        cout << "Warning: Port file '" << filename << "' not found. Using default port: " << DEFAULT_PORT << endl;
        return DEFAULT_PORT;
    }
    string port_str;
    getline(file, port_str);
    try {
        int port = stoi(port_str);
        if (port < 1 || port > 65535) {
            cout << "Warning: Port " << port << " out of range. Using default: " << DEFAULT_PORT << endl;
            return DEFAULT_PORT;
        }
        return port;
    }
    catch (const exception&) {
        cout << "Warning: Invalid port in file. Using default: " << DEFAULT_PORT << endl;
        return DEFAULT_PORT;
    }
}

void TestClient::connect() {
    tcp::resolver resolver(io_context_);
    auto endpoints = resolver.resolve(host_, to_string(port_));
    boost::asio::connect(socket_, endpoints);
    cout << "Connected to server at " << host_ << ":" << port_ << endl;
}

void TestClient::disconnect() {
    if (socket_.is_open()) {
        socket_.close();
        cout << "Disconnected from server" << endl;
    }
}

pair<bool, string> TestClient::validateRequest(const vector<uint8_t>& raw_data) {
    size_t offset = 0;
    const size_t min_length =   + VERSION_BSIZE + CODE_BSIZE + PAYLOAD_SIZE_BSIZE;

    if (raw_data.size() < min_length) {
        return { false, "Data too short: " + to_string(raw_data.size()) + " bytes (expected at least " + to_string(min_length) + ")" };
    }

    vector<uint8_t> client_id(raw_data.begin() + offset, raw_data.begin() + offset + CLIENT_ID_BSIZE);
    offset += CLIENT_ID_BSIZE;
    if (client_id.size() != CLIENT_ID_BSIZE) {
        return { false, "Client ID length incorrect: " + to_string(client_id.size()) + " bytes (expected " + to_string(CLIENT_ID_BSIZE) + ")" };
    }

    uint8_t version = boost::endian::little_to_native(raw_data[offset]);
    offset += VERSION_BSIZE;
    if (version != VERSION) {
        return { false, "Invalid version: " + to_string(version) + " (expected " + to_string(VERSION) + ")" };
    }

    uint16_t code_value = boost::endian::little_to_native(*reinterpret_cast<const uint16_t*>(&raw_data[offset]));
    offset += CODE_BSIZE;
    bool valid_code = false;
    array<RequestCode, 6> valid_codes = { RequestCode::SIGN_USER, RequestCode::LIST_USERS, RequestCode::GET_PUBLIC_KEY,
                                         RequestCode::SEND_MESSAGE, RequestCode::GET_MESSAGES, RequestCode::DEFAULT };
    for (RequestCode rc : valid_codes) {
        if (static_cast<uint16_t>(rc) == code_value) {
            valid_code = true;
            break;
        }
    }
    if (!valid_code) {
        return { false, "Invalid request code: " + to_string(code_value) + " (not a valid RequestCode)" };
    }
    RequestCode code = static_cast<RequestCode>(code_value);

    uint32_t payload_size = boost::endian::little_to_native(*reinterpret_cast<const uint32_t*>(&raw_data[offset]));
    offset += PAYLOAD_SIZE_BSIZE;
    size_t remaining_data = raw_data.size() - offset;
    if (payload_size != remaining_data) {
        return { false, "Payload size mismatch: " + to_string(payload_size) + " (actual remaining: " + to_string(remaining_data) + ")" };
    }

    switch (code) {
    case RequestCode::SIGN_USER: {
        uint32_t expected_size = NAME_BSIZE + PUBLIC_KEY_BSIZE;
        if (remaining_data != expected_size) {
            return { false, "Payload size incorrect for SIGN_USER: " + to_string(remaining_data) + " (expected " + to_string(expected_size) + ")" };
        }

        vector<uint8_t> name(raw_data.begin() + offset, raw_data.begin() + offset + NAME_BSIZE);
        offset += NAME_BSIZE;
        auto null_pos = find(name.begin(), name.end(), '\0');
        if (null_pos == name.end()) {
            return { false, "Name missing null terminator" };
        }
        vector<uint8_t> name_str(name.begin(), null_pos);
        if (name_str.empty()) {
            return { false, "Name is empty before null terminator" };
        }
        if (!all_of(name_str.begin(), name_str.end(), [](uint8_t c) { return c < 128; })) {
            return { false, "Name contains non-ASCII characters" };
        }

        vector<uint8_t> public_key(raw_data.begin() + offset, raw_data.begin() + offset + PUBLIC_KEY_BSIZE);
        if (public_key.size() != PUBLIC_KEY_BSIZE) {
            return { false, "Public key length incorrect: " + to_string(public_key.size()) + " (expected " + to_string(PUBLIC_KEY_BSIZE) + ")" };
        }
        break;
    }
    case RequestCode::LIST_USERS:
    case RequestCode::GET_MESSAGES:
        if (payload_size != 0) {
            return { false, string("Request ") + to_string(static_cast<uint16_t>(code)) + " should have no payload, got " + to_string(payload_size) + " bytes" };
        }
        break;
    case RequestCode::GET_PUBLIC_KEY: {
        uint32_t expected_size = CLIENT_ID_BSIZE;
        if (remaining_data != expected_size) {
            return { false, "Payload size incorrect for GET_PUBLIC_KEY: " + to_string(remaining_data) + " (expected " + to_string(expected_size) + ")" };
        }
        vector<uint8_t> other_client_id(raw_data.begin() + offset, raw_data.begin() + offset + CLIENT_ID_BSIZE);
        if (other_client_id.size() != CLIENT_ID_BSIZE) {
            return { false, "Other client ID length incorrect: " + to_string(other_client_id.size()) + " (expected " + to_string(CLIENT_ID_BSIZE) + ")" };
        }
        break;
    }
    case RequestCode::SEND_MESSAGE: {
        uint32_t min_size = CLIENT_ID_BSIZE + MESSAGE_TYPE_BSIZE + MESSAGE_SIZE_BSIZE;
        if (remaining_data < min_size) {
            return { false, "Insufficient data for SEND_MESSAGE: " + to_string(remaining_data) + " bytes (expected at least " + to_string(min_size) + ")" };
        }

        vector<uint8_t> other_client_id(raw_data.begin() + offset, raw_data.begin() + offset + CLIENT_ID_BSIZE);
        offset += CLIENT_ID_BSIZE;
        if (other_client_id.size() != CLIENT_ID_BSIZE) {
            return { false, "Other client ID length incorrect: " + to_string(other_client_id.size()) + " (expected " + to_string(CLIENT_ID_BSIZE) + ")" };
        }

        uint8_t message_type_value = boost::endian::little_to_native(raw_data[offset]);
        offset += MESSAGE_TYPE_BSIZE;
        bool valid_mt = false;
        array<MessageType, 4> valid_types = { MessageType::SYM_KEY_REQUEST, MessageType::SYM_KEY_RESPONSE,
                                             MessageType::TEXT_MESSAGE, MessageType::DEFAULT };
        for (MessageType mt : valid_types) {
            if (static_cast<uint8_t>(mt) == message_type_value) {
                valid_mt = true;
                break;
            }
        }
        if (!valid_mt) {
            return { false, "Invalid message type: " + to_string(message_type_value) };
        }

        uint32_t content_size = boost::endian::little_to_native(*reinterpret_cast<const uint32_t*>(&raw_data[offset]));
        offset += MESSAGE_SIZE_BSIZE;
        uint32_t expected_size = min_size + content_size;
        if (remaining_data != expected_size) {
            return { false, "Payload size incorrect for SEND_MESSAGE: " + to_string(remaining_data) + " (expected " + to_string(expected_size) + ")" };
        }
        if (offset + content_size > raw_data.size()) {
            return { false, "Content size exceeds available data: " + to_string(content_size) + " (remaining: " + to_string(raw_data.size() - offset) + ")" };
        }
        break;
    }
    case RequestCode::DEFAULT:
        if (payload_size != 0) {
            return { false, "Default request should have no payload, got " + to_string(payload_size) + " bytes" };
        }
        break;
    default:
        return { false, "Unhandled request code: " + to_string(code_value) };
    }

    return { true, "Request is valid" };
}


void start_test() {

}

void TestClient::run() {
    Response response;
    Client::MenuOption choice;
    try {
        connect();
        while (true) {
            vector<uint8_t> buffer(DATA_MAX_SIZE);
            boost::system::error_code error;
            size_t length = socket_.read_some(boost::asio::buffer(buffer), error);

            if (error == boost::asio::error::eof || error == boost::asio::error::connection_reset) {
                cout << "Server closed connection" << endl;
                break;
            }
            else if (error) {
                throw boost::system::system_error(error);
            }

            buffer.resize(length);
            cout << "\nReceived request (hex): ";
            for (uint8_t byte : buffer) {
                cout << hex << setw(2) << setfill('0') << static_cast<int>(byte);
            }
            cout << dec << endl;


            try
            {
                response = Response(buffer);

                if (!response.validate()) {
                    cout << "[INVALID]. invalid response\n";
                }
                else cout << "[VALID]. Was not filtered!!!!\n";
            }
            catch (const exception&)
            {
                cout << "[INVALID]. invalid response\n";
            }
        }
    }
    catch (const exception& e) {
        cout << "Error: " << e.what() << endl;
    }
    disconnect();
}

int test_client() {
    cout << "Starting Test Client..." << endl;
    TestClient client;
    client.run();
    return 0;
}