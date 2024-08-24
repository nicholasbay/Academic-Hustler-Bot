import logging
from os import getenv
import time

from dotenv import load_dotenv
import telebot
from telebot.util import smart_split

import bot_core.gpt_client as gpt
import bot_core.utils as utils
from bot_core.states import UserState
from bot_core.strings import Strings
import database.models as db

logger = logging.getLogger(__name__)


def initialize_bot() -> telebot.TeleBot:
    """
    Initializes the main bot and states for whitelist users.

    Returns:
        telebot.TeleBot: The main bot.
    """
    try:
        # Load environment variables
        load_dotenv()

        global bot
        bot = telebot.TeleBot(getenv('BOT_TOKEN'))      # Telegram bot

        logger.info('Successfully initialized Telegram bot.')
    except Exception as e:
        logger.error(f'Error initializing Telegram bot: {str(e)}')
        raise


# Initialize the bot globally
initialize_bot()

##################################################
# Functions for interacting with GPT
def add_conversation_and_generate_title(message: telebot.types.Message) -> int:
    """
    Creates a new conversation and returns the conversation ID.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        int: The conversation ID.
    """
    user_id = message.from_user.id
    prompt = message.text.strip()

    title = gpt.generate_title(prompt).strip()
    conv_id = db.add_conversation(user_id, title)

    new_conv_message_text = Strings.NEW_CONV_HEADER + f'Now conversing in _{title}_.'
    new_conv_message_text = utils.convert_to_mdv2(new_conv_message_text)
    sent_message_id = send_mdv2_message(message.chat.id, new_conv_message_text)
    utils.add_user_message_id(user_id, sent_message_id)

    logger.info(f'User {user_id} created new conversation: "{title}", ID: {conv_id}')

    return conv_id


def process_gpt_interaction(message: telebot.types.Message, conv_id: int) -> None:
    """
    Processes user's interaction with GPT by:
        1. Sending the user's message to the GPT model, and
        2. Sending the GPT model's response to the user.

    Args:
        message (telebot.types.Message): The message sent by the user.
        conv_id (int): The ID of the conversation to which the message belongs.

    Returns:
        None
    """
    user_id = message.from_user.id

    prompt = message.text.strip()

    indicator_message_id = send_mdv2_message(message.chat.id, 'Thinking...', disable_notification=True)

    past_messages = db.get_past_messages(user_id, conv_id)

    gpt_response = gpt.generate_response(prompt, past_messages)

    # Add unformatted messages to DB
    db.add_message(user_id, conv_id, 'user', prompt)
    db.add_message(user_id, conv_id, 'assistant', gpt_response)

    # Format GPT response
    gpt_response = utils.convert_to_mdv2(gpt_response)
    bot_response = Strings.BOT_MESSAGE_HEADER + gpt_response + Strings.BOT_RESPONSE_FOOTER

    markup = utils.back_quit_inline_keyboard()

    bot.delete_message(message.chat.id, indicator_message_id)

    # Entire bot response may be too long to send in one message
    for chunk in smart_split(bot_response):
        sent_message = bot.reply_to(message, chunk, reply_markup=markup, parse_mode='MarkdownV2')
        utils.add_user_message_id(user_id, sent_message.id)
##################################################

##################################################
def send_mdv2_message(chat_id: int,
                      text: str,
                      reply_markup: telebot.types.ReplyKeyboardMarkup = None,
                      parse_mode: str = 'MarkdownV2',
                      disable_notification: bool = False) -> int:
    """
    Sends a message with MarkdownV2 formatting.

    Args:
        chat_id (int): The ID of the chat to send the message to.
        text (str): The text of the message.
        reply_markup (telebot.types.ReplyKeyboardMarkup): The reply keyboard markup.
        parse_mode (str): The parse mode of the message.
        disable_notification (bool): Whether to disable notification for the message.

    Returns:
        int: The ID of the sent message.
    """
    try:
        sent_message = bot.send_message(chat_id,
                                        text,
                                        reply_markup=reply_markup,
                                        parse_mode=parse_mode,
                                        disable_notification=disable_notification)
    except:
        sent_message = bot.send_message(chat_id,
                                        text,
                                        reply_markup=reply_markup,
                                        parse_mode=None,
                                        disable_notification=disable_notification)
    return sent_message.id


