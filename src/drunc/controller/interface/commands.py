import click
import json
from drunc.controller.interface.context import ControllerContext
from druncschema.generic_pb2 import PlainText, Stacktrace

@click.command('list-transitions')
@click.option('--all', is_flag=True, help='List all transitions (available and unavailable)')
@click.pass_obj
def list_transitions(obj:ControllerContext, all:bool) -> None:
    desc = obj.get_driver('controller').describe_fsm('all-transitions' if all else None)

    if not desc:
        obj.print('Could not get the list of commands available')
        return

    from rich.table import Table
    if all:
        obj.print(f'\nAvailable transitions on \'{desc.name}\' are ([underline]some may not be accessible now, use list-transition without --all to see what transitions can be issued now[/]):')
    else:
        obj.print(f'\nCurrently available controller transitions on \'{desc.name}\' are:')

    for c in desc.data.commands:
        obj.print(f' - [yellow]{c.name.replace("_","-").lower()}[/]')


    obj.print('\nUse [yellow]help <command>[/] for more information on a command.\n')


@click.command('wait')
@click.argument("sleep_time", type=int, default=1)
@click.pass_obj
def wait(obj:ControllerContext, sleep_time:int) -> None:
    # Requested to "allow processing of commands to pause for a specified number of seconds"
    from time import sleep
    obj.print(f"Command [green]wait[/green] running for {sleep_time} seconds.")
    sleep(sleep_time)
    obj.print(f"Command [green]wait[/green] ran for {sleep_time} seconds.")




@click.command('status')
@click.pass_obj
def status(obj:ControllerContext) -> None:
    # Get the dynamic system information
    statuses = obj.get_driver('controller').status()
    # Get the static system information
    descriptions = obj.get_driver('controller').describe()
    from drunc.controller.interface.shell_utils import print_status_table
    print_status_table(obj, statuses, descriptions)

@click.command('connect')
@click.argument('controller_address', type=str)
@click.pass_obj
def connect(obj:ControllerContext, controller_address:str) -> None:
    obj.print(f'Connecting this shell to it...')
    from drunc.exceptions import DruncException

    obj.set_controller_driver(controller_address)
    from drunc.controller.interface.shell_utils import controller_setup
    controller_setup(obj, controller_address)


@click.command('take-control')
@click.pass_obj
def take_control(obj:ControllerContext) -> None:
    obj.get_driver('controller').take_control().data


@click.command('surrender-control')
@click.pass_obj
def surrender_control(obj:ControllerContext) -> None:
    obj.get_driver('controller').surrender_control().data


@click.command('who-am-i')
@click.pass_obj
def who_am_i(obj:ControllerContext) -> None:
    obj.print(obj.get_token().user_name)


@click.command('who-is-in-charge')
@click.pass_obj
def who_is_in_charge(obj:ControllerContext) -> None:
    who = obj.get_driver('controller').who_is_in_charge().data
    if who:
        obj.print(who.text)

@click.command('include')
@click.pass_obj
def include(obj:ControllerContext) -> None:
    from druncschema.controller_pb2 import FSMCommand
    data = FSMCommand(
        command_name = 'include',
    )
    result = obj.get_driver('controller').include(arguments=data).data
    if not result: return
    obj.print(result.text)


@click.command('exclude')
@click.pass_obj
def exclude(obj:ControllerContext) -> None:
    from druncschema.controller_pb2 import FSMCommand
    data = FSMCommand(
        command_name = 'exclude',
    )
    result = obj.get_driver('controller').exclude(arguments=data).data
    if not result: return
    obj.print(result.text)


@click.command('expert-command')
@click.option('-s', '--string', is_flag=True, help='Read the command directly from the command line, else you need to write a file and provide its path')
@click.argument('command', type=str)
@click.pass_obj
def expert_command(obj:ControllerContext, command:str, string:bool) -> None:
    data = dict()

    try:
        if string:
            data = json.loads(command)
        else:
            with open(command, 'r') as f:
                data = json.load(f)

    except FileNotFoundError:
        obj.print(f'File not found: {command}')
        return

    except json.JSONDecodeError as e:
        obj.print(f'JSON decode error: {e}')
        return

    result = obj.get_driver('controller').expert_command(json_string=json.dumps(data))

    def print_result(result, prefix=""):

        if not hasattr(result, "data"):
            obj.print(f'{prefix}[yellow]{result.name}[/yellow] [red]NO RESPONSE (no data)[/red]')
        elif result.data.DESCRIPTOR.name == "PlainText":
            obj.print(f'{prefix}[yellow]{result.name}[/yellow] [green]{result.data.text}[/green]')
        elif result.data.DESCRIPTOR.name == "Stacktrace":
            for i in reversed(range(len(result.data.text))):
                error = result.data.text[i]
                if error != '':
                    break
            obj.print(f'{prefix}[yellow]{result.name}[/yellow] [red]ERROR: {error}[/red]')
        else:
            obj.print(f'{prefix}[yellow]{result.name}[/yellow] [red]NO RESPONSE (data format not understood: {result.data.DESCRIPTOR.name})[/red]')

        for child in result.children:
            print_result(child, prefix + "    ")

    print_result(result)
