#ifndef CLIENT_H
#define CLIENT_H

#include <boost/asio.hpp>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "AESWrapper.h"
#include "Base64Wrapper.h"
#include "KeysMap.h"
#include "Protocol.h"
#include "RSAWrapper.h"
#include "UsersMap.h"

// Client class for server communication
class Client {
public:
    // Menu options for client actions
    enum MenuOption {
        REGISTER = 110,
        REQUEST_CLIENTS_LIST = 120,
        REQUEST_PUBLIC_KEY = 130,
        REQUEST_WAITING_MESSAGES = 140,
        SEND_TEXT_MESSAGE = 150,
        REQUEST_SYMMETRIC_KEY = 151,
        SEND_SYMMETRIC_KEY = 152,
        EXIT_CLIENT = 0,
        INVALID_OPTION = -1
    };

    // Constructor
    Client();

    // Core methods
    void connect();
    void start();
    void disconnect();

    void sendRequest(const Request& request);
    Response receiveResponse();

private:
    // User interaction
    void print_welcome_message() const;
    MenuOption get_user_choice() const;

    bool is_valid_name(const vector<uint8_t>& name) const;
    vector<uint8_t> get_user_name() const;
    string get_user_message() const;
    bool response_handler(const Response& response);
    bool choice_handler(Request& request, MenuOption choice);
    bool read_server_info(string& ip, string& port);
    bool is_valid_option(int choice) const;
    bool load_client_info();
    bool save_client_info() const;
    bool isSigned() const { return _client_signed; }

    // Encryption
    vector<uint8_t> generate_symmetric_key();
    vector<uint8_t> sym_encrypt_message(const string& message, vector<uint8_t>& key) const;
    string sym_decrypt_message(const vector<uint8_t>& message, vector<uint8_t>& key) const;
    vector<uint8_t> asm_encrypt_message(const vector<uint8_t>& message, const string& public_key) const;
    vector<uint8_t> asm_decrypt_message(const vector<uint8_t>& message, const string& private_key) const;

    // Constants
    static const size_t HEADER_SIZE_BSIZE = 7;
    static const size_t PAYLOAD_SIZE_BSIZE = 4;
    static const size_t PRIVATE_KEY_BSIZE = 358;
    const string MY_INFO_NAME = "my.info";
    const string SERVER_INFO_NAME = "server.info";

    // Client data variables
    vector<uint8_t> _name;
    vector<uint8_t> _client_id;
    string _private_key;
    string _public_key;

    bool _client_signed;

    // Client DB
    UsersMap _users_map;
    KeysMap _symkey_map;
    KeysMap _pubkey_map;

    // Network variables
    boost::asio::io_context io_context_;
    boost::asio::ip::tcp::socket socket_;
    boost::asio::ip::tcp::resolver resolver_;
    boost::asio::ip::tcp::resolver::results_type endpoints_;
};

// Main function for Client
int client_main();

#endif  // CLIENT_H