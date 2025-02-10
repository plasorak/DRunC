import asyncio
from click import BadParameter
from contextlib import closing
import ctypes
from datetime import datetime
from enum import Enum
from functools import wraps
import logging
import kafka
import os
import random
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.logging import RichHandler
from rich.console import Console
import re
from requests import delete, get, patch, post
import sh
import signal
import socket
import string
import sys
import time
from urllib.parse import urlparse

from drunc.connectivity_service.exceptions import ApplicationLookupUnsuccessful
from drunc.exceptions import DruncException, DruncSetupException


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

def setup_root_logger(stream_log_level:str) -> None:
    if stream_log_level not in log_levels.keys():
        raise DruncSetupException(f"Unrecognised log level, should be one of {log_levels.keys()}.")

    root_logger = logging.getLogger('drunc')
    if "drunc" in logging.Logger.manager.loggerDict:
        if root_logger.level == log_levels["NOTSET"]:
            root_logger.setLevel(stream_log_level)
            root_logger.debug(f"logger level updated from 'NOTSET' to '{stream_log_level}'")
        root_logger.debug("'drunc' logger already exists, skipping setup")
        return

    stream_log_level = log_levels[stream_log_level]
    root_logger.setLevel(stream_log_level)
    for handler in root_logger.handlers:
        handler.setLevel(stream_log_level)

    # And then manually tweak 'sh.command' logger. Sigh.
    sh_command_level = stream_log_level if stream_log_level > logging.INFO else (stream_log_level+10)
    sh_command_logger = logging.getLogger(sh.__name__)
    sh_command_logger.setLevel(sh_command_level)
    for handler in sh_command_logger.handlers:
        handler.setLevel(sh_command_level)

    # And kafka
    kafka_command_level = stream_log_level if stream_log_level > logging.INFO else (stream_log_level+10)
    kafka_command_logger = logging.getLogger(kafka.__name__)
    kafka_command_logger.setLevel(kafka_command_level)
    for handler in kafka_command_logger.handlers:
        handler.setLevel(kafka_command_level)

def get_logger(logger_name:str, log_file_path:str = None, override_log_file:bool = False, rich_handler:bool = False):
    if logger_name == "":
        raise DruncSetupException("This was an attempt to set up the root logger `drunc`, need to run `setup_root_logger` first.")
    if "drunc" not in logging.Logger.manager.loggerDict:
        raise DruncSetupException("The root logger has not been initialized, exiting.")
    if logger_name.split(".")[0] == "drunc":
        raise DruncSetupException(f"get_logger adds the root logger prefix, it is not required for {logger_name}")
    if logger_name == "process_manager" and not 'drunc.process_manager' in logging.Logger.manager.loggerDict:
        if not log_file_path:
            raise DruncSetupException("process_manager setup requires a log path.")
        if not rich_handler:
            raise DruncSetupException("process_manager requires a rich handler.")
    if logger_name.count(".") > 1:
        raise DruncSetupException(f"Logger {logger_name} has a larger inheritance structure than allowed.")
    if logger_name.count(".") == 1 and not ("drunc." + logger_name.split(".")[0]) in logging.Logger.manager.loggerDict:
        get_logger(logger_name.split(".")[0], log_file_path, override_log_file, rich_handler)

    logger_level = logging.getLogger('drunc').level

    # If the log level is not set, update the log level of the logger and its handlers, but do not overwrite.
    logger_name = 'drunc.' + logger_name
    logger = logging.getLogger(logger_name)
    logger.debug(f"Setting up logger {logger_name}")
    if logger_name in logging.Logger.manager.loggerDict:
        logger.debug(f"Logger {logger_name} already exists!")
        if logger.level == log_levels["NOTSET"]:
            logger.debug(f"Updating {logger_name} level and handlers' levels to {list(log_levels.keys())[list(log_levels.values()).index(logger_level)]}, matching the root logger")
            logger.setLevel(logger_level)
            for handler in logger.handlers:
                handler.setLevel(logger_level)
            logger.debug(f"Updated {logger_name} level and handlers")
            logger.debug(f"Logger {logger_name} has level {logger.level} and handlers {logger.handlers}")
        else:
            logger.debug(f"Logger {logger_name} already exists and is set, not overwriting handlers")
            return logger

    if override_log_file and log_file_path and os.path.isfile(log_file_path):
        os.remove(log_file_path)

    logger.setLevel(logger_level)

    if log_file_path:
        fileHandler = logging.FileHandler(filename = log_file_path)
        fileHandler.setLevel(logger_level)
        fileHandler.setFormatter(_get_stream_logging_format())
        logger.addHandler(fileHandler)
        logger.debug(f"Added file handler to {logger_name}")

    if any(isinstance(handler, RichHandler) for handler in [*logger.handlers, *logger.parent.handlers]):
        logger.debug(f"Logger {logger_name} already has an associated and usable RichHandler, skipping it")
        stdHandler = None
    elif rich_handler:
        logger.debug(f"Assigning a RichHandler to logger {logger_name}")
        try:
            width = os.get_terminal_size()[0]
        except:
            width = 150
        stdHandler = RichHandler(
            console=Console(width=width),
            rich_tracebacks=True,
            show_path=False,
            tracebacks_width=width,
            markup=True
        )
        stdHandler.setFormatter(_get_rich_logging_format())
    elif any(isinstance(handler, logging.StreamHandler) for handler in [*logger.handlers, *logger.parent.handlers]):
        logger.debug(f"Logger {logger_name} already has an associated and usable StreamHandler, skipping it")
        stdHandler = None
    else:
        logger.debug(f"Assigning a StreamHandler to logger {logger_name}")
        stdHandler = logging.StreamHandler()
        stdHandler.setFormatter(_get_stream_logging_format())

    if stdHandler:
        stdHandler.setLevel(logger_level)
        logger.addHandler(stdHandler)
        logger.debug(f"Added appropriate stream handler to {logger_name}")

    logger.debug(f"Finished setting up logger {logger_name}")
    return logger

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def regex_match(regex, string):
    return re.match(regex, string) is not None

