#ifndef KEYS_MAP_H
#define KEYS_MAP_H

#include <map>
#include <vector>

#include "Protocol.h"

class KeysMap {
private:
    std::map<std::vector<uint8_t>, std::vector<uint8_t>> keys_map;  // client_id -> key

public:
    KeysMap() = default;

    void insert(const std::vector<uint8_t>& client_id, const std::vector<uint8_t>& key);

    std::vector<uint8_t> get_key(const std::vector<uint8_t>& client_id) const;
    bool has_client_id(const std::vector<uint8_t>& client_id) const;
};

#endif  // KEYS_MAP_H