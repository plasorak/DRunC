import click
import click_shell
import os
import logging

from drunc.controller.interface.context import ControllerContext
from drunc.controller.interface.shell_utils import controller_cleanup_wrapper, controller_setup, generate_fsm_command
from drunc.utils.utils import CONTEXT_SETTINGS, get_logger, log_levels, validate_command_facility


@click_shell.shell(prompt='drunc-controller > ', chain=True, context_settings=CONTEXT_SETTINGS, hist_file=os.path.expanduser('~')+'/.drunc-controller-shell.history')
@click.option('-l', '--log-level', type=click.Choice(log_levels.keys(), case_sensitive=False), default='INFO', help='Set the log level')
@click.argument('controller-address', type=str, callback=validate_command_facility)
@click.pass_context
def controller_shell(ctx, controller_address:str, log_level:str) -> None:
    controller_shell_log = get_logger(
        logger_name = "controller_shell",
        rich_handler = True,
        rich_log_level = log_level
    )

    ctx.obj.reset(address = controller_address)
    controller_shell_log.info(f"Connected to [green]{ctx.obj.get_driver('controller').describe().data.name}[/green] at address [green]{controller_address}[/green]")
    ctx.call_on_close(controller_cleanup_wrapper(ctx.obj))
    controller_desc = controller_setup(ctx.obj, controller_address)

    transitions = ctx.obj.get_driver('controller').describe_fsm(key="all-transitions").data

    from drunc.controller.interface.commands import (
        status, connect, take_control, surrender_control, who_am_i, who_is_in_charge, include, exclude, wait
    )

    ctx.command.add_command(status, 'status')
    ctx.command.add_command(connect, 'connect')
    ctx.command.add_command(take_control, 'take-control')
    ctx.command.add_command(surrender_control, 'surrender-control')
    ctx.command.add_command(who_am_i, 'whoami')
    ctx.command.add_command(who_is_in_charge, 'who-is-in-charge')
    for transition in transitions.commands:
        ctx.command.add_command(*generate_fsm_command(ctx.obj, transition, controller_desc.name))
    ctx.command.add_command(include, 'include')
    ctx.command.add_command(exclude, 'exclude')
    ctx.command.add_command(wait, 'wait')
