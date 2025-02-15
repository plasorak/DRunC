
def main() -> None:
    from drunc.controller.interface.context import ControllerContext
    context = ControllerContext()

    try:
        from drunc.controller.interface.shell import controller_shell
        controller_shell(obj = context)

    except Exception:
        from rich import print as rprint
        rprint('[red bold]:fire::fire: Exception thrown :fire::fire:')
        from drunc.utils.utils import print_traceback
        print_traceback()
        rprint('Exiting...')
        exit(1)





if __name__ == '__main__':
    main()
