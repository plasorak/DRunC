import click
import click_shell
from drunc.utils.utils import log_levels
import os
from drunc.utils.utils import validate_command_facility
import pathlib

@click_shell.shell(prompt='drunc-unified-shell > ', chain=True, hist_file=os.path.expanduser('~')+'/.drunc-unified-shell.history')
@click.option('-l', '--log-level', type=click.Choice(log_levels.keys(), case_sensitive=False), default='INFO', help='Set the log level')
@click.argument('process-manager-configuration', type=str)# callback=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path, resolve_path=True))
@click.pass_context
def unified_shell(ctx, process_manager_configuration:str, log_level:str) -> None:

    from drunc.utils.utils import update_log_level, pid_info_str, ignore_sigint_sighandler
    update_log_level(log_level)
    from logging import getLogger
    logger = getLogger('unified_shell')
    logger.debug(pid_info_str())

    from drunc.process_manager.interface.process_manager import run_pm
    import multiprocessing as mp
    ready_event = mp.Event()
    port = mp.Value('i', 0)

    # Check if process_manager_configuration is a packaged config
    from urllib.parse import urlparse
    import os
    ## Make the configuration name finding easier
    if os.path.splitext(process_manager_configuration)[1] != '.json':
        process_manager_configuration += '.json'
    ## If no scheme is provided, assume that it is an internal packaged configuration.
    ## First check it's not an existing external file
    if os.path.isfile(process_manager_configuration):
        if urlparse(process_manager_configuration).scheme == '':
            process_manager_configuration = 'file://' + process_manager_configuration
    else:
        ## Check if the file is in the list of packaged configurations
        from importlib.resources import path
        packaged_configurations = os.listdir(path('drunc.data.process_manager', ''))
        if process_manager_configuration in packaged_configurations:
            process_manager_configuration = 'file://' + str(path('drunc.data.process_manager', '')) + '/' + process_manager_configuration
        else:
            from drunc.exceptions import DruncShellException
            raise DruncShellException(f"Configuration {process_manager_configuration} is not found in the package. The packaged configurations are {packaged_configurations}")

    ctx.obj.pm_process = mp.Process(
        target = run_pm,
        kwargs = {
            "pm_conf": process_manager_configuration,
            "log_level": log_level,
            "ready_event": ready_event,
            "signal_handler": ignore_sigint_sighandler,
            # sigint gets sent to the PM, so we need to ignore it, otherwise everytime the user ctrl-c on the shell, the PM goes down
            "generated_port": port,
        },
    )
    ctx.obj.print(f'Starting process manager with configuration {process_manager_configuration}')
    ctx.obj.pm_process.start()


    from time import sleep
    for _ in range(100):
        if ready_event.is_set():
            break
        sleep(0.1)

    if not ready_event.is_set():
        from drunc.exceptions import DruncSetupException
        raise DruncSetupException('Process manager did not start in time')

    import socket
    process_manager_address = f'localhost:{port.value}'

    ctx.obj.reset(
        address_pm = process_manager_address,
    )

    desc = None

    try:
        import asyncio
        desc = asyncio.get_event_loop().run_until_complete(
            ctx.obj.get_driver().describe()
        )
        desc = desc.data

    except Exception as e:
        ctx.obj.critical(f'Could not connect to the process manager')
        if not ctx.obj.pm_process.is_alive():
            ctx.obj.critical(f'The process manager is dead, exit code {ctx.obj.pm_process.exitcode}')
        raise e

    ctx.obj.info(f'{process_manager_address} is \'{desc.name}.{desc.session}\' (name.session), starting listening...')
    if desc.HasField('broadcast'):
        ctx.obj.start_listening_pm(
            broadcaster_conf = desc.broadcast,
        )

    def cleanup():
        ctx.obj.terminate()
        ctx.obj.pm_process.terminate()
        ctx.obj.pm_process.join()

    ctx.call_on_close(cleanup)

    from drunc.unified_shell.commands import boot
    ctx.command.add_command(boot, 'boot')

    from drunc.process_manager.interface.commands import kill, flush, logs, restart, ps, dummy_boot
    ctx.command.add_command(kill, 'kill')
    ctx.command.add_command(flush, 'flush')
    ctx.command.add_command(logs, 'logs')
    ctx.command.add_command(restart, 'restart')
    ctx.command.add_command(ps, 'ps')
    ctx.command.add_command(dummy_boot, 'dummy_boot')

    from drunc.controller.interface.commands import (
        describe, ls, status, connect, take_control, surrender_control, who_am_i, who_is_in_charge, fsm, include, exclude
    )
    ctx.command.add_command(describe, 'describe')
    ctx.command.add_command(ls, 'ls')
    ctx.command.add_command(status, 'status')
    ctx.command.add_command(connect, 'connect')
    ctx.command.add_command(take_control, 'take-control')
    ctx.command.add_command(surrender_control, 'surrender-control')
    ctx.command.add_command(who_am_i, 'whoami')
    ctx.command.add_command(who_is_in_charge, 'who-is-in-charge')
    ctx.command.add_command(fsm, 'fsm')
    ctx.command.add_command(include, 'include')
    ctx.command.add_command(exclude, 'exclude')
