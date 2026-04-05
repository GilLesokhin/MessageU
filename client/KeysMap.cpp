#include "KeysMap.h"

using namespace std;

// Adds a client ID and key pair to the map
void KeysMap::insert(const vector<uint8_t>& client_id, const vector<uint8_t>& key) {
    keys_map[client_id] = key;
}

// Looks up and returns the key for a given client ID
vector<uint8_t> KeysMap::get_key(const vector<uint8_t>& client_id) const {
    auto it = keys_map.find(client_id);
    if (it != keys_map.end()) {
        return it->second;
    }
    return vector<uint8_t>();
}

// Checks if a client ID exists in the map
bool KeysMap::has_client_id(const vector<uint8_t>& client_id) const {
    return keys_map.find(client_id) != keys_map.end();
}