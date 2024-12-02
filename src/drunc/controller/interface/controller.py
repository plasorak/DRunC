from concurrent import futures
import click
import grpc
import os
from logging import getLogger
import signal
from rich.console import Console

from druncschema.controller_pb2_grpc import add_ControllerServicer_to_server
from druncschema.token_pb2 import Token

from drunc.controller.controller import Controller
from drunc.utils.configuration import parse_conf_url, OKSKey
from drunc.utils.utils import print_traceback, resolve_localhost_and_127_ip_to_network_ip, log_levels,  update_log_level, validate_command_facility, log_levels, setup_logger, validate_command_facility

@click.command()
@click.argument('configuration', type=str)
@click.argument('command-facility', type=str, callback=validate_command_facility)#, help=f'Command facility (protocol, host and port) grpc://{socket.gethostname()}:12345')
@click.argument('name', type=str)
@click.argument('session', type=str)
@click.option('-l', '--log-level', type=click.Choice(log_levels.keys(), case_sensitive=False), default='INFO', help='Set the log level')
def controller_cli(configuration:str, command_facility:str, name:str, session:str, log_level:str):

    console = Console()

    setup_logger(log_level)
    log = getLogger('controller_cli')

    token = Token(
        user_name = "controller_init_token",
        token = '',
    )

    ctrlr = Controller(
        name = name,
        session = session,
        configuration = configuration,
        token = token,
    )

    def serve(listen_addr:str) -> None:

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))

        add_ControllerServicer_to_server(ctrlr, server)
        port = server.add_insecure_port(listen_addr)

        server.start()
        log.info(f'\'{ctrlr.name}\' was started on \'{port}\'')
        return server, port

    def controller_shutdown():
        console.print('Requested termination')
        ctrlr.terminate()

    def kill_me(sig, frame):
        l = getLogger("drunc.controller.interface.controller.kill_me")
        l.info('Sending SIGKILL')
        pgrp = os.getpgid(os.getpid())
        os.killpg(pgrp, signal.SIGKILL)

    def shutdown(sig, frame):
        l = getLogger("drunc.controller.interface.controller.shutdown")
        l.info('Shutting down gracefully')
        try:
            controller_shutdown()
        except:
            print_traceback()
            kill_me(sig, frame)

    signal.signal(signal.SIGHUP, kill_me)
    signal.signal(signal.SIGINT, shutdown)

    try:
        command_facility = resolve_localhost_and_127_ip_to_network_ip(command_facility)
        server_name = command_facility.split(':')[0]
        server, port = serve(command_facility)

        ctrlr.advertise_control_address(f'grpc://{server_name}:{port}')

        server.wait_for_termination(timeout=None)

    except Exception as e:
        print_traceback()


