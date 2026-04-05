#include "Client.h"

using namespace std;
using boost::asio::ip::tcp;

// Constructor: Reads server info from file and initializes the client
Client::Client() : socket_(io_context_), resolver_(io_context_) {
    string ip;
    string port;
    if (!read_server_info(ip, port)) {
        throw exception("Failed to read server info.\n");
    }

    try {
        // Resolve the server address and store endpoints
        endpoints_ = resolver_.resolve(ip, port);
    }
    catch (const exception&) {
        throw exception("Failed to resolve server address.\n");
    }
}

// Establishes a connection to the server.
void Client::connect() {
    try {
        // Connects the socket to the resolved server endpoints
        boost::asio::connect(socket_, endpoints_);
    }
    catch (const exception&) {
        throw exception("Failed to connect to server.\n");
    }
}

// Sends a request to the server.
void Client::sendRequest(const Request& request) {
    try {
        // Serialize the request into a byte vector
        vector<uint8_t> serialized_request = request.serialize();
        // Send the serialized request over the socket
        boost::asio::write(socket_, boost::asio::buffer(serialized_request));
    }
    catch (const exception&) {
        throw exception("Failed to send request.\n");
    }
}

// Receives a response from the server.
Response Client::receiveResponse() {
    try {
        // Read the response header (fixed size)
        vector<uint8_t> header(HEADER_SIZE_BSIZE);
        socket_.read_some(boost::asio::buffer(header));

        // Extract the payload size from the header (last PAYLOAD_SIZE_BSIZE bytes)
        uint32_t payload_size;
        memcpy(&payload_size, &header[HEADER_SIZE_BSIZE - PAYLOAD_SIZE_BSIZE], PAYLOAD_SIZE_BSIZE);
        payload_size = boost::endian::little_to_native(payload_size);

        // Read the payload based on the extracted size
        vector<uint8_t> payload(payload_size);
        socket_.read_some(boost::asio::buffer(payload));

        // Concatenate header and payload into a single response vector
        vector<uint8_t> response = header;
        response.insert(response.end(), payload.begin(), payload.end());

        // Deserialize the response into a Response object
        Response des_response(response);
        return des_response;
    }
    catch (const exception&) {
        throw exception("Failed to receive response.\n");
    }
}

// Disconnects from the server.
void Client::disconnect() {
    try {
        // Closes the socket connection
        socket_.close();
    }
    catch (const exception&) {
        throw exception("Failed to disconnect.\n");
    }
}

// Prints the client menu.
void Client::print_welcome_message() const {
    cout << "\nMessageU client at your service.\n\n";
    cout << "110) Register\n";
    cout << "120) Request for clients list\n";
    cout << "130) Request for public key\n";
    cout << "140) Request for waiting messages\n";
    cout << "150) Send a text message\n";
    cout << "151) Send a request for symmetric key\n";
    cout << "152) Send your symmetric key\n";
    cout << " 0) Exit client\n";
}

// Gets and validates user choice.
Client::MenuOption Client::get_user_choice() const {
    string choice;
    int numeric_choice;
    getline(cin, choice);

    // Convert the string into an integer
    try {
        numeric_choice = stoi(choice);
    }
    catch (const exception&) {
        return INVALID_OPTION;
    }
    // validate the choice
    if (!is_valid_option(numeric_choice)) {
        return INVALID_OPTION;
    }
    return static_cast<MenuOption>(numeric_choice);
}

// Checks if the selected menu option is valid.
bool Client::is_valid_option(int choice) const {
    return choice == REGISTER || choice == REQUEST_CLIENTS_LIST || choice == REQUEST_PUBLIC_KEY || choice == REQUEST_WAITING_MESSAGES ||
        choice == SEND_TEXT_MESSAGE || choice == REQUEST_SYMMETRIC_KEY || choice == SEND_SYMMETRIC_KEY || choice == EXIT_CLIENT;
}

// Checks if the selected menu option is name.
bool Client::is_valid_name(const vector<uint8_t>& name) const {
    // Validate name size
    if (name.size() > NAME_BSIZE) {
        cout << "Name is too long!\n";
        return false;
    }
    // Check if all characters are ASCII (0-127)
    for (uint8_t c : name) {
        if (c > 127) {
            cout << "Invalid input: Only ASCII characters are allowed!\n";
            return false;
        }
    }
    return true;
}

