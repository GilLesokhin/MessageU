// TestClient.h
#ifndef TEST_CLIENT_H
#define TEST_CLIENT_H

#include <boost/asio.hpp>
#include <vector>
#include <string>
#include <cstdint>
#include <iostream>
#include "Protocol.h"  // Your provided Protocol.h
#include "Client.h"

class TestClient {
public:
    TestClient(const std::string& host = "127.0.0.1", int port = 0);
    ~TestClient();
    void connect();
    void disconnect();
    void run();

private:
    std::string host_;
    int port_;
    boost::asio::io_context io_context_;
    boost::asio::ip::tcp::socket socket_;
    std::pair<bool, std::string> validateRequest(const std::vector<uint8_t>& raw_data);

    int getPort(const std::string& filename = "myport.info");
};

#endif // TEST_CLIENT_H