def edit_mdv2_message(text:str,
                      chat_id: int,
                      message_id: int,
                      reply_markup: telebot.types.ReplyKeyboardMarkup = None,
                      parse_mode: str = 'MarkdownV2') -> None:
    """
    Edits a message with MarkdownV2 formatting.

    Args:
        text (str): The text of the message.
        chat_id (int): The ID of the chat to send the message to.
        message_id (int): The ID of the message to edit.
        reply_markup (telebot.types.ReplyKeyboardMarkup): The reply keyboard markup.
        parse_mode (str): The parse mode of the message.

    Returns:
        None
    """
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)


def load_existing_conversation(call: telebot.types.CallbackQuery, conversation_id: int) -> None:
    """
    Loads an existing conversation based on the conversation ID.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.
        conversation_id (int): The ID of the conversation to load.

    Returns:
        None
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    title = db.get_conversation_title(conversation_id)
    title_message_text = Strings.EXTG_CONV_HEADER + f'_{title}_'
    title_message_text = utils.convert_to_mdv2(title_message_text)
    title_message_id = send_mdv2_message(call.message.chat.id,
                                         title_message_text,
                                         disable_notification=True)
    utils.add_user_message_id(user_id, title_message_id)

    past_messages = db.get_conversation_messages(user_id, conversation_id)
    for past_message in past_messages:
        role, content = past_message['role'], past_message['content']
        header = Strings.USER_MESSAGE_HEADER if role == 'user' else Strings.BOT_MESSAGE_HEADER
        
        # Past messages may be too long
        for chunk in smart_split(header + content):
            chunk = utils.convert_to_mdv2(chunk)
            sent_message_id = send_mdv2_message(chat_id, chunk, disable_notification=True)
            utils.add_user_message_id(user_id, sent_message_id)


# Delete past messages
def delete_past_messages(user_id: int, message_ids: list) -> None:
    """
    Deletes past messages sent by the user.

    Args:
        user_id (int): The ID of the user.
        message_ids (list): The list of message IDs to delete.

    Returns:
        None
    """
    try:
        bot.delete_messages(user_id, message_ids)
    except:
        pass

    utils.set_user_message_ids(user_id, [])


def check_inactivity() -> None:
    """
    Checks if users have been inactive for more than 30 minutes and resets their state to idle.
    """
    TIMEOUT_SECONDS = 1800
    user_ids = db.get_whitelisted_user_ids()
    
    while True:
        current_time = time.time()
        
        for user_id in user_ids:
            user_id = user_id[0]
            last_activity = utils.get_user_last_activity(user_id)
            user_state = utils.get_user_state(user_id)
            
            if (last_activity is not None and
                user_state != UserState.IDLE and
                current_time - last_activity > TIMEOUT_SECONDS):
                timeout_message = send_mdv2_message(user_id, Strings.TIMEOUT_MESSAGE, disable_notification=True)

                past_message_ids = utils.get_user_message_ids(user_id)
                delete_past_messages(user_id, past_message_ids)

                utils.set_user_state(user_id, UserState.IDLE)
                utils.set_user_conversation_id(user_id, None)
                utils.set_user_last_activity(user_id, None)
                utils.add_user_message_id(user_id, timeout_message)

                logger.info(f'User {user_id} has been reset to idle state due to inactivity.')

        time.sleep(60)
##################################################


##################################################
# Handlers
@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_state(message.from_user.id) == UserState.IDLE
))
def idle_handler(message: telebot.types.Message) -> None:
    """
    Handles all messages that are not commands when the user is in the idle state.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    utils.add_user_message_id(message.from_user.id, message.id)

    idle_message = bot.send_message(message.chat.id, Strings.IDLE_MESSAGE, parse_mode='MarkdownV2')
    utils.add_user_message_id(message.from_user.id, idle_message.id)


@bot.callback_query_handler(func=lambda call: utils.get_user_state(call.from_user.id) == UserState.IDLE)
def idle_button_presses_handler(call: telebot.types.CallbackQuery) -> None:
    """
    Handles button presses when the user is in the idle state.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    idle_message = bot.send_message(call.message.chat.id, Strings.IDLE_MESSAGE, parse_mode='MarkdownV2')
    utils.add_user_message_id(call.from_user.id, idle_message.id)


@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_state(message.from_user.id) in (
        UserState.MAIN_MENU,
        UserState.LOAD_CONV,
        UserState.EDIT_CONV_0,
        UserState.DELETE_CONV_0,
        UserState.DELETE_CONV_1,
        UserState.ADMIN_MENU,
        UserState.REMOVE_WHITELIST_USER,
        UserState.SHOW_WHITELIST_USERS
    )
))
def invalid_message_handler(message: telebot.types.Message) -> None:
    """
    Handles invalid messages when a callback query is expected.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    utils.add_user_message_id(message.from_user.id, message.id)

    sent_message_id = send_mdv2_message(message.chat.id, Strings.INVALID_INPUT_ERROR)
    utils.add_user_message_id(message.from_user.id, sent_message_id)