// Reads server IP and port from server.info file.
bool Client::read_server_info(string& ip, string& port) {
    ifstream file(SERVER_INFO_NAME);
    if (!file) {
        return false;
    }

    // Reads the first line from the file
    string server_info;
    getline(file, server_info);
    file.close();

    // Check if ':' exists and find its possition
    size_t delimiter_pos = server_info.find(':');
    if (delimiter_pos == string::npos) {
        return false;
    }

    // Save the ip and port
    ip = server_info.substr(0, delimiter_pos);
    port = server_info.substr(delimiter_pos + 1);

    return true;
}

// Function to get user name from user
vector<uint8_t> Client::get_user_name() const {
    cout << "Enter user name: ";

    string input_name;
    getline(cin, input_name);

    // Convert string into vector of uint8_t
    vector<uint8_t> name = vector<uint8_t>(input_name.begin(), input_name.end());
    name.push_back('\0');

    return name;
}
// Function to get user message from user
string Client::get_user_message() const {
    cout << "Enter message: \n";
    string input_message;
    getline(cin, input_message);

    return input_message;
}

// Handles server's response
bool Client::response_handler(const Response& response) {
    switch (response.getCode()) {
    case ResponseCode::USER_SIGNED: {
        this->_client_id = response.getClientId();
        
        // Save client information
        if (save_client_info()) this->_client_signed = true;

        cout << "Registered successfully" << '\n';
        return true;
    }
    case ResponseCode::USERS_LIST: {
        // Creates a new users map and prints it
        this->_users_map = UsersMap(response.getClientNameList());
        cout << _users_map;
        return true;
    }
    case ResponseCode::RETRIEVED_PUBLIC_KEY: {
        // Saves the requested Public Key
        this->_pubkey_map.insert(response.getOtherClientId(), response.getPublicKey());
        cout << "Public Key retrieved successfully. \n";
        return true;
    }
    case ResponseCode::MESSAGE_SENT: {
        cout << "Message sent successfully" << '\n';
        return true;
    }
    case ResponseCode::RETRIEVED_MESSAGES: {
        // Parse Messages List and prints it
        cout << "Retrieved messages:\n";
        for (const auto& message : response.getMessagesList()) {
            vector<uint8_t> client_id = get<0>(message);
            uint32_t message_id = get<1>(message);
            MessageType message_type = static_cast<MessageType>(get<2>(message));
            vector<uint8_t> content = get<3>(message);
            vector<uint8_t> name = this->_users_map.get_name(client_id);
            cout << "From: <" << string(name.begin(), name.end()) << ">\nContent:\n";
            switch (message_type) {
            case MessageType::SYM_KEY_REQUEST: {
                cout << "Request for symmetric key\n";
                break;
            }
            case MessageType::SYM_KEY_RESPONSE: {
                vector<uint8_t> key = asm_decrypt_message(content, _private_key);
                this->_symkey_map.insert(client_id, key);
                cout << "Symmetric key received\n";
                break;
            }
            case MessageType::TEXT_MESSAGE: {
                if (!_symkey_map.has_client_id(client_id)) {
                    cout << "can’t decrypt message\n";
                    break;
                }
                try {
                    vector<uint8_t> symkey = _symkey_map.get_key(client_id);
                    string message_content = sym_decrypt_message(content, symkey);
                    cout << message_content << '\n';
                }
                catch (const exception&) {
                    cout << "can’t decrypt message\n";
                }

                break;
            }
            case MessageType::DEFAULT: {
                break;
            }
            }
            cout << "-----<EOM>-----\n\n";
        }
        return true;
    }

    case ResponseCode::ERROR_MESSAGE: {
        // Print Error message
        cout << "server responded with an error\n";
        return true;
    }

    case ResponseCode::DEFAULT: {
        // We shouldnt get here but just in case
        cout << "Server responded with invalid response\n";
        return false;
    }
    }
    return true;
}

