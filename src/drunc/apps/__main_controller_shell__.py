from rich import print as rprint

from drunc.controller.interface.context import ControllerContext
from drunc.controller.interface.shell import controller_shell
from drunc.utils.utils import print_traceback


def main() -> None:
    context = ControllerContext()

    try:
        controller_shell(obj = context)

    except Exception as e:
        rprint(f'[red bold]:fire::fire: Exception thrown :fire::fire:')
        print_traceback()
        rprint(f'Exiting...')
        exit(1)

if __name__ == '__main__':
    main()
