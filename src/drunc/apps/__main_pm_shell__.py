from rich import print as rprint

from drunc.process_manager.interface.shell import process_manager_shell
from drunc.process_manager.interface.context import ProcessManagerContext
from drunc.utils.utils import print_traceback


def main():
    context = ProcessManagerContext()
    try:
        process_manager_shell(obj = context)
    except Exception as e:
        rprint(f'[red bold]:fire::fire: Exception thrown :fire::fire:')
        print_traceback()
        rprint(f'Exiting...')
        exit(1)

if __name__ == '__main__':
    main()
