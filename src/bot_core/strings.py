# Description: Strings used in the bot_core package

class Strings():
    # Headers
    TIMEOUT_HEADER = ('🤖 *Academic Hustler Bot* \| Timeout\n' +
                      '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    IDLE_HEADER = ('🤖 *Academic Hustler Bot* \| Idle\n' +
                   '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    MAIN_MENU_HEADER = ('🤖 *Academic Hustler Bot* \| Main Menu\n' +
                        '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    NEW_CONV_HEADER = ('🤖 *Academic Hustler Bot* \| New Conversation\n' + 
                       '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    LOAD_CONV_HEADER = ('🤖 *Academic Hustler Bot* \| Load Conversation\n' +
                        '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    EXTG_CONV_HEADER = ('🤖 *Academic Hustler Bot* \| Existing Conversation\n' +
                        '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    EDIT_CONV_HEADER = ('🤖 *Academic Hustler Bot* \| Edit Conversation\n' +
                        '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    DELETE_CONV_HEADER = ('🤖 *Academic Hustler Bot* \| Delete Conversation\n' +
                          '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    HELP_HEADER = ('🤖 *Academic Hustler Bot* \| Help\n' +
                   '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    ID_HEADER = ('🤖 *Academic Hustler Bot* \| User ID\n' +
                 '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    ERROR_HEADER = ('🤖 *Academic Hustler Bot* \| Error\n' +
                    '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    ADMIN_MENU_HEADER = ('🤖 *Academic Hustler Bot* \| Admin Menu\n' +
                         '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    ADD_WHITELIST_USER_HEADER = ('🤖 *Academic Hustler Bot* \| Add Whitelist User\n' +
                                 '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    REMOVE_WHITELIST_USER_HEADER = ('🤖 *Academic Hustler Bot* \| Remove Whitelist User\n' +
                                    '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    SHOW_WHITELIST_USERS_HEADER = ('🤖 *Academic Hustler Bot* \| Show Whitelist Users\n' +
                                   '\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n')

    USER_MESSAGE_HEADER = '👤 *User*:\n'

    BOT_MESSAGE_HEADER = '🤖 *Academic Hustler Bot*:\n'

    BOT_RESPONSE_HEADER = '🤖 *Academic Hustler Bot*:\n'

    # Footers
    NAVIGATION_FOOTER = '\n\nUse the inline keyboard provided to go back or quit\.'

    BOT_RESPONSE_FOOTER = ('\n\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\n' +
                           'Send a prompt to continue the conversation\.' +
                           NAVIGATION_FOOTER)

    # Messages
    TIMEOUT_MESSAGE = (TIMEOUT_HEADER +
                       'You have been inactive for too long\. Use */start* to begin\.')

    IDLE_MESSAGE = (IDLE_HEADER +
                    'You are currently idle\. Use */start* to begin\.')

    MAIN_MENU_MESSAGE = (MAIN_MENU_HEADER +
                         'Welcome to Academic Hustler Bot\! I am here to help you with your academic tasks\.\n\n' +
                         'Select any of the following options to get started\.')

    NEW_CONV_MESSAGE = (NEW_CONV_HEADER +
                        'Send a prompt to start the conversation\.' +
                        NAVIGATION_FOOTER)

    LOAD_CONV_MESSAGE = (LOAD_CONV_HEADER +
                         'Select a conversation to load from the list below\.' +
                         NAVIGATION_FOOTER)

    NO_CONV_TO_LOAD_MESSAGE = (LOAD_CONV_HEADER +
                               'No conversations to load\.' +
                               NAVIGATION_FOOTER)

    EXTG_CONV_MESSAGE = (EXTG_CONV_HEADER +
                        'Send a prompt to continue the conversation\.' +
                        NAVIGATION_FOOTER)

    EDIT_CONV_MESSAGE = (EDIT_CONV_HEADER + 
                         'Select a conversation to edit from the list below\.' +
                         NAVIGATION_FOOTER)
    
    NO_CONV_TO_EDIT_MESSAGE = (EDIT_CONV_HEADER +
                               'No conversations to edit\.' +
                               NAVIGATION_FOOTER)

    DELETE_CONV_MESSAGE = (DELETE_CONV_HEADER +
                           'Select a conversation to delete from the list below\.' +
                           NAVIGATION_FOOTER)

    NO_CONV_TO_DELETE_MESSAGE = (DELETE_CONV_HEADER +
                                 'No conversations to delete\.' +
                                 NAVIGATION_FOOTER)

    HELP_MESSAGE = (HELP_HEADER +
                    '/start \- Start the bot\.\n' +
                    '/quit \- Quit the bot\. Same functionality as the *👋 Quit* inline button\.' +
                    NAVIGATION_FOOTER)

    ADMIN_MENU_MESSAGE = (ADMIN_MENU_HEADER +
                          'Select an operation below to proceed\.' +
                          NAVIGATION_FOOTER)
    
    ADD_WHITELIST_USER_MESSAGE = (ADD_WHITELIST_USER_HEADER +
                                  'Send the user ID to whitelist\.' +
                                  NAVIGATION_FOOTER)
    
    REMOVE_WHITELIST_USER_MESSAGE = (REMOVE_WHITELIST_USER_HEADER +
                                     'Select a user to remove from the whitelist\.' +
                                     NAVIGATION_FOOTER)
    
    NO_WHITELIST_USERS_TO_REMOVE_MESSAGE = (REMOVE_WHITELIST_USER_HEADER +
                                            'No users in the whitelist to remove\.' +
                                            NAVIGATION_FOOTER)
    
    NO_WHITELIST_USERS_TO_SHOW_MESSAGE = (SHOW_WHITELIST_USERS_HEADER +
                                          'No users in the whitelist at the moment\.' +
                                          NAVIGATION_FOOTER)

    # Errors
    NOT_WHITELISTED_ERROR = ERROR_HEADER + 'You are not whitelisted to use this bot\.'

    INVALID_INPUT_ERROR = ERROR_HEADER + 'Invalid input\. Please use the inline keyboard provided\.'

    INVALID_COMMAND_ERROR = ERROR_HEADER + 'Invalid command\. Please refer to the menu for the available commands\.'

    INVALID_USER_ID_ERROR = ERROR_HEADER + 'Invalid user ID\. Please send a valid user ID \(numeric digits only\)\.'

    ADMIN_NOT_IDLE_ERROR = ERROR_HEADER + '*/admin* is only available in the idle state\.'

    NOT_ADMIN_ERROR = ERROR_HEADER + 'You do not have permission to use this command\.'