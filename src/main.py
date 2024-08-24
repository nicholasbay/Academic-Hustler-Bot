# This file is the main file that runs the bot.
import logging
from threading import Thread

from bot_core.bot_logic import bot, check_inactivity
from bot_core.gpt_client import initialize_gpt_client
from bot_core.utils import initialize_users_data
from config.logging_config import setup_logging
from database.models import initialize_db


def main() -> None:
    """
    Main function that initializes the bot and runs it.

    Args:
        None

    Returns:
        None
    """
    # Setup loggers
    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database, users' data, and GPT client
    initialize_db()
    initialize_users_data()
    initialize_gpt_client()

    # Bot is initialized in bot_logic

    # Start inactivity checker in separate thread
    inactivity_thread = Thread(target=check_inactivity, daemon=True)
    inactivity_thread.start()

    logger.info('Bot is currently running.')
    bot.infinity_polling(timeout=None, logger_level=None)


if __name__ == "__main__":
    main()
