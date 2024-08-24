import base64
import logging

import telebot
from telegramify_markdown import markdownify

import database.models as db
from bot_core.states import UserState

logger = logging.getLogger(__name__)

# Dictionary to store the state and conversation ID of each user
# {
#   user_id (int): {
#       'state': state,
#       'conversation_id': conversation_id,
#       'message_ids': [message_id1, message_id2, ...],
#       'last_activity': time_of_last_activity,
#       'temp_data': temp_data
#   }
# }
user_data = {}


##################################################
# Functions for managing users' data
def initialize_users_data() -> None:
    """
    Initializes the user data in memory.

    Returns:
        None
    """
    try:
        global user_data

        user_ids = db.get_whitelisted_user_ids()

        for user_id in user_ids:
            user_id = user_id[0]       # DB results are returned as tuples
            user_data[user_id] = {}
            set_user_state(user_id, UserState.IDLE)
            set_user_conversation_id(user_id, None)
            set_user_message_ids(user_id, [])
            
            set_user_temp_data(user_id, None)

        logger.info('Successfully initialized user data.')
    except Exception as e:
        logger.error(f'Error initializing user data: {str(e)}')
        raise


def set_user_state(user_id: int, state: int) -> None:
    """
    Sets the state of a user.

    Args:
        user_id (int): The user's ID.
        state (int): The state to be set.

    Returns:
        None
    """
    user_data.setdefault(user_id, {})['state'] = state


def get_user_state(user_id: int) -> int:
    """
    Gets the state of a user.

    Args:
        user_id (int): The user's ID.

    Returns:
        int: The state of the user.
    """
    return user_data.get(user_id, {}).get('state', UserState.IDLE)


def set_user_conversation_id(user_id: int, conversation_id: int | None) -> None:
    """
    Sets the conversation ID of a user.

    Args:
        user_id (int): The user's ID.
        conversation_id (int or None): The conversation ID to be set. None if the user is not in a conversation.

    Returns:
        None
    """
    user_data.setdefault(user_id, {})['conversation_id'] = conversation_id


def get_user_conversation_id(user_id: int) -> int | None:
    """
    Gets the conversation ID of a user.

    Args:
        user_id (int): The user's ID.

    Returns:
        int or None: The conversation ID of the user. None if the user is not in a conversation.
    """
    return user_data.get(user_id, {}).get('conversation_id', None)


def set_user_message_ids(user_id: int, message_ids: list) -> None:
    """
    Sets the list of message IDs of a user.

    Args:
        user_id (int): The user's ID.
        message_ids (list): The list of message IDs to be set.

    Returns:
        None
    """
    user_data.setdefault(user_id, {})['message_ids'] = message_ids


def get_user_message_ids(user_id: int) -> list:
    """
    Gets the list of message IDs of a user.

    Args:
        user_id (int): The user's ID.

    Returns:
        list: The list of message IDs of the user.
    """
    return user_data.get(user_id, {}).get('message_ids', [])


def add_user_message_id(user_id: int, message_id: int) -> None:
    """
    Adds a message ID to the list of message IDs of a user.

    Args:
        user_id (int): The user's ID.
        message_id (int): The message ID to be added.

    Returns:
        None
    """
    user_data.setdefault(user_id, {}).setdefault('message_ids', []).append(message_id)


def set_user_last_activity(user_id: int, last_activity: float) -> None:
    """
    Sets the time of the last activity of a user.

    Args:
        user_id (int): The user's ID.
        last_activity (float): The time of the last activity.

    Returns:
        None
    """
    user_data.setdefault(user_id, {})['last_activity'] = last_activity


def get_user_last_activity(user_id: int) -> float:
    """
    Gets the time of the last activity of a user.

    Args:
        user_id (int): The user's ID.

    Returns:
        float: The time of the last activity of the user.
    """
    return user_data.get(user_id, {}).get('last_activity', None)


def set_user_temp_data(user_id: int, temp_data: dict | None) -> None:
    """
    Sets the temporary data of a user.

    Args:
        user_id (int): The user's ID.
        temp_data (dict or None): The temporary data to be set.

    Returns:
        None
    """
    user_data.setdefault(user_id, {})['temp_data'] = temp_data


def get_user_temp_data(user_id: int) -> dict | None:
    """
    Gets the temporary data of a user.

    Args:
        user_id (int): The user's ID.

    Returns:
        dict or None: The temporary data of the user.
    """
    return user_data.get(user_id, {}).get('temp_data', None)
