import logging
from logging.config import dictConfig
from os import getenv

from dotenv import load_dotenv


def setup_logging():
    load_dotenv()
    LOG_PATH = getenv('LOG_PATH')

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard'
            },
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': LOG_PATH,
                'when': 'midnight',
                'interval': 1,
                'backupCount': 3
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True
            }
        }
    }

    dictConfig(log_config)

    logger = logging.getLogger(__name__)
    logger.info('Successfully initialized logger.')

    return logger
