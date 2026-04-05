# MessageU Client (C++)

A C++ client for the MessageU secure messaging application.

## Dependencies

- **Boost.Asio** - TCP networking
- **Boost.Endian** - Byte order conversion
- **Crypto++** - Cryptography (AES, RSA, Base64)

## Build

### Prerequisites

Install the required libraries:

**Ubuntu/Debian:**
```bash
sudo apt-get install libboost-all-dev libcrypto++
```

**Windows:**
- Install Boost libraries (https://www.boost.org/)
- Install Crypto++ (https://www.cryptopp.com/)

### Compile

```bash
g++ -std=c++17 -o client *.cpp -lboost_system -lboost_thread -lcryptopp
```

## Configuration

Edit `my.info` to configure the client:
- Username
- RSA keys location

Edit `server.info` to set the server address:
- IP address
- Port number

## Usage

```bash
./client
```
