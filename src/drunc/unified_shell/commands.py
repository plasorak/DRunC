import click
import getpass
import logging

from drunc.controller.interface.shell_utils import controller_setup
from drunc.process_manager.interface.context import ProcessManagerContext
from drunc.process_manager.interface.cli_argument import validate_conf_string
from drunc.utils.shell_utils import InterruptedCommand
from drunc.utils.utils import run_coroutine, log_levels, get_logger

@click.command('boot')
@click.option(
    '-u','--user',
    type=str,
    default=getpass.getuser(),
    help='Select the process of a particular user (default $USER)'
)
@click.option(
    '-l', '--log-level',
    type=click.Choice(log_levels.keys(), case_sensitive=False),
    default='INFO',
    help='Set the log level'
)
@click.option(
    '--override-logs/--no-override-logs',
    default=True
)
@click.pass_obj
@run_coroutine
async def boot(
    obj:ProcessManagerContext,
    user:str,
    log_level:str,
    override_logs:bool,
    ) -> None:

    log = get_logger("unified_shell.boot")
    try:
        results = obj.get_driver('process_manager').boot(
            conf = obj.boot_configuration,
            user = user,
            session_name = obj.session_name,
            log_level = log_level,
            override_logs = override_logs,
        )
        async for result in results:
            if not result: break
            log.debug(f'\'{result.data.process_description.metadata.name}\' ({result.data.uuid.uuid}) started')
    except InterruptedCommand:
        log.warning("Booting interrupted")
        return

    controller_address = obj.get_driver('process_manager').controller_address
    if controller_address:
        log.debug(f'Controller endpoint is \'{controller_address}\'')
        log.debug(f'Connecting the unified_shell to the controller endpoint')
        obj.set_controller_driver(controller_address)
        controller_setup(obj, controller_address)

    else:
        log.error(f'Could not understand where the controller is!')
        return

    log.info("Booted successfully")
