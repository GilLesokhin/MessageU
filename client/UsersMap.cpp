#include "UsersMap.h"

using namespace std;

// Builds a map from a list of user ID and name pairs
UsersMap::UsersMap(const vector<tuple<vector<uint8_t>, vector<uint8_t>>>& users_list) {
    for (const auto& user : users_list) {
        vector<uint8_t> client_id = get<0>(user);
        vector<uint8_t> name = get<1>(user);
        auto null_pos = find(name.begin(), name.end(), '\0');
        name.resize(distance(name.begin(), null_pos + 1));
        users_map[name] = client_id;
    }
}

// Gets the client ID for a given name
vector<uint8_t> UsersMap::get_client_id(const vector<uint8_t>& name) const {
    auto it = users_map.find(name);
    if (it != users_map.end()) {
        return it->second;
    }
    return vector<uint8_t>();
}

// Finds the name tied to a client ID
vector<uint8_t> UsersMap::get_name(const vector<uint8_t>& client_id) const {
    for (const pair<vector<uint8_t>, vector<uint8_t>>& entry : users_map) {
        if (entry.second == client_id)
            return entry.first;
    }
    string uu = "unknown user";
    return vector<uint8_t>(uu.begin(), uu.end());
}

// Checks if a name is in the map
bool UsersMap::has_name(const vector<uint8_t>& name) const {
    return users_map.find(name) != users_map.end();
}

// Prints the list of users
ostream& operator<<(ostream& os, const UsersMap& users) {
    int index = 1;
    os << "Clients list:\n";
    for (const pair<vector<uint8_t>, vector<uint8_t>>& entry : users.users_map) {
        os << index << ". ";
        for (const uint8_t byte : entry.first) {
            os << static_cast<char>(byte);
        }
        os << '\n';
        index++;
    }
    return os;
}