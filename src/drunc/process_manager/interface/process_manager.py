import asyncio
import click
import grpc
import os
import logging
import getpass

from drunc.utils.utils import log_levels

_cleanup_coroutines = []

def run_pm(pm_conf:str, pm_address:str, log_level:str, ready_event:bool=None, signal_handler:bool=None, generated_port:bool=None, user:str=getpass.getuser(), override_logs:bool=True):
    from drunc.utils.utils import update_log_level, pid_info_str
    from drunc.process_manager.utils import get_log_path
    import os
    log = logging.getLogger('process_manager')
    log.debug(pid_info_str())
    log_path = get_log_path(
        user = user,
        session_name = "",
        application_name = "process_manager",
        override_logs = override_logs
    )
    if override_logs and os.path.isfile(log_path):
        os.remove(log_path)

    handler = logging.FileHandler(log_path)
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s[%(levelname)s] %(funcName)s: %(message)s", "[%H:%M:%S]")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.info("Setting up process_manager with run_pm")

    if signal_handler is not None:
        signal_handler()

    from drunc.utils.utils import parent_death_pact
    parent_death_pact() # If the parent dies (for example unified shell), we die too

    from rich.console import Console
    console = Console()
    console.print(f'Using \'{pm_conf}\' as the ProcessManager configuration')
    log.info(f'Using \'{pm_conf}\' as the ProcessManager configuration')

    from drunc.process_manager.process_manager import ProcessManager
    from drunc.utils.configuration import parse_conf_url, OKSKey
    from drunc.process_manager.configuration import ProcessManagerConfHandler
    conf_path, conf_type = parse_conf_url(pm_conf)
    pmch = ProcessManagerConfHandler(
        type = conf_type,
        data = conf_path
    )

    pm = ProcessManager.get(pmch, name='process_manager')

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
        log.debug(f"Serving the process manager at address {pm_address}")
    except Exception as e:
        import os
        log.error(f"Received exception {e}")
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
    from drunc.process_manager.configuration import get_process_manager_configuration
    pm_conf = get_process_manager_configuration(pm_conf)
    run_pm(pm_conf, f'0.0.0.0:{pm_port}', log_level)
