import asyncio
import click
import grpc
from logging import getLogger
import os
from rich.console import Console
import socket

from druncschema.process_manager_pb2_grpc import add_ProcessManagerServicer_to_server

from drunc.exceptions import DruncSetupException
from drunc.process_manager.process_manager import ProcessManager
from drunc.process_manager.configuration import get_process_manager_configuration
from drunc.process_manager.utils import get_process_manager
from drunc.utils.utils import parent_death_pact, update_log_level, pid_info_str, log_levels

_cleanup_coroutines = []

def run_pm(pm_conf, pm_address, log_level, ready_event=None, signal_handler=None, generated_port=None):
    if signal_handler is not None:
        signal_handler()

    parent_death_pact() # If the parent dies (for example unified shell), we die too

    console = Console()
    console.print(f'Using \'{pm_conf}\' as the ProcessManager configuration')

    update_log_level(log_level)
    logger = getLogger('run_pm')
    logger.debug(pid_info_str())

    pm = get_process_manager(pm_conf, name='process_manager')

    loop = asyncio.get_event_loop()

    async def serve(address:str) -> None:
        if not address:
            raise DruncSetupException('The address on which to expect commands/send status wasn\'t specified')

        server = grpc.aio.server()
        add_ProcessManagerServicer_to_server(pm, server)
        port = server.add_insecure_port(address)
        if generated_port is not None:
            generated_port.value = port

        await server.start()
        hostname = socket.gethostname()
        console.print(f'ProcessManager was started on {hostname}:{port}')


        async def server_shutdown():
            console.print("Starting shutdown...")
            # Shuts down the server with 5 seconds of grace period. During the
            # grace period, the server won't accept new connections and allow
            # existing RPCs to continue within the grace period.
            await server.stop(5)
            pm._terminate_impl(None)

        _cleanup_coroutines.append(server_shutdown())
        if ready_event is not None:
            ready_event.set()

        await server.wait_for_termination()


    try:
        loop.run_until_complete(
            serve(pm_address)
        )
    except Exception as e:
        console.print_exception(width=os.get_terminal_size()[0])
    finally:
        if _cleanup_coroutines:
            loop.run_until_complete(*_cleanup_coroutines)
        loop.close()

@click.command()
@click.argument('pm-conf', type=str)
@click.argument('pm-port', type=int)
@click.option(
    '-l',
    '--log-level',
    type=click.Choice(
        log_levels.keys(),
        case_sensitive=False
    ),
    default='INFO',
    help='Set the log level'
)
def process_manager_cli(pm_conf:str, pm_port:int, log_level):
    pm_conf = get_process_manager_configuration(pm_conf)
    run_pm(pm_conf, f'0.0.0.0:{pm_port}', log_level)
