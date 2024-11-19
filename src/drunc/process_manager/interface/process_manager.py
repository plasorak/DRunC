import asyncio
import click
import grpc
import os
import logging
import getpass

from drunc.utils.utils import log_levels

_cleanup_coroutines = []

def run_pm(pm_conf:str, pm_address:str, override_logs:bool, log_level:str, ready_event:bool=None, signal_handler:bool=None, generated_port:bool=None):
    log = logging.getLogger("run_pm")
    log.debug("Running run_pm")
    if signal_handler is not None:
        signal_handler()

    from drunc.utils.utils import parent_death_pact
    parent_death_pact() # If the parent dies (for example unified shell), we die too

    # from rich.console import Console
    # console = Console()
    log.debug(f'Using \'{pm_conf}\' as the ProcessManager configuration')

    from drunc.process_manager.process_manager import ProcessManager
    from drunc.utils.configuration import parse_conf_url, OKSKey
    from drunc.process_manager.configuration import ProcessManagerConfHandler
    conf_path, conf_type = parse_conf_url(pm_conf)
    pmch = ProcessManagerConfHandler(
        type = conf_type,
        data = conf_path
    )

    pm = ProcessManager.get(
        pmch,
        name='process_manager',
        override_logs = override_logs,
        log_level = log_level
    )
    log.debug("Setup up ProcessManager")

    loop = asyncio.get_event_loop()

    async def serve(address:str) -> None:
        if not address:
            from drunc.exceptions import DruncSetupException
            raise DruncSetupException('The address on which to expect commands/send status wasn\'t specified')
        from druncschema.process_manager_pb2_grpc import add_ProcessManagerServicer_to_server

        server = grpc.aio.server()
        add_ProcessManagerServicer_to_server(pm, server)
        port = server.add_insecure_port(address)
        if generated_port is not None:
            generated_port.value = port

        await server.start()
        import socket
        hostname = socket.gethostname()
        log.debug(f'ProcessManager was started on {hostname}:{port}')


        async def server_shutdown():
            log.warning("Starting shutdown...")
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
        log.debug("Serving process manager")
        loop.run_until_complete(
            serve(pm_address)
        )
    except Exception as e:
        log.error("Serving the ProcessManager received an Exception")
        import os
        console.print_exception(width=os.get_terminal_size()[0])
    finally:
        if _cleanup_coroutines:
            log.debug("Clearing coroutines")
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
    from drunc.process_manager.configuration import get_process_manager_configuration
    pm_conf = get_process_manager_configuration(pm_conf)
    run_pm(pm_conf, f'0.0.0.0:{pm_port}', log_level)
