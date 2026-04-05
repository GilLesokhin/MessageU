#ifndef USERS_MAP_H
#define USERS_MAP_H

#include <map>
#include <ostream>
#include <tuple>
#include <vector>

#include "Protocol.h"

class UsersMap {
private:
    std::map<std::vector<uint8_t>, std::vector<uint8_t>> users_map;  // client_id -> name

public:
    UsersMap() = default;
    UsersMap(const std::vector<std::tuple<std::vector<uint8_t>, std::vector<uint8_t>>>& users_list);

    std::vector<uint8_t> get_client_id(const std::vector<uint8_t>& name) const;
    std::vector<uint8_t> get_name(const std::vector<uint8_t>& client_id) const;

    bool has_name(const std::vector<uint8_t>& name) const;

    friend std::ostream& operator<<(std::ostream& os, const UsersMap& users);
};

#endif  // USERS_MAP_H