##################################################


def verify_user(user_id: int) -> bool:
    """
    Verifies if the user has been whitelisted to use the bot.

    Args:
        user_id (int): The user's ID.

    Returns:
        bool: True if the user is whitelisted, False otherwise.
    """
    whitelisted = db.find_whitelisted_user(user_id)

    return whitelisted


def custom_inline_keyboard(buttons: list) -> telebot.types.InlineKeyboardMarkup:
    """
    Creates a custom inline keyboard with the given list of buttons.

    Args:
        buttons (list): A list of lists, where each inner list represents a row.
                        Each item in the inner list is a tuple (button_text, callback_data).

    Returns:
        telebot.types.InlineKeyboardMarkup: A custom inline keyboard markup with the given buttons.
    """
    keyboard = []

    for row_buttons in buttons:
        row = []
        
        for button_text, callback_data in row_buttons:
            row.append(telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data))
        
        keyboard.append(row)

    markup = telebot.types.InlineKeyboardMarkup(keyboard)

    return markup


def admin_menu_inline_keyboard() -> telebot.types.InlineKeyboardMarkup:
    buttons = []
    buttons.append([('➕ Add Whitelist User', 'add')])
    buttons.append([('➖ Remove Whitelist User', 'remove')])
    buttons.append([('📜 Show Whitelist Users', 'show')])
    buttons.append([('👋 Quit', 'quit')])

    markup = custom_inline_keyboard(buttons)

    return markup


def admin_remove_whitelist_user_inline_keyboard() -> telebot.types.InlineKeyboardMarkup:
    # Fetch whitelisted users
    user_ids = db.get_whitelisted_user_ids()

    # Create custom keyboard
    buttons = []

    for user_id in user_ids:
        user_id = user_id[0]        # DB results are returned as tuples
        # Button text: User ID, Callback data: User ID
        buttons.append([(f'👤 {user_id}', f'{user_id}')])
    buttons.append([('🔙 Back', 'back'), ('👋 Quit', 'quit')])
    markup = custom_inline_keyboard(buttons)

    return markup


def back_quit_inline_keyboard() -> telebot.types.InlineKeyboardMarkup:
    """
    Creates an inline keyboard with 'Back' and 'Quit' buttons.

    Returns:
        telebot.types.InlineKeyboardMarkup: An inline keyboard markup with 'Back' and 'Quit' buttons.
    """
    buttons = [[('🔙 Back', 'back'), ('👋 Quit', 'quit')]]
    markup = custom_inline_keyboard(buttons)

    return markup


def confirmation_inline_keyboard() -> telebot.types.InlineKeyboardMarkup:
    """
    Creates an inline keyboard with 'Yes' and 'No' buttons for confirmation.

    Returns:
        telebot.types.InlineKeyboardMarkup: An inline keyboard markup with 'Yes' and 'No' buttons.
    """
    buttons = [[('✔️ Yes', 'yes'), ('❌ No', 'no')]]
    markup = custom_inline_keyboard(buttons)

    return markup


def conversations_inline_keyboard(user_id: int) -> telebot.types.InlineKeyboardMarkup:
    # Fetch user's conversations
    conversations = [(conversation_id, title) for conversation_id, title in db.get_user_conversations(user_id)]

    # Create custom keyboard
    buttons = []
    for conversation in conversations:
        # Button text: Conversation title, Callback data: Conversation ID
        buttons.append([(f'💬 {conversation[1]}', f'{conversation[0]}')])
    buttons.append([('🔙 Back', 'back'), ('👋 Quit', 'quit')])
    markup = custom_inline_keyboard(buttons)

    return markup


def main_menu_inline_keyboard() -> telebot.types.InlineKeyboardMarkup:
    buttons = []

    buttons.append([('🆕 Create New Conversation', 'create')])
    buttons.append([('💬 Load Existing Conversation', 'load')])
    buttons.append([('✏️ Edit Existing Conversation', 'edit')])
    buttons.append([('🗑️ Delete Existing Conversation', 'delete')])
    buttons.append([('❓ Help', 'help'), ('🆔 Show User ID', 'id'), ('👋 Quit', 'quit')])

    markup = custom_inline_keyboard(buttons)

    return markup


def convert_image_to_base64(image_path: str) -> str:
    """
    Converts an image to base64 encoding.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64 encoded image.
    """
    with open(image_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    return encoded_image


def convert_to_mdv2(mdv1_text: str) -> str:
    return markdownify(mdv1_text)
