from enum import Enum


class UserState(Enum):
    IDLE = 0
    MAIN_MENU = 1
    NEW_CONV = 2
    LOAD_CONV = 3
    EDIT_CONV_0 = 4
    EDIT_CONV_1 = 5
    DELETE_CONV_0 = 6
    DELETE_CONV_1 = 7
    EXTG_CONV = 8
    ADMIN_MENU = 9
    ADD_WHITELIST_USER = 10
    REMOVE_WHITELIST_USER = 11
    SHOW_WHITELIST_USERS = 12
