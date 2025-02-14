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
import pytz
import random
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.logging import RichHandler
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
full_log_format = "%(asctime)s %(levelname)s %(filename)s %(name)s %(message)s" #TODO: for production, remove the filename
rich_log_format = "%(filename)s %(name)s %(message)s" # TODO: for production, remove the filename
date_time_format = "[%Y/%m/%d %H:%M:%S]" # TODO: include timezone as %Z when the RichHandler starts supporting it in the tty. If this is desired, a custom handler can be written that looks like the rich handler
time_zone = pytz.utc

class LoggingFormatter(logging.Formatter):
    def __init__(self, fmt=full_log_format, datefmt=date_time_format, tz=time_zone):
        super().__init__(fmt, datefmt)
        self.tz = tz
        self.datefmt = datefmt

    def formatTime(self, record, datefmt):
        date_time = datetime.fromtimestamp(record.created, self.tz)
        return date_time.strftime(self.datefmt)

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        #TODO: for production, remove filename and lineno entries
        component_width = 30 
        file_lineno = f"{record.filename}:{record.lineno}"
        record.filename = file_lineno.ljust(component_width)[:component_width]
        component_width = 45
        name_colon = f"{record.name}:"
        record.name = name_colon.ljust(component_width)[:component_width]
        component_width = 10
        level_name = record.levelname
        record.levelname = level_name.ljust(component_width)[:component_width]
        return super().format(record)

def root_logger_is_setup(log_level:int) -> bool:
    if "drunc" in logging.Logger.manager.loggerDict:
        root_logger = logging.getLogger("drunc")
        root_logger.debug("Root logger is already setup, not setting it up again")
        if root_logger.level == log_levels["NOTSET"] and log_level != "NOTSET":
            root_logger.setLevel(log_level)
            for handler in root_logger.handlers:
                handler.setLevel(log_level)
            root_logger.debug(f'Root logger level updated from "NOTSET" to {logging.getLevelName(log_level)}')
        return True
    return False

def setup_root_logger(log_level:str) -> None:
    log_level = log_level.upper()
    if log_level not in log_levels.keys():
        raise DruncSetupException(f"Unrecognised log level, should be one of {log_levels.keys()}")
    log_level = log_levels[log_level]

    if root_logger_is_setup(log_level):
        return

    root_logger = logging.getLogger("drunc")
    root_logger.debug('Setting up root logger "drunc"')
    root_logger.setLevel(log_level)

    # And then manually tweak 'sh.command' logger. Sigh.
    sh_command_level = log_level if log_level > logging.INFO else (log_level+10)
    sh_command_logger = logging.getLogger("drunc." + sh.__name__) # Not get_logger as the root logger is initially "UNSET" at context declaration
    sh_command_logger.setLevel(sh_command_level)
    for handler in sh_command_logger.handlers:
        handler.setLevel(sh_command_level)

    # And kafka
    kafka_command_level = log_level if log_level > logging.INFO else (log_level+10)
    kafka_command_logger = logging.getLogger("drunc." + kafka.__name__) # Not get_logger as the root logger is initially "UNSET" at context declaration
    kafka_command_logger.setLevel(kafka_command_level)
    for handler in kafka_command_logger.handlers:
        handler.setLevel(kafka_command_level)

