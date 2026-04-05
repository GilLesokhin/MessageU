#include "Client.h"
#include "MockRequest.h"


using namespace std;

// Test function to send and evaluate response
void test_edge_case(Client& client, const string& test_name, const MockRequest& request) {
    try {
        cout << "\nTesting: " << test_name << endl;
        vector<uint8_t> serialized = request.serialize();
        boost::asio::write(client.socket_, boost::asio::buffer(serialized));
        Response response = client.receiveResponse();

        if (response.getCode() == ResponseCode::ERROR_MESSAGE) {
            cout << "[PASS] Server returned error as expected: " << response.getCode() << endl;
        }
        else {
            cout << "[FAIL] Unexpected response code: " << response.getCode() << endl;
        }
    }
    catch (const exception& e) {
        cout << "[PASS] Exception caught as expected: " << e.what() << endl;
    }
}

void run_edge_case_tests() {
    try {
        Client client;
        client.connect();
        cout << "Connected to server successfully" << endl;

        // Valid client ID for reuse
        vector<uint8_t> valid_client_id(16, 1);

        // 1. Empty Request
        test_edge_case(client, "Empty Request", MockRequest({}, 0, 0, 0, {}));

        // 2. Short Header (only client_id)
        test_edge_case(client, "Short Header", MockRequest(valid_client_id, 0, 0, 0, {}));

        // 3. Invalid Version
        {
            vector<uint8_t> payload = { 'T', 'e', 's', 't', 0 };
            test_edge_case(client, "Invalid Version (2)",
                MockRequest(valid_client_id, 2, 600, payload.size(), payload));
        }

        // 4. Unknown Request Code
        {
            vector<uint8_t> payload = { 'T', 'e', 's', 't', 0 };
            test_edge_case(client, "Unknown Request Code (999)",
                MockRequest(valid_client_id, 1, 999, payload.size(), payload));
        }

        // 5a. Payload Size Too Large
        {
            vector<uint8_t> payload = { 'T', 'e', 's', 't', 0 };
            test_edge_case(client, "Payload Size Too Large",
                MockRequest(valid_client_id, 1, 600, 100, payload));
        }

        // 5b. Payload Size Too Small
        {
            vector<uint8_t> payload(100, 'A');
            test_edge_case(client, "Payload Size Too Small",
                MockRequest(valid_client_id, 1, 600, 5, payload));
        }

        // 6. Wrong Client ID Size
        {
            vector<uint8_t> short_client_id(10, 1);
            vector<uint8_t> payload = { 'T', 'e', 's', 't', 0 };
            test_edge_case(client, "Wrong Client ID Size (10 bytes)",
                MockRequest(short_client_id, 1, 600, payload.size(), payload));
        }

        // 7. All-Zero Client ID
        {
            vector<uint8_t> zero_client_id(16, 0);
            vector<uint8_t> payload = { 'T', 'e', 's', 't', 0 };
            test_edge_case(client, "All-Zero Client ID",
                MockRequest(zero_client_id, 1, 600, payload.size(), payload));
        }

        // 8. Empty Name (600)
        {
            vector<uint8_t> payload(415, 0); // Name (255) + PubKey (160), all zeros
            test_edge_case(client, "Empty Name (600)",
                MockRequest(valid_client_id, 1, 600, 415, payload));
        }

        // 9. Oversized Name (600)
        {
            vector<uint8_t> oversized_name(300, 'A');
            oversized_name[299] = 0;
            vector<uint8_t> pubkey(160, 1);
            vector<uint8_t> payload;
            payload.insert(payload.end(), oversized_name.begin(), oversized_name.end());
            payload.insert(payload.end(), pubkey.begin(), pubkey.end());
            test_edge_case(client, "Oversized Name (600)",
                MockRequest(valid_client_id, 1, 600, payload.size(), payload));
        }

        // 10. No Null Terminator in Name (600)
        {
            vector<uint8_t> name(255, 'A'); // No null terminator
            vector<uint8_t> pubkey(160, 1);
            vector<uint8_t> payload;
            payload.insert(payload.end(), name.begin(), name.end());
            payload.insert(payload.end(), pubkey.begin(), pubkey.end());
            test_edge_case(client, "No Null Terminator in Name (600)",
                MockRequest(valid_client_id, 1, 600, 415, payload));
        }

        // 11. Wrong Public Key Size (600)
        {
            vector<uint8_t> name = { 'T', 'e', 's', 't', 0 };
            vector<uint8_t> short_pubkey(100, 1); // < 160 bytes
            vector<uint8_t> payload(255, 0); // Pad name to 255
            copy(name.begin(), name.end(), payload.begin());
            payload.insert(payload.end(), short_pubkey.begin(), short_pubkey.end());
            test_edge_case(client, "Wrong Public Key Size (600)",
                MockRequest(valid_client_id, 1, 600, payload.size(), payload));
        }

        // 12. Empty Public Key (600)
        {
            vector<uint8_t> name = { 'T', 'e', 's', 't', 0 };
            vector<uint8_t> empty_pubkey(160, 0);
            vector<uint8_t> payload(255, 0);
            copy(name.begin(), name.end(), payload.begin());
            payload.insert(payload.end(), empty_pubkey.begin(), empty_pubkey.end());
            test_edge_case(client, "Empty Public Key (600)",
                MockRequest(valid_client_id, 1, 600, 415, payload));
        }

        // 13. Non-Empty Payload (601)
        {
            vector<uint8_t> payload = { 'U', 'n', 'e', 'x', 'p', 'e', 'c', 't', 'e', 'd' };
            test_edge_case(client, "Non-Empty Payload (601)",
                MockRequest(valid_client_id, 1, 601, payload.size(), payload));
        }

        // 14. Wrong Other Client ID Size (602)
        {
            vector<uint8_t> short_other_id(10, 1);
            test_edge_case(client, "Wrong Other Client ID Size (602)",
                MockRequest(valid_client_id, 1, 602, short_other_id.size(), short_other_id));
        }

        // 15. Empty Other Client ID (602)
        {
            vector<uint8_t> zero_other_id(16, 0);
            test_edge_case(client, "Empty Other Client ID (602)",
                MockRequest(valid_client_id, 1, 602, 16, zero_other_id));
        }

        // 16. Wrong Other Client ID Size (603)
        {
            vector<uint8_t> short_other_id(10, 1);
            vector<uint8_t> payload = short_other_id;
            payload.push_back(1); // MessageType
            uint32_t content_size = 5;
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            payload.insert(payload.end(), { 'T', 'e', 's', 't', 0 });
            test_edge_case(client, "Wrong Other Client ID Size (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        // 17. Invalid Message Type (603)
        {
            vector<uint8_t> other_id(16, 1);
            vector<uint8_t> payload = other_id;
            payload.push_back(4); // Invalid MessageType
            uint32_t content_size = 5;
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            payload.insert(payload.end(), { 'T', 'e', 's', 't', 0 });
            test_edge_case(client, "Invalid Message Type (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        // 18a. Content Size Too Large (603)
        {
            vector<uint8_t> other_id(16, 1);
            vector<uint8_t> payload = other_id;
            payload.push_back(3); // Text Message
            uint32_t content_size = 100;
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            payload.insert(payload.end(), { 'T', 'e', 's', 't', 0 }); // Only 5 bytes
            test_edge_case(client, "Content Size Too Large (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        // 18b. Content Size Too Small (603)
        {
            vector<uint8_t> other_id(16, 1);
            vector<uint8_t> payload = other_id;
            payload.push_back(3); // Text Message
            uint32_t content_size = 2;
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            payload.insert(payload.end(), { 'T', 'e', 's', 't', 0 }); // 5 bytes
            test_edge_case(client, "Content Size Too Small (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        // 19. Empty Content (603)
        {
            vector<uint8_t> other_id(16, 1);
            vector<uint8_t> payload = other_id;
            payload.push_back(3); // Text Message
            uint32_t content_size = 0;
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            test_edge_case(client, "Empty Content (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        // 20. Oversized Content (603)
        {
            vector<uint8_t> other_id(16, 1);
            vector<uint8_t> payload = other_id;
            payload.push_back(3); // Text Message
            uint32_t content_size = 1048576; // 1MB
            payload.insert(payload.end(), reinterpret_cast<uint8_t*>(&content_size),
                reinterpret_cast<uint8_t*>(&content_size) + 4);
            vector<uint8_t> large_content(1048576, 'A');
            payload.insert(payload.end(), large_content.begin(), large_content.end());
            test_edge_case(client, "Oversized Content (603)",
                MockRequest(valid_client_id, 1, 603, payload.size(), payload));
        }

        client.disconnect();
        cout << "\nDisconnected from server" << endl;
    }
    catch (const exception& e) {
        cout << "Error: " << e.what() << endl;
    }
}

int test_main() {
    cout << "Running edge case tests with MockRequest...\n" << endl;
    run_edge_case_tests();
    return 0;
}