@bot.callback_query_handler(func=lambda call: (
    call.data == 'create' and
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_create_conversation(call: telebot.types.CallbackQuery) -> None:
    """
    Creates a new conversation. User is directed here when they select 'Create New Conversation' from the main menu.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Creating new conversation...')
    
    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.NEW_CONV)    

    markup = utils.back_quit_inline_keyboard()
    edit_mdv2_message(Strings.NEW_CONV_MESSAGE,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=markup)


@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_state(message.from_user.id) == UserState.NEW_CONV
))
def new_conversation_handler(message: telebot.types.Message) -> None:
    """
    Handles new conversation creation when the user is in the new conversation state.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    user_id = message.from_user.id
    utils.add_user_message_id(user_id, message.id)

    # Create new conversation
    # Add conversation to DB & generate title
    conv_id = add_conversation_and_generate_title(message)

    # Process the user's prompt
    process_gpt_interaction(message, conv_id)

    # Update user state and conversation ID
    utils.set_user_state(user_id, UserState.EXTG_CONV)
    utils.set_user_conversation_id(user_id, conv_id)

    logger.info(f'User {user_id} started new conversation: "{db.get_conversation_title(conv_id)}", ID: {conv_id}')


@bot.callback_query_handler(func=lambda call: (
    call.data == 'load' and 
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_load_all_conversations(call: telebot.types.CallbackQuery) -> None:
    """
    Shows all the existing conversations for the user to choose from. User is directed here after they select 'Load Existing Conversation' from the main menu.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Loading existing conversations...')

    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.LOAD_CONV)

    conversations = db.get_user_conversations(user_id)
    is_conversations_empty = len(conversations) == 0

    if is_conversations_empty:
        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(Strings.NO_CONV_TO_LOAD_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    else:
        markup = utils.conversations_inline_keyboard(user_id)
        edit_mdv2_message(Strings.LOAD_CONV_MESSAGE,
                        call.message.chat.id,
                        call.message.id,
                        reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data.isdigit() and
    utils.get_user_state(call.from_user.id) == UserState.LOAD_CONV
))
def callback_load_existing_conversation(call: telebot.types.CallbackQuery) -> None:
    """
    Loads an existing conversation based on the conversation ID.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    conv_id = call.data
    title = db.get_conversation_title(conv_id)

    bot.answer_callback_query(call.id, f'Loading "{title}"...')

    user_id = call.from_user.id

    utils.set_user_state(user_id, UserState.EXTG_CONV)
    utils.set_user_conversation_id(user_id, conv_id)
    
    bot.delete_message(call.message.chat.id, call.message.id)
    
    load_existing_conversation(call, conv_id)
    
    sent_message_id = send_mdv2_message(call.message.chat.id,
                                        Strings.EXTG_CONV_MESSAGE,
                                        reply_markup=utils.back_quit_inline_keyboard())
    utils.add_user_message_id(user_id, sent_message_id)


@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_state(message.from_user.id) == UserState.EXTG_CONV
))
def existing_conversation_text_handler(message: telebot.types.Message) -> None:
    """
    Handles the continuation of an existing conversation.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    user_id = message.from_user.id
    conversation_id = utils.get_user_conversation_id(user_id)

    utils.add_user_message_id(user_id, message.id)
    process_gpt_interaction(message, conversation_id)


@bot.callback_query_handler(func=lambda call: (
    call.data == 'edit' and
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_edit_conversations(call: telebot.types.CallbackQuery) -> None:
    """
    Loads the edit conversation menu. User is directed here after they select 'Edit Conversation' from the main menu.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Loading edit conversation menu...')

    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.EDIT_CONV_0)

    conversations = db.get_user_conversations(user_id)
    is_conversations_empty = len(conversations) == 0

    if is_conversations_empty:
        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(Strings.NO_CONV_TO_EDIT_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    else:
        markup = utils.conversations_inline_keyboard(user_id)
        edit_mdv2_message(Strings.EDIT_CONV_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data.isdigit() and
    utils.get_user_state(call.from_user.id) == UserState.EDIT_CONV_0
))
def callback_edit_selected_conversation(call: telebot.types.CallbackQuery) -> None:
    """
    Prompts user for new title of the selected conversation. User is directed here after they select a conversation to edit.

    Args:
        call (telebot.types.CallbackQuery): The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    conv_id = call.data
    title = db.get_conversation_title(conv_id)

    bot.answer_callback_query(call.id, f'Editing "{title}"...')

    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.EDIT_CONV_1)
    utils.set_user_conversation_id(user_id, conv_id)

    markup = utils.back_quit_inline_keyboard()
    edit_conv_message_text = (Strings.EDIT_CONV_HEADER + 
                              f'Enter a new name for _{title}_.' +
                              Strings.NAVIGATION_FOOTER)
    edit_conv_message_text = utils.convert_to_mdv2(edit_conv_message_text)
    edit_mdv2_message(edit_conv_message_text,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=markup)


@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_conversation_id(message.from_user.id) is not None and
    utils.get_user_state(message.from_user.id) == UserState.EDIT_CONV_1
))
def edit_conversation_handler(message: telebot.types.Message) -> None:
    """
    Handles the renaming of a conversation. User sends in the new title of the selected conversation.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    user_id = message.from_user.id
    utils.add_user_message_id(user_id, message.id)

    conversation_id = utils.get_user_conversation_id(user_id)
    new_title = message.text.strip()

    db.edit_conversation(user_id, conversation_id, new_title)
    
    edit_conv_message_text = (Strings.EDIT_CONV_HEADER +
                              f'Conversation has been renamed to _{new_title}_.' +
                              Strings.NAVIGATION_FOOTER)
    edit_conv_message_text = utils.convert_to_mdv2(edit_conv_message_text)
    markup = utils.back_quit_inline_keyboard()

    past_message_ids = utils.get_user_message_ids(user_id)
    delete_past_messages(user_id, past_message_ids)
    utils.set_user_conversation_id(user_id, None)

    sent_message_id = send_mdv2_message(message.chat.id, edit_conv_message_text, reply_markup=markup)
    utils.add_user_message_id(user_id, sent_message_id)


@bot.message_handler(func=lambda message: (
    not telebot.util.is_command(message.text) and
    utils.get_user_conversation_id(message.from_user.id) is None and
    utils.get_user_state(message.from_user.id) == UserState.EDIT_CONV_1
))
def invalid_edit_conversation_handler(message: telebot.types.Message) -> None:
    """
    Handles invalid messages when the user is editing a conversation.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    user_id = message.from_user.id
    utils.add_user_message_id(user_id, message.id)

    sent_message_id = send_mdv2_message(message.chat.id, Strings.INVALID_INPUT_ERROR)
    utils.add_user_message_id(user_id, sent_message_id)


@bot.callback_query_handler(func=lambda call: (
    call.data == 'delete' and
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_delete_conversations(call: telebot.types.CallbackQuery) -> None:
    """
    Loads the delete conversation menu. User is directed here after they select 'Delete Conversation' from the main menu.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Loading delete conversation menu...')

    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.DELETE_CONV_0)

    conversations = db.get_user_conversations(user_id)
    is_conversations_empty = len(conversations) == 0

    if is_conversations_empty:
        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(Strings.NO_CONV_TO_DELETE_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    else:
        markup = utils.conversations_inline_keyboard(user_id)
        edit_mdv2_message(Strings.DELETE_CONV_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data.isdigit() and
    utils.get_user_state(call.from_user.id) == UserState.DELETE_CONV_0
))
def callback_delete_selected_conversation(call: telebot.types.CallbackQuery) -> None:
    """
    Prompts user for confirmation to delete the selected conversation. User is directed here after they select a conversation to delete.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    conv_id = call.data
    title = db.get_conversation_title(conv_id)

    bot.answer_callback_query(call.id, f'Deleting "{title}"...')

    user_id = call.from_user.id
    utils.set_user_state(user_id, UserState.DELETE_CONV_1)
    utils.set_user_conversation_id(user_id, conv_id)

    markup = utils.confirmation_inline_keyboard()
    confirmation_message_text = Strings.DELETE_CONV_HEADER + f'Permanently delete _{title}_?'
    confirmation_message_text = utils.convert_to_mdv2(confirmation_message_text)
    edit_mdv2_message(confirmation_message_text,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data in ['yes', 'no'] and
    utils.get_user_state(call.from_user.id) == UserState.DELETE_CONV_1
))
def callback_delete_conversation_confirmation(call: telebot.types.CallbackQuery) -> None:
    """
    Handles the confirmation of deleting a conversation.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    user_id = call.from_user.id
    conv_id = utils.get_user_conversation_id(user_id)

    if call.data == 'yes':
        db.delete_conversation(user_id, conv_id)
        bot.answer_callback_query(call.id, 'Conversation deleted.')

        delete_conv_success_message_text = (Strings.DELETE_CONV_HEADER +
                                            'Conversation has been deleted.' +
                                            Strings.NAVIGATION_FOOTER)
        delete_conv_success_message_text = utils.convert_to_mdv2(delete_conv_success_message_text)
        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(delete_conv_success_message_text,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    elif call.data == 'no':
        bot.answer_callback_query(call.id, 'Deletion canceled.')

        utils.set_user_state(user_id, UserState.DELETE_CONV_0)
        utils.set_user_conversation_id(user_id, None)       # Reset conversation ID in memory

        markup = utils.conversations_inline_keyboard(user_id)
        edit_mdv2_message(Strings.DELETE_CONV_MESSAGE,
                         call.message.chat.id,
                         call.message.id,
                         reply_markup=markup)


@bot.callback_query_handler(func=lambda call:(
    call.data == 'help' and
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_help(call: telebot.types.CallbackQuery) -> None:
    """
    Shows the available commands. User is directed here after they select 'Help' from the main menu.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Loading help menu...')

    edit_mdv2_message(Strings.HELP_MESSAGE,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=utils.back_quit_inline_keyboard())


@bot.callback_query_handler(func=lambda call: (
    call.data == 'id' and 
    utils.get_user_state(call.from_user.id) == UserState.MAIN_MENU
))
def callback_id(call: telebot.types.CallbackQuery) -> None:
    """
    Shows the Telegram ID of the user. User is directed here after they select 'Show User ID' from the main menu.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Getting user ID...')

    user_id = call.from_user.id
    id_message_text = Strings.ID_HEADER + f'Your user ID is *{user_id}*.' + Strings.NAVIGATION_FOOTER
    id_message_text = utils.convert_to_mdv2(id_message_text)
    edit_mdv2_message(id_message_text,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=utils.back_quit_inline_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_back(call: telebot.types.CallbackQuery) -> None:
    """
    Handles 'Back' button presses by the user.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    user_id = call.from_user.id
    user_state = utils.get_user_state(user_id)

    # User is in admin submenu, return to admin menu
    if user_state in (UserState.ADD_WHITELIST_USER, UserState.REMOVE_WHITELIST_USER, UserState.SHOW_WHITELIST_USERS):
        bot.answer_callback_query(call.id, 'Returning to admin menu...')

        utils.set_user_state(user_id, UserState.ADMIN_MENU)
        utils.set_user_conversation_id(user_id, None)

        markup = utils.admin_menu_inline_keyboard()
        edit_mdv2_message(Strings.ADMIN_MENU_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
        return

    # User is in edit conversation submenus, return to edit conversation menu
    if user_state == UserState.EDIT_CONV_1:
        bot.answer_callback_query(call.id, 'Returning to edit conversation menu...')

        utils.set_user_state(user_id, UserState.EDIT_CONV_0)
        utils.set_user_conversation_id(user_id, None)

        conversations = db.get_user_conversations(user_id)
        is_conversations_empty = len(conversations) == 0

        if is_conversations_empty:
            markup = utils.back_quit_inline_keyboard()
            edit_mdv2_message(Strings.NO_CONV_TO_EDIT_MESSAGE,
                              call.message.chat.id,
                              call.message.id,
                              reply_markup=markup)
        else:
            markup = utils.conversations_inline_keyboard(user_id)
            edit_mdv2_message(Strings.EDIT_CONV_MESSAGE,
                              call.message.chat.id,
                              call.message.id,
                              reply_markup=markup)
        return

    # User is in delete conversation submenus, return to delete conversation menu
    if user_state == UserState.DELETE_CONV_1:
        bot.answer_callback_query(call.id, 'Returning to delete conversation menu...')

        utils.set_user_state(user_id, UserState.DELETE_CONV_0)
        utils.set_user_conversation_id(user_id, None)

        conversations = db.get_user_conversations(user_id)
        is_conversations_empty = len(conversations) == 0

        if is_conversations_empty:
            markup = utils.back_quit_inline_keyboard()
            edit_mdv2_message(Strings.NO_CONV_TO_DELETE_MESSAGE,
                            call.message.chat.id,
                            call.message.id,
                            reply_markup=markup)
        else:
            markup = utils.conversations_inline_keyboard(user_id)
            edit_mdv2_message(Strings.DELETE_CONV_MESSAGE,
                            call.message.chat.id,
                            call.message.id,
                            reply_markup=markup)
        return

    # User is in all other states, return to main menu
    bot.answer_callback_query(call.id, 'Returning to main menu...')

    utils.set_user_state(user_id, UserState.MAIN_MENU)
    utils.set_user_conversation_id(user_id, None)

    markup = utils.main_menu_inline_keyboard()
    # User is in existing covnersation, delete past messages before returning to main menu
    if user_state == UserState.EXTG_CONV:
        past_message_ids = utils.get_user_message_ids(user_id)

        start_message_id = send_mdv2_message(call.message.chat.id, Strings.MAIN_MENU_MESSAGE, reply_markup=markup)
        delete_past_messages(user_id, past_message_ids)

        utils.add_user_message_id(user_id, start_message_id)
    # Use is in any other state, return to main menu normally
    else:
        edit_mdv2_message(Strings.MAIN_MENU_MESSAGE,
                            call.message.chat.id,
                            call.message.id,
                            reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'quit')
def callback_quit(call: telebot.types.CallbackQuery) -> None:
    """
    Handles 'Quit' button presses by the user. Clears all messages within the past 48h (Telegram limit) and resets user data in memory.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    bot.answer_callback_query(call.id, 'Quitting...')

    user_id = call.from_user.id
    past_message_ids = utils.get_user_message_ids(user_id)
    utils.set_user_state(user_id, UserState.IDLE)
    utils.set_user_conversation_id(user_id, None)

    # Send idle message before deletion to prevent Start Bot popup on Telegram client
    idle_message_id = send_mdv2_message(call.message.chat.id, Strings.IDLE_MESSAGE)
    delete_past_messages(user_id, past_message_ids)

    utils.add_user_message_id(user_id, idle_message_id)


@bot.callback_query_handler(func=lambda call: (
    call.data in ['add', 'remove', 'show'] and
    utils.get_user_state(call.from_user.id) == UserState.ADMIN_MENU
))
def callback_admin_operations(call: telebot.types.CallbackQuery) -> None:
    """
    Handles the admin operations: add, remove, and show whitelisted users.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    user_id = call.from_user.id
    user_ids = db.get_whitelisted_user_ids()
    is_user_ids_empty = len(user_ids) == 0

    if call.data == 'add':
        bot.answer_callback_query(call.id, 'Adding user to whitelist...')
        utils.set_user_state(user_id, UserState.ADD_WHITELIST_USER)

        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(Strings.ADD_WHITELIST_USER_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    elif call.data == 'remove':
        bot.answer_callback_query(call.id, 'Removing user from whitelist...')
        utils.set_user_state(user_id, UserState.REMOVE_WHITELIST_USER)

        remove_user_message_text = Strings.REMOVE_WHITELIST_USER_HEADER
        if is_user_ids_empty:
            remove_user_message_text += 'No whitelisted users at the moment.'
        else:
            remove_user_message_text += 'Select a user to remove from the whitelist.'
        remove_user_message_text += Strings.NAVIGATION_FOOTER
        remove_user_message_text = utils.convert_to_mdv2(remove_user_message_text)

        markup = utils.admin_remove_whitelist_user_inline_keyboard()
        edit_mdv2_message(remove_user_message_text,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    elif call.data == 'show':
        bot.answer_callback_query(call.id, 'Showing whitelist...')
        utils.set_user_state(user_id, UserState.SHOW_WHITELIST_USERS)

        if is_user_ids_empty:
            markup = utils.back_quit_inline_keyboard()
            edit_mdv2_message(Strings.NO_WHITELIST_USERS_TO_SHOW_MESSAGE,
                              call.message.chat.id,
                              call.message.id,
                              reply_markup=markup)
        else:
            show_whitelist_message_text = Strings.SHOW_WHITELIST_USERS_HEADER
            for user_id in user_ids:
                user_id = user_id[0]        # DB results are returned as tuples
                show_whitelist_message_text += f'{user_id}\n'
            show_whitelist_message_text += ('\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-' +
                                            Strings.NAVIGATION_FOOTER)
            show_whitelist_message_text = utils.convert_to_mdv2(show_whitelist_message_text)
            
            markup = utils.back_quit_inline_keyboard()
            edit_mdv2_message(show_whitelist_message_text,
                              call.message.chat.id,
                              call.message.id,
                              reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data.isdigit() and
    utils.get_user_state(call.from_user.id) == UserState.REMOVE_WHITELIST_USER
))
def callback_remove_whitelist_user(call: telebot.types.CallbackQuery) -> None:
    """
    Handles the removal of a whitelisted user.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    admin_user_id = call.from_user.id
    user_id_to_remove = call.data
    utils.set_user_temp_data(admin_user_id, {'user_id_to_remove': user_id_to_remove})
    
    confirmation_message_text = Strings.REMOVE_WHITELIST_USER_HEADER + f'Permanently remove user _{user_id_to_remove}_?'
    confirmation_message_text = utils.convert_to_mdv2(confirmation_message_text)
    markup = utils.confirmation_inline_keyboard()
    edit_mdv2_message(confirmation_message_text,
                      call.message.chat.id,
                      call.message.id,
                      reply_markup=markup)


@bot.callback_query_handler(func=lambda call: (
    call.data in ('yes', 'no') and 
    utils.get_user_state(call.from_user.id) == UserState.REMOVE_WHITELIST_USER
))
def callback_remove_whitelist_user_confirmation(call: telebot.types.CallbackQuery) -> None:
    """
    Handles the confirmation to remove a whitelisted user.

    Args:
        call: The callback query sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(call.from_user.id, time.time())

    user_id_to_remove = utils.get_user_temp_data(call.from_user.id).get('user_id_to_remove', None)

    # Error checking
    if user_id_to_remove is None:
        bot.answer_callback_query(call.id, 'Error removing user from whitelist.')
        error_message_text = Strings.ERROR_HEADER + 'Error removing user from whitelist. Please try again.'
        error_message_text = utils.convert_to_mdv2(error_message_text)
        error_message_id = send_mdv2_message(call.message.chat.id, error_message_text)
        utils.add_user_message_id(call.from_user.id, error_message_id)
        return

    if call.data == 'yes':
        db.remove_whitelist_user(user_id_to_remove)
        bot.answer_callback_query(call.id, f'Removed user {user_id_to_remove} from whitelist.')
    elif call.data == 'no':
        bot.answer_callback_query(call.id, 'Removal canceled.')

    utils.set_user_temp_data(call.from_user.id, None)

    whitelist_users = db.get_whitelisted_user_ids()
    is_whitelist_users_empty = len(whitelist_users) == 0

    # Return to remove whitelist user menu
    if is_whitelist_users_empty:
        markup = utils.back_quit_inline_keyboard()
        edit_mdv2_message(Strings.NO_WHITELIST_USERS_TO_REMOVE_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)
    else:
        markup = utils.admin_remove_whitelist_user_inline_keyboard()
        edit_mdv2_message(Strings.REMOVE_WHITELIST_USER_MESSAGE,
                          call.message.chat.id,
                          call.message.id,
                          reply_markup=markup)


@bot.message_handler(func=lambda message: utils.get_user_state(message.from_user.id) == UserState.ADD_WHITELIST_USER)
def add_whitelist_user_handler(message: telebot.types.Message) -> None:
    """
    Handles the addition of a user to the whitelist.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    utils.add_user_message_id(message.from_user.id, message.id)

    user_id = message.from_user.id
    new_user_id = message.text

    try:
        new_user_id = int(new_user_id)
    except ValueError:
        sent_message_id = send_mdv2_message(message.chat.id, Strings.INVALID_USER_ID_ERROR)
        utils.add_user_message_id(user_id, sent_message_id)
        return

    db.add_whitelist_user(new_user_id)
    logger.info(f'Successfully added user {new_user_id} to the whitelist.')

    add_user_success_text = Strings.ADD_WHITELIST_USER_HEADER + f'Successfully added user _{new_user_id}_ to the whitelist.'
    add_user_success_text = utils.convert_to_mdv2(add_user_success_text)
    markup = utils.back_quit_inline_keyboard()

    past_message_ids = utils.get_user_message_ids(user_id)
    delete_past_messages(user_id, past_message_ids)
    utils.set_user_conversation_id(user_id, None)

    sent_message_id = send_mdv2_message(message.chat.id, add_user_success_text, reply_markup=markup)
    utils.add_user_message_id(user_id, sent_message_id)


##################################################
# Commands handler
@bot.message_handler(func=lambda message: telebot.util.is_command(message.text))
def commands_handler(message: telebot.types.Message) -> None:
    """
    Handles all commands sent by the user.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    utils.set_user_last_activity(message.from_user.id, time.time())

    # Admin user does not have to be whitelisted
    if message.text == '/admin':
        admin_command_handler(message)
        return

    # Check if the user is whitelisted
    if not utils.verify_user(message.from_user.id):
        send_mdv2_message(message.chat.id, Strings.NOT_WHITELISTED_ERROR)
        return

    if message.text == '/start':
        start_command_handler(message)
    elif message.text == '/quit':
        quit_command_handler(message)
    else:
        utils.add_user_message_id(message.from_user.id, message.id)
        error_message_id = send_mdv2_message(message.chat.id, Strings.INVALID_COMMAND_ERROR)
        utils.add_user_message_id(message.from_user.id, error_message_id)


def start_command_handler(message: telebot.types.Message) -> None:
    """
    Handles the /start command. Initializes the user's state and conversation ID.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    
    logger.info(f'Received /start command from user {user_id}.')

    # Delete past messages
    past_message_ids = utils.get_user_message_ids(user_id)
    delete_past_messages(user_id, past_message_ids)

    utils.add_user_message_id(user_id, message.id)

    indicator_message_id = send_mdv2_message(chat_id, 'Loading...', disable_notification=True)

    db.add_user(user_id, username)
    utils.set_user_state(user_id, UserState.MAIN_MENU)

    # Create inline keyboard for main menu
    markup = utils.main_menu_inline_keyboard()

    bot.delete_message(message.chat.id, indicator_message_id)

    start_message_id = send_mdv2_message(chat_id, Strings.MAIN_MENU_MESSAGE, reply_markup=markup)
    utils.add_user_message_id(user_id, start_message_id)


def quit_command_handler(message: telebot.types.Message) -> None:
    """
    Handles the /quit command. Allows the user to quit the bot.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    logger.info(f'Received /quit command from user {user_id}.')

    utils.set_user_state(user_id, UserState.IDLE)
    utils.set_user_conversation_id(user_id, None)

    past_messages_id = utils.get_user_message_ids(user_id)
    delete_past_messages(user_id, past_messages_id)

    utils.add_user_message_id(user_id, message.id)

    idle_message_id = send_mdv2_message(chat_id, Strings.IDLE_MESSAGE)
    utils.add_user_message_id(user_id, idle_message_id)


def admin_command_handler(message: telebot.types.Message) -> None:
    """
    Handles the /admin command. Provides options to add or remove whitelist users.

    Args:
        message (telebot.types.Message): The message sent by the user.

    Returns:
        None
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    logger.info(f'Received /admin command from user {user_id}.')

    utils.add_user_message_id(user_id, message.id)

    # Check if the user is the admin
    ADMIN_ID = int(getenv('ADMIN_ID'))
    if message.from_user.id != ADMIN_ID:
        logger.info(f'User {user_id} attempted to use admin commands without permission.')
        error_message_id = send_mdv2_message(chat_id, Strings.NOT_ADMIN_ERROR)
        utils.add_user_message_id(user_id, error_message_id)
        return

    # Check if the user is in the idle state
    if utils.get_user_state(user_id) != UserState.IDLE:
        error_message_id = send_mdv2_message(chat_id, Strings.ADMIN_NOT_IDLE_ERROR)
        utils.add_user_message_id(user_id, error_message_id)
        return

    utils.set_user_state(user_id, UserState.ADMIN_MENU)

    markup = utils.admin_menu_inline_keyboard()
    admin_message_id = send_mdv2_message(chat_id, Strings.ADMIN_MENU_MESSAGE, reply_markup=markup)
    utils.add_user_message_id(user_id, admin_message_id)