// Handles clients's choice
bool Client::choice_handler(Request& request, Client::MenuOption choice) {
    vector<uint8_t> client_id = { 0 };
    vector<uint8_t> name;
    vector<uint8_t> public_key;
    vector<uint8_t> other_client_id;
    vector<uint8_t> message_content;

    switch (choice) {
    case Client::REGISTER: {
        // Checks if clients is Signed
        if (isSigned()) {
            system("cls");
            cout << "You are already signed with the name: " << string(_name.begin(), _name.end()) << '\n';
            return false;
        }
        // Choose a name and validate
        name = get_user_name();
        while (!is_valid_name(name)) name = get_user_name();

        this->_name = name;
        // Convert public key to a vector
        public_key = vector<uint8_t>(_public_key.begin(), _public_key.end());

        // Creates a request
        request = Request(client_id, RequestCode::SIGN_USER, name, public_key);
        cout << "Requested registration with name: " << string(name.begin(), name.end()) << '\n';
        return true;
    }

    case Client::REQUEST_CLIENTS_LIST: {
        // Creates a request
        client_id = this->_client_id;
        request = Request(client_id, RequestCode::LIST_USERS);
        cout << "Requested clients list\n";
        return true;
    }

    case Client::REQUEST_PUBLIC_KEY: {
        client_id = this->_client_id;
        // Get Username from user and checks if it exists in _users_map
        name = get_user_name();
        if (_users_map.has_name(name))
            // Get client_id of name
            other_client_id = _users_map.get_client_id(name);
        else {
            system("cls");
            cout << string(name.begin(), name.end()) << " Was not found in clients list\n";
            cout << "Please request clients list\n";
            return false;
        }
        cout << "Requested public key for name: " << string(name.begin(), name.end()) << '\n';
        // Creates a request
        request = Request(client_id, RequestCode::GET_PUBLIC_KEY, other_client_id);
        return true;
    }

    case Client::REQUEST_WAITING_MESSAGES:
        // Creates a request
        client_id = this->_client_id;
        cout << "Requested waiting messages\n";
        request = Request(client_id, RequestCode::GET_MESSAGES);
        return true;

    case Client::SEND_TEXT_MESSAGE: {
        name = this->_name;
        client_id = this->_client_id;
        // Get Username from user and checks if it exists in _users_map
        name = get_user_name();
        if (_users_map.has_name(name))
            other_client_id = _users_map.get_client_id(name);
        else {
            system("cls");
            cout << string(name.begin(), name.end()) << " Was not found in clients list\n";
            cout << "Please request clients list\n";
            return false;
        }
        // Checks if the was exchanges key for the user
        if (!_symkey_map.has_client_id(other_client_id)) {
            system("cls");
            cout << "Need to request a symmetric key\n";
            return false;
        }
        // Get a message from the user and encrypt it
        vector<uint8_t> symkey = _symkey_map.get_key(other_client_id);
        string message = get_user_message();
        message_content = sym_encrypt_message(message, symkey);
        
        cout << "Sent a Message to " << string(name.begin(), name.end()) << '\n';
        // Creates a request
        request = Request(client_id, RequestCode::SEND_MESSAGE, other_client_id, MessageType::TEXT_MESSAGE, message_content);
        return true;
    }

    case Client::REQUEST_SYMMETRIC_KEY: {
        client_id = this->_client_id;
        // Get Username from user and checks if it exists in _users_map
        name = get_user_name();
        if (_users_map.has_name(name))
            other_client_id = _users_map.get_client_id(name);
        else {
            system("cls");
            cout << string(name.begin(), name.end()) << " Was not found in clients list\n";
            cout << "Please request clients list\n";
            return false;
        }

        if (_symkey_map.has_client_id(other_client_id)) {
            system("cls");
            cout << "Public key for " << string(name.begin(), name.end()) << " already exists\n";
            return false;
        }
        // Creates a request
        message_content.clear();
        cout << "Requested symmetric key from " << string(name.begin(), name.end()) << '\n';
        request = Request(client_id, RequestCode::SEND_MESSAGE, other_client_id, MessageType::SYM_KEY_REQUEST, message_content);
        return true;
    }

    case Client::SEND_SYMMETRIC_KEY: {
        client_id = this->_client_id;
        // Get Username from user and checks if it exists in _users_map
        name = get_user_name();
        if (!_users_map.has_name(name)) {
            system("cls");
            cout << string(name.begin(), name.end()) << " Was not found in clients list\n";
            cout << "Please request clients list\n";
            return false;
        }
        // Get user info
        other_client_id = _users_map.get_client_id(name);

        if (!_pubkey_map.has_client_id(other_client_id)) {
            system("cls");
            cout << "Need to request public key\n";
            return false;
        }
        // Generate key
        vector<uint8_t> sym_key = generate_symmetric_key();
        vector<uint8_t> recipient_pub_key = _pubkey_map.get_key(other_client_id);
        string pub_key = string(recipient_pub_key.begin(), recipient_pub_key.end());

        message_content = asm_encrypt_message(sym_key, pub_key);
        _symkey_map.insert(other_client_id, sym_key);
        cout << "Sent symmetric key to " << string(name.begin(), name.end()) << '\n';
        // Get Username from user and checks if it exists in _users_map
        request = Request(client_id, RequestCode::SEND_MESSAGE, other_client_id, MessageType::SYM_KEY_RESPONSE, message_content);
        return true;
    }
    }
    return false;
}

