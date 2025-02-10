from drunc.controller.interface.controller import controller_cli
from drunc.utils.utils import print_traceback


def main():
    try:
        controller_cli()
    except Exception:
        print_traceback()

if __name__ == '__main__':
    main()

