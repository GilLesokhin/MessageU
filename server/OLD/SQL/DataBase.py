import sqlite3
import datetime

class DefensiveDB:
    def __init__(self, db_file='defensive.db'):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Creating Table 1: User info table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            ID BLOB PRIMARY KEY,
            UserName TEXT NOT NULL,
            PublicKey BLOB NOT NULL,
            LastSeen DATE
        )""")
        
        # Creating Table 2: Messages table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Messages (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ToClient BLOB NOT NULL,
            FromClient BLOB NOT NULL,
            Type INTEGER NOT NULL,
            Content BLOB NOT NULL
        )""")
        
        self.conn.commit()

    def insert_user(self, user_id, username, public_key, last_seen=None):
        if last_seen is None:
            last_seen = datetime.datetime.now()
        
        self.cursor.execute("""
        INSERT INTO Users (ID, UserName, PublicKey, LastSeen)
        VALUES (?, ?, ?, ?)
        """, (user_id, username, public_key, last_seen))
        
        self.conn.commit()

    def update_user(self, user_id, username=None, public_key=None, last_seen=None):
        query = "UPDATE Users SET "
        params = []
        
        if username:
            query += "UserName = ?, "
            params.append(username)
        
        if public_key:
            query += "PublicKey = ?, "
            params.append(public_key)
        
        if last_seen:
            query += "LastSeen = ?, "
            params.append(last_seen)
        
        query = query.rstrip(', ')  # Remove the last comma and space
        query += " WHERE ID = ?"
        params.append(user_id)
        
        self.cursor.execute(query, tuple(params))
        self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM Users WHERE ID = ?", (user_id,))
        self.conn.commit()

    def insert_message(self, to_client, from_client, msg_type, content):
        self.cursor.execute("""
        INSERT INTO Messages (ToClient, FromClient, Type, Content)
        VALUES (?, ?, ?, ?)
        """, (to_client, from_client, msg_type, content))
        
        self.conn.commit()

    def update_message(self, message_id, to_client=None, from_client=None, msg_type=None, content=None):
        query = "UPDATE Messages SET "
        params = []
        
        if to_client:
            query += "ToClient = ?, "
            params.append(to_client)
        
        if from_client:
            query += "FromClient = ?, "
            params.append(from_client)
        
        if msg_type is not None:
            query += "Type = ?, "
            params.append(msg_type)
        
        if content is not None:
            query += "Content = ?, "
            params.append(content)
        
        query = query.rstrip(', ')  # Remove the last comma and space
        query += " WHERE ID = ?"
        params.append(message_id)
        
        self.cursor.execute(query, tuple(params))
        self.conn.commit()

    def delete_message(self, message_id):
        self.cursor.execute("DELETE FROM Messages WHERE ID = ?", (message_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


# Usage Example
if __name__ == "__main__":
    # Create database and tables
    db = DefensiveDB()
    
    # Insert a user
    user_id = b'\x01' * 16  # Example 16-byte user ID
    public_key = b'\x02' * 160  # Example 160-byte public key
    db.insert_user(user_id, "JohnDoe", public_key, datetime.datetime.now())
    
    # Insert a message
    to_client = b'\x01' * 16
    from_client = b'\x02' * 16
    message_content = b'Hello, World!'
    db.insert_message(to_client, from_client, 1, message_content)
    
    # Update a user's details
    db.update_user(user_id, username="JaneDoe")
    
    # Update a message's content
    db.update_message(1, content=b'Updated message content.')
    
    # Delete a message
    db.delete_message(1)
    
    # Delete a user
    db.delete_user(user_id)
    
    # Close the connection
    db.close()