def print_traceback(with_rich:bool=True): # RETURNTOME - rename to print_console_traceback
    if with_rich: # Try running this line without the if with_rich, get the exception
        c = Console()
        try:
            width = os.get_terminal_size()[0]
        except:
            width = 300
        c.print_exception(width=width)
    # else: # RETURNTOME
    #     import sys
    #     sys.traceback # FIX THISNOW


def _get_stream_logging_format():
    return logging.Formatter(
        fmt = "%(asctime)s\t%(levelname)s\t%(filename)s:%(lineno)i\t%(name)s:\t%(message)s",
        datefmt = "[%X]",
        validate = True
    )
def _get_rich_logging_format():
    return logging.Formatter(
        fmt = "%(asctime)s\t%(filename)s:%(lineno)i\t%(name)s:\t%(message)s", # For production, remove the filename and lineno
        datefmt = "[%X]",
        validate = True
    )

def get_new_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def now_str(posix_friendly=False):
    if not posix_friendly:
        return datetime.now().strftime("%m/%d/%Y,%H:%M:%S")
    else:
        return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def run_coroutine(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()

        ret = None

        main_task = asyncio.ensure_future(f(*args, **kwargs))
        wanna_catch_during_command = [signal.SIGINT]

        for sig in wanna_catch_during_command:
            loop.add_signal_handler(sig, main_task.cancel)

        try:
            ret = loop.run_until_complete(main_task)
        except asyncio.exceptions.CancelledError as e:
            print("Command cancelled")
        finally:
            for sig in wanna_catch_during_command:
                loop.remove_signal_handler(sig)

        if ret:
            return ret

    return wrapper


def expand_path(path, turn_to_abs_path=False):
    if turn_to_abs_path:
        return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
    return os.path.expanduser(os.path.expandvars(path))


def validate_command_facility(ctx, param, value):
    parsed = ''
    try:
        parsed = urlparse(value)
    except Exception as e:
        raise BadParameter(message=str(e), ctx=ctx, param=param)

    if parsed.path or parsed.params or parsed.query or parsed.fragment:
        raise BadParameter(message=f'Command factory for drunc-controller is not understood', ctx=ctx, param=param)

    match parsed.scheme:
        case 'grpc':
            return str(parsed.netloc)
        case _:
            raise BadParameter(message=f'Command factory for drunc-controller only allows \'grpc\'', ctx=ctx, param=param)


def resolve_localhost_to_hostname(address):
    if not address:
        return None
    hostname = socket.gethostname()
    if 'localhost' in address:
        address = address.replace('localhost', hostname)

    ip_match = re.search(
        "((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",
        address
    )
    # https://stackoverflow.com/a/25969006

    if not ip_match:
        return address

    if ip_match.group(0).startswith('127.'):
        address = address.replace(ip_match.group(0), hostname)

    if ip_match.group(0).startswith('0.'):
        address = address.replace(ip_match.group(0), hostname)

    return address


def resolve_localhost_and_127_ip_to_network_ip(address):
    this_ip = socket.gethostbyname(socket.gethostname())
    if 'localhost' in address:
        address = address.replace('localhost', this_ip)

    ip_match = re.search(
        "((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",
        address
    )
    # https://stackoverflow.com/a/25969006

    if not ip_match:
        return address

    if ip_match.group(0).startswith('127.'):
        address = address.replace(ip_match.group(0), this_ip)

    if ip_match.group(0).startswith('0.'):
        address = address.replace(ip_match.group(0), this_ip)

    return address

def host_is_local(host):
    if host in ['localhost', socket.gethostname(), socket.gethostbyname(socket.gethostname())]:
        return True

    if host.startswith('127.') or host.startswith('0.'):
        return True

    return False

def pid_info_str():
    return f'Parent\'s PID: {os.getppid()} | This PID: {os.getpid()}'

def ignore_sigint_sighandler():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def parent_death_pact(signal=signal.SIGHUP):
    """
    Commit to kill current process when parent process dies.
    Each time you spawn a new process, run this to set signal
    handler appropriately (e.g put it at the beginning of each
    script, and in multiprocessing startup code).
    """
    assert sys.platform == 'linux', \
        "this fn only works on Linux right now"
    libc = ctypes.CDLL("libc.so.6")
    # see include/uapi/linux/prctl.h in kernel
    PR_SET_PDEATHSIG = 1
    # last three args are unused for PR_SET_PDEATHSIG
    retcode = libc.prctl(PR_SET_PDEATHSIG, signal, 0, 0, 0)
    if retcode != 0:
        raise Exception("prctl() returned nonzero retcode %d" % retcode)

class IncorrectAddress(DruncException):
    pass

def https_or_http_present(address:str):
    if not address.startswith('https://') and not address.startswith('http://'):
        raise IncorrectAddress('Endpoint should start with http:// or https://')


def http_post(address, data, as_json=True, ignore_errors=False, **post_kwargs):
    https_or_http_present(address)
    if as_json:
        r = post(address, json=data, **post_kwargs)
    else:
        r = post(address, data=data, **post_kwargs)

    if not ignore_errors:
        r.raise_for_status()
    return r

def http_get(address, data, as_json=True, ignore_errors=False, **post_kwargs):
    https_or_http_present(address)

    log = get_logger("utils.http_get")

    log.debug(f"GETTING {address} {data}")
    if as_json:
        r = get(address, json=data, **post_kwargs)
    else:
        r = get(address, data=data, **post_kwargs)

    log.debug(r.text)
    log.debug(r.status_code)

    if not ignore_errors:
        log.error(r.text)
        r.raise_for_status()
    return r


def http_patch(address, data, as_json=True, ignore_errors=False, **post_kwargs):
    https_or_http_present(address)

    if as_json:
        r = patch(address, json=data, **post_kwargs)
    else:
        r = patch(address, data=data, **post_kwargs)

    if not ignore_errors:
        r.raise_for_status()
    return r


def http_delete(address, data, as_json=True, ignore_errors=False, **post_kwargs):
    https_or_http_present(address)

    if as_json:
        r = delete(address, json=data, **post_kwargs)
    else:
        r = delete(address, data=data, **post_kwargs)

    if not ignore_errors:
        r.raise_for_status()

class ControlType(Enum):
    Unknown = 0
    gRPC = 1
    REST_API = 2
    Direct = 3


def get_control_type_and_uri_from_cli(CLAs:list[str]) -> ControlType:
    for CLA in CLAs:
        if   CLA.startswith("rest://"): return ControlType.REST_API, resolve_localhost_and_127_ip_to_network_ip(CLA.replace("rest://", ""))
        elif CLA.startswith("grpc://"): return ControlType.gRPC, resolve_localhost_and_127_ip_to_network_ip(CLA.replace("grpc://", ""))
    raise DruncSetupException("Could not find if the child was controlled by gRPC or a REST API")


from drunc.connectivity_service.client import ConnectivityServiceClient
def get_control_type_and_uri_from_connectivity_service(
    connectivity_service:ConnectivityServiceClient,
    name:str,
    timeout:int=10, # seconds
    retry_wait:float=0.1, # seconds
    progress_bar:bool=False,
    title:str=None,
) -> tuple[ControlType, str]:

    uris = []
    logger = get_logger('utils.get_control_type_and_uri_from_connectivity_service')

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn()
    ) as progress:

        task = progress.add_task(f'[yellow]{title}', total=timeout, visible=progress_bar)
        start = time.time()

        while time.time() - start < timeout:
            progress.update(task, completed=time.time() - start)

            try:
                uris = connectivity_service.resolve(name+'_control', 'RunControlMessage')
                if len(uris) == 0:
                    raise ApplicationLookupUnsuccessful
                else:
                    break

            except ApplicationLookupUnsuccessful as e:
                el = time.time() - start
                logger.debug(f"Could not resolve \'{name}_control\' elapsed {el:.2f}s/{timeout}s")
                time.sleep(retry_wait)



    if len(uris) != 1:
        raise ApplicationLookupUnsuccessful(f"Could not resolve the URI for \'{name}_control\' in the connectivity service, got response {uris}")

    uri = uris[0]['uri']

    return get_control_type_and_uri_from_cli([uri])