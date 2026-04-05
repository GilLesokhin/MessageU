// MockRequest.h
#ifndef MOCK_REQUEST_H
#define MOCK_REQUEST_H

#include <vector>
#include <boost/endian/conversion.hpp>
#include <iostream>
#include <fstream>
#include <vector>
#include <boost/asio.hpp>

int test_main();

class MockRequest {
private:
    std::vector<uint8_t> client_id;
    uint8_t version;
    uint16_t code;
    uint32_t payload_size;
    std::vector<uint8_t> payload;

public:
    MockRequest(const std::vector<uint8_t>& client_id, uint8_t version,
        uint16_t code, uint32_t payload_size, const std::vector<uint8_t>& payload)
        : client_id(client_id), version(version), code(code),
        payload_size(payload_size), payload(payload) {
    }

    std::vector<uint8_t> serialize() const {
        std::vector<uint8_t> request;

        // Client ID (no size validation)
        request.insert(request.end(), client_id.begin(), client_id.end());

        // Version (1 byte)
        request.push_back(version);

        // Code (2 bytes, little-endian)
        uint16_t code_le = boost::endian::native_to_little(code);
        request.insert(request.end(), reinterpret_cast<uint8_t*>(&code_le),
            reinterpret_cast<uint8_t*>(&code_le) + 2);

        // Payload size (4 bytes, little-endian)
        uint32_t payload_size_le = boost::endian::native_to_little(payload_size);
        request.insert(request.end(), reinterpret_cast<uint8_t*>(&payload_size_le),
            reinterpret_cast<uint8_t*>(&payload_size_le) + 4);

        // Payload (no validation)
        request.insert(request.end(), payload.begin(), payload.end());

        return request;
    }
};

#endif // MOCK_REQUEST_H