// Function to start the clinet
void Client::start() {
    Request request;
    Response response;
    Client::MenuOption choice;
    bool running = true;

    try {
        load_client_info();
        this->_client_signed = true;
        // generate public_key from private_key
        RSAPrivateWrapper rsapriv(Base64Wrapper::decode(_private_key));
        this->_public_key = rsapriv.getPublicKey();
    }
    catch (exception&) {
        cout << "Unable To load my.info\n";
        ofstream file(MY_INFO_NAME, ios::trunc);  // Clear file if existists
        file.close();                             
        this->_client_signed = false;
        this->_name.clear();
        this->_client_id.clear();
        // generate public_key and private_key
        RSAPrivateWrapper rsapriv;
        this->_public_key = rsapriv.getPublicKey();
        this->_private_key = Base64Wrapper::encode(rsapriv.getPrivateKey());
    }

    while (running) {
        // Display menu and get user choice
        print_welcome_message();
        choice = get_user_choice();

        if (choice == Client::EXIT_CLIENT) {
            running = false;
            return;
        }
        if (choice == Client::INVALID_OPTION) {
            system("cls");
            cout << "Invalid Choice\n";
            continue;
        }
        if (!choice_handler(request, choice)) {
            cout << "Invalid Choice\n";
            continue;
        }

        try {
            sendRequest(request);
        }
        catch (exception& e) {
            cout << e.what();
            continue;
        }
        try {
            response = receiveResponse();
        }
        catch (exception& e) {
            cout << e.what();
            continue;
        }
        system("cls"); // clear screen
        if (!response.validate()) {
            cout << "Server responded with invalid response\n";
            continue;
        }
        response_handler(response);
    }
}

// Functions to load Clients info from a file
bool Client::load_client_info() {
    ifstream file(MY_INFO_NAME);
    string temp_str;

    // If file doesn't exist, create an empty one
    if (!file) {
        ofstream create_file(MY_INFO_NAME);
        if (!create_file) {
            throw exception("Error: Unable to create file 'my.info'\n");
        }
        create_file.close();
        throw exception("Error: Unable to close file 'my.info'\n");
    }

    // Check if file is open and readable
    if (!file.is_open()) {
        throw exception("Error: Unable to read 'my.info'\n");
    }

    // Read and validate name
    if (!getline(file, temp_str)) {
        file.close();
        throw exception("Error: with my.info name\n");
    }
    vector<uint8_t> name(temp_str.begin(), temp_str.end());
    name.push_back('\0');

    if (name.size() >= NAME_BSIZE) {
        file.close();
        throw exception("Error: with my.info name\n");
    }
    if (name.empty()) {
        cout << "Error: with my.info name\n";
        file.close();
        throw exception("Error: with my.info name\n");
    }
    this->_name = name;

    // Read and validate client_id
    if (!getline(file, temp_str)) {
        file.close();
        throw exception("Error: with my.info client_id\n");
    }

    vector<uint8_t> client_id = {};
    for (size_t i = 0; i < temp_str.length(); i += 2) {
        string byteStr = temp_str.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(stoi(byteStr, nullptr, 16));
        client_id.push_back(byte);
    }

    this->_client_id = client_id;

    if (_client_id.size() != CLIENT_ID_BSIZE) {
        file.close();
        throw exception("Error: with my.info client_id\n");
    }

    // Read private_key (multi-line)
    string private_key_content;
    while (getline(file, temp_str) && !temp_str.empty()) {
        private_key_content += temp_str + '\n';
    }

    this->_private_key = private_key_content;

    // Check for unexpected additional content
    if (getline(file, temp_str) && !temp_str.empty()) {
        file.close();
        throw exception("ERROR: Extra content found in 'my.info' after expected data\n");
    }

    file.close();
    return true;
}
// Functions to save Clients info to a file
bool Client::save_client_info() const {
    // Open file for writing (this will overwrite existing content)
    ofstream out_file("my.info");
    if (!out_file) {
        cout << "Error: Unable save client info to 'my.info'\n";
        return false;
    }

    // Write client info with newlines

    out_file << string(_name.begin(), _name.end() - 1) << '\n'; // exclude '\0'
    out_file << _client_id << '\n';
    out_file << _private_key;

    // Check if writing was successful
    if (!out_file) {
        cout << "Error: Unable save client info to 'my.info'\n";
        out_file.close();
        return false;
    }

    out_file.close();
    return true;
}

