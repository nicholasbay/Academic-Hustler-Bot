import logging

from database.db_connector import execute_query

logger = logging.getLogger(__name__)


def initialize_db() -> None:
    """
    Initializes the database by creating the necessary tables if they do not already exist.

    Returns:
        None
    """
    try:
        execute_query("PRAGMA foreign_keys = ON")

        create_Whitelist_table()
        create_User_table()
        create_Conversation_table()
        create_Message_table()

        logger.info('Successfully initialized database.')
    except Exception as e:
        logger.error(f'Error initializing database: {str(e)}')
        raise

##################################################
# Operations on 'Whitelist' table
def create_Whitelist_table() -> None:
    """
    Creates the 'Whitelist' table in the database.

    Returns:
        None
    """
    logger.debug('Creating Whitelist table...')

    query = """
        CREATE TABLE IF NOT EXISTS Whitelist (
            user_id INTEGER PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(query)

    logger.debug('Successfully created Whitelist table.')


def add_whitelist_user(user_id: int) -> None:
    """
    Adds a new user to the 'Whitelist' table if the user does not already exist.

    Args:
        user_id (int): The user's ID.

    Returns:
        None
    """
    logger.debug(f'Adding user {user_id} to Whitelist...')

    query = """
        INSERT INTO Whitelist (user_id)
        SELECT ?
        WHERE NOT EXISTS (SELECT 1 FROM Whitelist WHERE user_id = ?)
    """
    params = (user_id, user_id)
    execute_query(query, params)

    logger.debug(f'Successfully added user {user_id} to Whitelist.')


def remove_whitelist_user(user_id: int) -> None:
    """
    Removes a user from the 'Whitelist' table.

    Args:
        user_id (int): The user's ID.

    Returns:
        None
    """
    logger.debug(f'Removing user {user_id} from Whitelist...')

    # Manual ON DELETE CASCADE
    remove_user(user_id)

    query = """
        DELETE FROM Whitelist
        WHERE user_id = ?
    """
    params = (user_id,)
    execute_query(query, params)

    logger.debug(f'Successfully removed user {user_id} from Whitelist.')


def get_whitelisted_user_ids() -> list:
    """
    Get all whitelisted users.

    Returns:
        list: A list of all whitelisted users.
    """
    logger.debug('Retrieving whitelisted user IDs...')

    query = """
        SELECT user_id
        FROM Whitelist
    """
    whitelisted_users = execute_query(query, fetch=True)

    logger.debug('Successfully retrieved all whitelisted user IDs.')

    return whitelisted_users


def find_whitelisted_user(user_id: int) -> bool:
    """
    Find a whitelisted user.

    Args:
        user_id (int): The user's ID.

    Returns:
        bool: True if the user is whitelisted, False otherwise.
    """
    logger.debug(f'Finding if user {user_id} is whitelisted...')

    query = """
        SELECT 1
        FROM Whitelist
        WHERE user_id = ?
    """
    params = (user_id,)
    whitelisted_user = execute_query(query, params, fetch=True)
    whitelisted = bool(whitelisted_user)

    logger.debug(f"User {user_id} {'is' if whitelisted else 'is not'} whitelisted.")

    return whitelisted
##################################################

##################################################
# Operations on 'User' table
def create_User_table() -> None:
    """
    Creates the 'User' table in the database.

    Returns:
        None
    """
    logger.debug('Creating User table...')

    query = """
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            FOREIGN KEY (user_id) REFERENCES Whitelist (user_id) ON DELETE CASCADE
        )
    """
    execute_query(query)

    logger.debug('Successfully created User table.')


def add_user(user_id: int, username: str) -> None:
    """
    Adds a new user to the 'User' table if the user does not already exist.

    Args:
        user_id (int): The user's ID.
        username (str): The user's username.

    Returns:
        None
    """
    logger.debug(f'Adding user {user_id} to User table...')

    query = """
        INSERT INTO User (user_id, username)
        SELECT ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM User WHERE user_id = ?)
    """
    params = (user_id, username, user_id)
    execute_query(query, params)

    logger.debug(f'Successfully added user {user_id} to User table.')


def remove_user(user_id: int) -> None:
    """
    Removes a user from the 'User' table and deletes his conversations.

    Args:
        user_id (int): The user's ID.

    Returns:
        None
    """
    logger.debug(f'Removing user {user_id} from User table...')

    # Manual ON DELETE CASCADE
    delete_user_conversations(user_id)

    query = """
        DELETE FROM User
        WHERE user_id = ?
    """
    params = (user_id,)
    execute_query(query, params)

    logger.debug(f'Successfully removed user {user_id} from User table.')
##################################################

##################################################
# Operations on 'Conversation' table
def create_Conversation_table() -> None:
    """
    Creates the 'Conversation' table in the database.

    Returns:
        None
    """
    logger.debug('Creating Conversation table...')

    query = """
        CREATE TABLE IF NOT EXISTS Conversation (
            conversation_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            FOREIGN KEY (user_id) REFERENCES User (user_id) ON DELETE CASCADE
        )
    """
    execute_query(query)

    logger.debug('Successfully created Conversation table.')


def add_conversation(user_id: int, title: str) -> int:
    """
    Adds a new conversation to the 'Conversation' table and returns the conversation ID.

    Args:
        user_id (int): The user's ID.
        title (str): The title of the conversation.

    Returns:
        int: The conversation ID.
    """
    logger.debug(f'Adding conversation for user {user_id} to Conversation table...')
    
    query = """
        INSERT INTO Conversation (user_id, title)
        VALUES (?, ?)
    """
    params = (user_id, title)
    conversation_id = execute_query(query, params, fetch_lastrowid=True)

    logger.debug(f'Successfully added conversation {conversation_id} for user {user_id} to Conversation table.')

    return conversation_id


def edit_conversation(user_id: int, conversation_id: int, new_title: str) -> None:
    """
    Updates the title of an existing conversation in the 'Conversation' table.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID.
        new_title (str): The new title of the conversation.

    Returns:
        None
    """
    logger.debug(f'Editing conversation {conversation_id} for user {user_id} in Conversation table...')

    query = """
        UPDATE Conversation
        SET title = ?
        WHERE user_id = ? AND conversation_id = ?
    """
    params = (new_title, user_id, conversation_id)
    execute_query(query, params)

    logger.debug(f'Successfully edited conversation {conversation_id} for user {user_id} in Conversation table.')


def delete_conversation(user_id: int, conversation_id: int) -> None:
    """
    Deletes a conversation and all associated messages from the 'Conversation' and 'Message' tables.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID.

    Returns:
        None
    """
    logger.debug(f'Deleting conversation {conversation_id} for user {user_id} from Conversation table...')

    # Manual ON DELETE CASCADE
    delete_conversation_messages(user_id, conversation_id)

    # Delete the conversation entry from the 'Conversation' table
    query = """
        DELETE FROM Conversation
        WHERE user_id = ? AND conversation_id = ?
    """
    params = (user_id, conversation_id)
    execute_query(query, params)

    logger.debug(f'Successfully deleted conversation {conversation_id} for user {user_id} from Conversation table.')


def delete_user_conversations(user_id: int) -> None:
    """
    Deletes all conversations for a user from the 'Conversation' table.

    Args:
        user_id (int): The user's ID.

    Returns:
        None
    """
    logger.debug(f'Deleting all conversations for user {user_id} from Conversation table...')

    # Manual ON DELETE CASCADE
    delete_user_messages(user_id)

    query = """
        DELETE FROM Conversation
        WHERE user_id = ?
    """
    params = (user_id,)
    execute_query(query, params)

    logger.debug(f'Successfully deleted all conversations for user {user_id} from Conversation table.')


def get_user_conversations(user_id: int) -> list:
    """
    Gets conversations for a particular user.

    Args:
        user_id (int): The user's ID.

    Returns:
        list: A list of all conversations for the user.
    """
    logger.debug(f'Retrieving conversations for user {user_id} from Conversation table...')

    query = """
        SELECT conversation_id, title
        FROM Conversation
        WHERE user_id = ?
    """
    params = (user_id,)
    conversations = execute_query(query, params, fetch=True)

    logger.debug(f'Successfully retrieved conversations for user {user_id} from Conversation table.')

    return conversations


def get_conversation_title(conversation_id: int) -> str:
    """
    Get the title of a conversation.

    Args:
        conversation_id (int): The conversation's ID.

    Returns:
        str: The title of the conversation.
    """
    logger.debug(f'Retrieving title for conversation {conversation_id} from Conversation table...')

    query = """
        SELECT title
        FROM Conversation
        WHERE conversation_id = ?
    """
    params = (conversation_id,)
    title = execute_query(query, params, fetch=True)[0][0]

    logger.debug(f'Successfully retrieved title for conversation {conversation_id} from Conversation table.')

    return title
##################################################

##################################################
# Operations on 'Message' table
def create_Message_table() -> None:
    """
    Creates the 'Message' table in the database.

    Returns:
        None
    """
    logger.debug('Creating Message table...')

    query = """
        CREATE TABLE IF NOT EXISTS Message (
            message_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            conversation_id INTEGER,
            message_role TEXT,
            message_content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES User (user_id) ON DELETE CASCADE,
            FOREIGN KEY (conversation_id) REFERENCES Conversation (conversation_id) ON DELETE CASCADE
        )
    """
    execute_query(query)

    logger.debug('Successfully created Message table.')


def add_message(user_id: int, conversation_id: int, message_role: str, message_content: str) -> None:
    """
    Adds a new message to the 'Message' table.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID associated with the message.
        message_role (str): The role of the message (e.g., 'user' or 'assistant').
        message_content (str): The content of the message.

    Returns:
        None
    """
    logger.debug(f'Adding message to conversation {conversation_id} for user {user_id} in Message table...')

    query = """
        INSERT INTO Message (user_id, conversation_id, message_role, message_content)
        VALUES (?, ?, ?, ?)
    """
    params = (user_id, conversation_id, message_role, message_content)
    execute_query(query, params)

    logger.debug(f'Successfully added message to conversation {conversation_id} for user {user_id} in Message table.')


def get_past_messages(user_id: int, conversation_id: int) -> list[dict[str, str]]:
    """
    Get the all of the past messages from the 'Message' table for a given conversation.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID.

    Returns:
        list: A list of the most recent ten messages.
    """
    logger.debug(f'Retrieving past ten messages for conversation {conversation_id} for user {user_id} from Message table...')
    query = """
        SELECT message_role, message_content
        FROM Message
        WHERE user_id = ? AND conversation_id = ?
        ORDER BY timestamp
    """
    params = (user_id, conversation_id)
    messages = execute_query(query, params, fetch=True)

    logger.debug(f'Successfully retrieved past messages for conversation {conversation_id} for user {user_id} from Message table.')

    messages_list = []
    for message in messages:
        messages_list.append({
            "role": message[0],
            "content": message[1]
        })

    return messages_list


def get_conversation_messages(user_id: int, conversation_id: int) -> list[dict[str, str]]:
    """
    Get all messages for a conversation from the 'Message' table.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID.

    Returns:
        list: A list of all messages for the conversation.
    """
    logger.debug(f'Retrieving all messages for conversation {conversation_id} for user {user_id} from Message table...')

    query = """
        SELECT message_role, message_content
        FROM Message
        WHERE user_id = ? AND conversation_id = ?
        ORDER BY timestamp
    """
    params = (user_id, conversation_id)
    messages = execute_query(query, params, fetch=True)

    logger.debug(f'Successfully retrieved all messages for conversation {conversation_id} for user {user_id} from Message table.')

    messages_list = []
    for message in messages:
        messages_list.append({
            "role": message[0],
            "content": message[1]
        })

    return messages_list


def delete_conversation_messages(user_id: int, conversation_id: int) -> None:
    """
    Deletes all messages for a conversation from the 'Message' table.

    Args:
        user_id (int): The user's ID.
        conversation_id (int): The conversation's ID.

    Returns:
        None
    """
    logger.debug(f'Deleting all messages for conversation {conversation_id} for user {user_id} from Message table...')

    query = """
        DELETE FROM Message
        WHERE user_id = ? AND conversation_id = ?
    """
    params = (user_id, conversation_id)
    execute_query(query, params)

    logger.debug(f'Successfully deleted all messages for conversation {conversation_id} for user {user_id} from Message table.')


def delete_user_messages(user_id: int) -> None:
    """
    Deletes all messages for a user from the 'Message' table.

    Args:
        user_id (int): The user's ID.

    Returns:
        None
    """
    logger.debug(f'Deleting all messages for user {user_id} from Message table...')

    query = """
        DELETE FROM Message
        WHERE user_id = ?
    """
    params = (user_id,)
    execute_query(query, params)

    logger.debug(f'Successfully deleted all messages for user {user_id} from Message table.')
##################################################