def get_logger(logger_name:str, log_file_path:str = None, override_log_file:bool = False, rich_handler:bool = False):
    logger_dict = logging.Logger.manager.loggerDict
    if "drunc" not in logger_dict:
        raise DruncSetupException("Required root logger 'drunc' has not been initialized")
    if logger_name == "":
        raise DruncSetupException("This was an attempt to set up the root logger `drunc`, need to run `setup_root_logger` first.")
    if logger_name.split(".")[0] == "drunc":
        raise DruncSetupException(f"get_logger adds the root logger prefix, it is not required for {logger_name}")
    if override_log_file and not log_file_path:
        raise DruncSetupException("Configuration error - a log_file_path must be provided if it is to be overwritten")
    if logger_name.count(".") > 2:
        raise DruncSetupException(f"Logger {logger_name} has a larger inheritance structure than allowed.")
    if logger_name == "process_manager" and 'drunc.process_manager' not in logger_dict:
        if not log_file_path:
            raise DruncSetupException("process_manager logger setup requires a log path.")
        if not rich_handler:
            raise DruncSetupException("process_manager logger requires a rich handler.")

    function_logger = logging.getLogger("utils.get_logger")
    if ("drunc." + logger_name) in logger_dict:
        function_logger.debug("This logger has already been set up, returning the original")
        logger = logging.getLogger("drunc." + logger_name)
        return logger
    if logger_name.count(".") == 2 and ("drunc." + logger_name.split(".")[0]) not in logger_dict:
        function_logger.debug(f"Parent of logger {logger_name} (drunc.{logger_name.split('.')[0]}) not set up yet, setting it up now")
        get_logger(logger_name.split(".")[0], log_file_path, override_log_file, rich_handler)

    logger_level = logging.getLogger("drunc").level
    if not logger_level:
        raise DruncSetupException(f"Root logger level not set (found level {logging.getLevelName(logger_level)})")

    logger_name = 'drunc.' + logger_name
    logger = logging.getLogger(logger_name)

    if override_log_file and os.path.isfile(log_file_path):
        os.remove(log_file_path)
        function_logger.debug(f"Removed existing log file at {log_file_path}")
    if log_file_path:
        fileHandler = logging.FileHandler(filename = log_file_path)
        fileHandler.setLevel(logger_level)
        fileHandler.setFormatter(LoggingFormatter())
        logger.addHandler(fileHandler)
        function_logger.debug(f"Added file handler to {logger_name}")

    if any(isinstance(handler, RichHandler) for handler in [*logger.handlers, *logger.parent.handlers]):
        function_logger.debug(f"Logger {logger_name} already has an associated and usable RichHandler, skipping it")
        stdHandler = None
    elif rich_handler:
        function_logger.debug(f"Assigning a RichHandler to logger {logger_name}")
        try:
            width = os.get_terminal_size()[0]
        except:
            width = 150
        stdHandler = RichHandler(
            console=Console(width=width),
            omit_repeated_times=False,
            markup=True,
            rich_tracebacks=True,
            show_path=False,
            tracebacks_width=width
        )
        stdHandler.setFormatter(LoggingFormatter(fmt=rich_log_format))
    elif any(isinstance(handler, logging.StreamHandler) for handler in [*logger.handlers, *logger.parent.handlers]):
        function_logger.debug(f"Logger {logger_name} already has an associated and usable StreamHandler, skipping it")
        stdHandler = None
    else:
        function_logger.debug(f"Assigning a StreamHandler to logger {logger_name}")
        stdHandler = logging.StreamHandler()
        stdHandler.setFormatter(LoggingFormatter())

    if stdHandler:
        stdHandler.setLevel(logger_level)
        logger.addHandler(stdHandler)
        function_logger.debug(f"Added appropriate stream handler to {logger_name}")

    function_logger.debug(f"Finished setting up logger {logger_name}")
    return logger

def setup_standard_loggers() -> None:
    get_logger(
        logger_name="utils",
        rich_handler=True
    )

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def regex_match(regex, string):
    return re.match(regex, string) is not None

def print_traceback(e): # RETURNTOME - rename to print_console_traceback
    log = get_logger(
        logger_name="utils.traceback",
        rich_handler=True
    )
    log.exception(e)

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
        except asyncio.exceptions.CancelledError:
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
        raise BadParameter(message='Command factory for drunc-controller is not understood', ctx=ctx, param=param)

    match parsed.scheme:
        case 'grpc':
            return str(parsed.netloc)
        case _:
            raise BadParameter(message='Command factory for drunc-controller only allows \'grpc\'', ctx=ctx, param=param)


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

    start = time.time()
    elapsed = 0

    if progress_bar:
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn()
        ) as progress:

            task = progress.add_task(f'[yellow]{title}', total=timeout, visible=progress_bar)

            while elapsed < timeout:
                progress.update(task, completed=elapsed)

                try:
                    uris = connectivity_service.resolve(name+'_control', 'RunControlMessage')
                    if len(uris) == 0:
                        raise ApplicationLookupUnsuccessful
                    else:
                        break

                except ApplicationLookupUnsuccessful:
                    elapsed = time.time() - start
                    logger.debug(f"Could not resolve \'{name}_control\' elapsed {elapsed:.2f}s/{timeout}s")
                    time.sleep(retry_wait)

            progress.update(task, completed=timeout)

    else:
        while elapsed < timeout:
            try:
                uris = connectivity_service.resolve(name+'_control', 'RunControlMessage')
                if len(uris) == 0:
                    raise ApplicationLookupUnsuccessful
                else:
                    break

            except ApplicationLookupUnsuccessful:
                elapsed = time.time() - start
                logger.debug(f"Could not resolve \'{name}_control\' elapsed {elapsed:.2f}s/{timeout}s")
                time.sleep(retry_wait)
                


    if len(uris) != 1:
        raise ApplicationLookupUnsuccessful(f"Could not resolve the URI for \'{name}_control\' in the connectivity service, got response {uris}")

    uri = uris[0]['uri']

    return get_control_type_and_uri_from_cli([uri])