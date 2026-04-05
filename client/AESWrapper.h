#pragma once

#include <string>

class AESWrapper {
public:
    static const size_t DEFAULT_KEYLENGTH = 16;

private:
    unsigned char _key[DEFAULT_KEYLENGTH];
    AESWrapper(const AESWrapper& aes);

public:
    static unsigned char* GenerateKey(unsigned char* buffer, size_t length);

    AESWrapper();
    AESWrapper(const unsigned char* key, size_t size);
    ~AESWrapper();

    const unsigned char* getKey() const;

    std::string encrypt(const char* plain, size_t length);
    std::string decrypt(const char* cipher, size_t length);
};