import asyncio
import click
import grpc
import os
import logging
import getpass
from rich.console import Console
from rich.logging import RichHandler
from drunc.utils.utils import log_levels, setup_root_logger, get_logger
from drunc.process_manager.utils import get_log_path
_cleanup_coroutines = []

def run_pm(pm_conf:str, pm_address:str, log_level:str, override_logs:bool, log_path:str=None, user:str=getpass.getuser(), ready_event:bool=None, signal_handler:bool=None, generated_port:bool=None):
    appName = "process_manager"

    from drunc.process_manager.utils import get_pm_conf_name_from_dir
    pmConfFileName = get_pm_conf_name_from_dir(pm_conf) # Treating the pm conf data filename as the session

    log_path = get_log_path(
        user = user,
        session_name = pmConfFileName,
        application_name = appName,
        override_logs = override_logs,
        app_log_path = log_path
    )
    log = get_logger(
        logger_name = "process_manager", 
        log_file_path = log_path,
        rich_handler = True
    )

    log.info("Running run_pm")
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

    pm = ProcessManager.get(pmch, name="process_manager")
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
        log.info(f'ProcessManager was started on {hostname}:{port}')


        async def server_shutdown():
            log.warning("Starting shutdown...")
            # Shuts down the server with 5 seconds of grace period. During the
            # grace period, the server won't accept new connections and allow
            # existing RPCs to continue within the grace period.
            await server.stop(5)
            pm._terminate_impl()

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
        from rich.console import Console
        console = Console()
        console.print_exception(width=os.get_terminal_size()[0])
    finally:
        if _cleanup_coroutines:
            log.info("Clearing coroutines")
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
    default='DEBUG',
    help='Set the log level'
)
@click.option('-o/-no', '--override-logs/--no-override-logs', type=bool, default=True, help="Override logs, if --no-override-logs filenames have the timestamp of the run.")
@click.option('-lp', '--log-path', type=str, default=None, help="Log path of process_manager logs.")
@click.option('-u', '--user', type=str, default=getpass.getuser(), help="Username for process_manager logs.")
def process_manager_cli(pm_conf:str, pm_port:int, log_level:str, override_logs:bool, log_path:str, user:str):
    from drunc.process_manager.configuration import get_process_manager_configuration
    pm_conf = get_process_manager_configuration(pm_conf)
    run_pm(
        pm_conf = pm_conf,
        pm_address = f'0.0.0.0:{pm_port}',
        log_level = log_level,
        override_logs = override_logs,
        log_path = log_path,
        user = user
    )