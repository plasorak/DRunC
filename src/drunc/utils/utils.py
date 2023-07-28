import logging
from rich.theme import Theme

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
CONSOLE_THEMES = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})
log_levels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR'   : logging.ERROR,
    'WARNING' : logging.WARNING,
    'INFO'    : logging.INFO,
    'DEBUG'   : logging.DEBUG,
    'NOTSET'  : logging.NOTSET,
}


def regex_match(regex, string):
    import re
    return re.match(regex, string) is not None

log_level = logging.INFO

def update_log_level(loglevel):
    log_level = log_levels[loglevel]
    #logging.basicConfig(level=log_level)
    # Update log level for root logger
    logger = logging.getLogger('drunc')
    logger.setLevel(log_level)
    for handler in logger.handlers:
        handler.setLevel(log_level)

    # And then manually tweak 'sh.command' logger. Sigh.
    sh_command_level = log_level if log_level > logging.INFO else (log_level+10)
    import sh

    sh_command_logger = logging.getLogger(sh.__name__)
    sh_command_logger.setLevel(sh_command_level)
    for handler in sh_command_logger.handlers:
        handler.setLevel(sh_command_level)

    # And kafka
    kafka_command_level = log_level if log_level > logging.INFO else (log_level+10)
    import kafka
    kafka_command_logger = logging.getLogger(kafka.__name__)
    kafka_command_logger.setLevel(kafka_command_level)
    for handler in kafka_command_logger.handlers:
        handler.setLevel(kafka_command_level)

    from rich.logging import RichHandler

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            #logging.StreamHandler(),
            RichHandler(rich_tracebacks=False) # Make this True, and everything crashes on exceptions (no clue why)
        ]
    )

def get_new_port():
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]


def now_str(posix_friendly=False):
    from datetime import datetime
    if not posix_friendly:
        return datetime.now().strftime("%m/%d/%Y,%H:%M:%S")
    else:
        return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