// Helper Function to encrypt message with asymmetric key
vector<uint8_t> Client::asm_encrypt_message(const vector<uint8_t>& message, const string& public_key) const {
    RSAPublicWrapper rsapub(public_key);
    string str_message = string(message.begin(), message.end());
    string cipher = rsapub.encrypt(str_message);
    return vector<uint8_t>(cipher.begin(), cipher.end());
}
// Helper Function to decrypt message with asymmetric key
vector<uint8_t> Client::asm_decrypt_message(const vector<uint8_t>& message, const string& private_key) const {
    RSAPrivateWrapper rsapriv(Base64Wrapper::decode(private_key));
    string cipher = string(message.begin(), message.end());
    string decrypted_message = rsapriv.decrypt(cipher);
    return vector<uint8_t>(decrypted_message.begin(), decrypted_message.end());
}

// Helper Function generate symmetric key
vector<uint8_t> Client::generate_symmetric_key() {
    unsigned char key[AESWrapper::DEFAULT_KEYLENGTH] = { 0 };
    AESWrapper aes(AESWrapper::GenerateKey(key, AESWrapper::DEFAULT_KEYLENGTH), AESWrapper::DEFAULT_KEYLENGTH);
    vector<uint8_t> symkey(key, key + AESWrapper::DEFAULT_KEYLENGTH);
    return symkey;
}

// Helper Function to encrypt message with symmetric key
vector<uint8_t> Client::sym_encrypt_message(const string& message, vector<uint8_t>& sym_key) const {
    unsigned char key[AESWrapper::DEFAULT_KEYLENGTH] = { 0 };
    memcpy(key, sym_key.data(), min(sym_key.size(), AESWrapper::DEFAULT_KEYLENGTH));
    AESWrapper aes(key, AESWrapper::DEFAULT_KEYLENGTH);
    string cipher = aes.encrypt(message.c_str(), message.length());
    vector<uint8_t> encrypted_message = vector<uint8_t>(cipher.begin(), cipher.end());
    return encrypted_message;
}
// Helper Function to decrypt message with symmetric key
string Client::sym_decrypt_message(const vector<uint8_t>& message, vector<uint8_t>& sym_key) const {
    unsigned char key[AESWrapper::DEFAULT_KEYLENGTH] = { 0 };
    memcpy(key, sym_key.data(), min(sym_key.size(), AESWrapper::DEFAULT_KEYLENGTH));
    AESWrapper aes(key, AESWrapper::DEFAULT_KEYLENGTH);
    string cipher = string(message.begin(), message.end());
    string decrypted_message = aes.decrypt(cipher.c_str(), cipher.length());
    return decrypted_message;
}

// Main to start clinet
int client_main() {
    try {
        Client client;

        client.connect();
        cout << "Successfully connected to the server\n";

        client.start();

        client.disconnect();
        cout << "Disconnected from server\n";

    }
    catch (const exception& e) {
        cout << "Error: " << e.what() << endl;
        return 0;
    }
    return 0;
}