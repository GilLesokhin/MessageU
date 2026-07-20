# MessageU

A secure messaging application built with a C++ client and Python server.

Built for an Open University Defensive Systems Programming course. The project includes the full client and server implementation.

## Overview

MessageU implements a course-specified binary protocol for client registration, user discovery, key exchange, encrypted messaging, and message retrieval.

## System Design

The C++ client manages the interactive messaging workflow, TCP communication, protocol serialization, and local cryptographic operations. The Python server accepts concurrent connections, validates protocol requests, and manages registered users and queued messages.

Clients use RSA public keys to exchange AES symmetric keys. Text messages are encrypted with AES before delivery through the server.

## Conceptual Message Flow

```mermaid
sequenceDiagram
    participant A as Client A
    participant S as Server
    participant B as Client B

    A->>S: Request symmetric key from B
    S->>B: Forward key request
    B->>B: Generate and store AES key
    B->>S: Encrypt AES key with A's RSA public key
    S->>A: Forward encrypted AES key
    A->>A: Decrypt and store the same AES key

    Note over A,B: Both clients now share one AES key

    A->>S: Encrypt message with shared AES key
    S->>B: Forward encrypted message
    B->>S: Encrypt reply with shared AES key
    S->>A: Forward encrypted reply
```

## Concurrent Server Handling

The Python server handles each TCP connection in a dedicated thread. Shared user and message data is protected with a lock, allowing multiple clients to interact with the server concurrently.

## Technical Highlights

- C++ client using Boost.Asio for TCP communication.
- Python server handling concurrent client connections.
- RSA public-key cryptography for key exchange.
- AES encryption for message content.
- Custom binary protocol implemented on both client and server.
- Thread-safe in-memory storage for registered users and queued messages.

## Architecture

| Component | Responsibility |
| --- | --- |
| `client/Client.cpp` | Client workflow, networking, and user interaction |
| `client/Protocol.cpp` | Binary request serialization and response parsing |
| `client/AESWrapper.cpp` | AES encryption and decryption |
| `client/RSAWrapper.cpp` | RSA key generation, encryption, and decryption |
| `server/Server.py` | TCP server and request handling |
| `server/Protocol.py` | Protocol parsing, validation, and response serialization |
| `server/DataBase.py` | Thread-safe user and message storage |

## Dependencies

- C++17
- Boost
- Crypto++
- Python 3.10+
