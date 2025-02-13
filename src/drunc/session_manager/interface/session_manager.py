import click
from concurrent import futures
import grpc
from logging import getLogger, Logger

from druncschema.session_manager_pb2_grpc import add_SessionManagerServicer_to_server

from drunc.utils.utils import log_levels, print_traceback, setup_logger
from drunc.session_manager.configuration import SessionManagerConfHandler
from drunc.session_manager.session_manager import SessionManager


def serve(session_manager: SessionManager, address: str, logger: Logger) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_SessionManagerServicer_to_server(session_manager, server)
    port = server.add_insecure_port(address)
    server.start()
    logger.info(f"{session_manager.name} listening on {address}:{port}")


@click.command()
@click.option(
    '--log-level',
    type=click.Choice(list(log_levels.keys()), case_sensitive=False),
    default="INFO",
    help="Verbosity of the session manager logger.",
)
@click.option(
    '--log-path',
    type=str,
    default=None,
    help="Path of the session manager log file.",
)
def session_manager_cli(log_level: str, log_path: str):
    setup_logger(log_level, log_path)
    logger = getLogger("drunc.session_manager")

    # Load the configuration for the session manager.
    config = SessionManagerConfHandler()
    logger.info(f"Using '{config}' as the SessionManager configuration.")

    # Load the session manager.
    session_manager = SessionManager("session_manager", config)
    logger.info("Creating session manager.")

    try:
        # Start serving the session manager.
        serve(session_manager, "localhost", logger)
    except Exception as e:
        logger.error("Error whilst serving the session manager.")
        print_traceback()
