import click
from drunc.controller.interface.context import ControllerContext

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


@click.command('recompute-status')
@click.pass_obj
def recompute_status(obj:ControllerContext) -> None:
    statuses = obj.get_driver('controller').recompute_status()
    descriptions = obj.get_driver('controller').describe()
    from drunc.controller.interface.shell_utils import print_status_table
    print_status_table(obj, statuses, descriptions)


@click.command('connect')
@click.argument('controller_address', type=str)
@click.option('-f', '--force', is_flag=True, help='Confirm the disconnect')
@click.pass_obj
def connect(obj:ControllerContext, controller_address:str, force:bool) -> None:
    if obj.has_driver('controller'):
        driver = obj.get_driver("controller")
        obj.info(f'Already connected to a controller ({driver.name}@{driver.address})')
        if not force:
            click.confirm(f'Do you want to disconnect from it before?', abort=True)
        obj.info(f'Disconnecting...')
        obj.delete_driver('controller')

    obj.info(f'Connecting this shell to the controller at {controller_address}...')

    if controller_address.startswith('grpc://'):
        controller_address = controller_address.replace('grpc://', '')

    from drunc.exceptions import DruncException

    obj.set_controller_driver(controller_address)
    from drunc.controller.interface.shell_utils import controller_setup
    controller_setup(obj, controller_address)


@click.command('disconnect')
@click.option('-f', '--force', is_flag=True, help='Confirm the disconnect')
@click.pass_obj
def disconnect(obj:ControllerContext, force:bool):
    if not obj.has_driver('controller'):
        obj.info('You are not connected to any controller.')
        return

    driver = obj.get_driver("controller")

    if not force:
        obj.info(f'''
[red]You are about to disconnect from the {driver.name} controller.[/red]

To reconnect to it, you will need to issue the following command:

[yellow]connect {driver.address}[/yellow]

To get the address of another controller, abort now and issue the command:

[yellow]status[/yellow]

You can also find the controller address on the connectivity service.
''', extra={'markup': True})
        click.confirm('Are you sure you want to disconnect from the controller?', abort=True)

    obj.delete_driver('controller')


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
