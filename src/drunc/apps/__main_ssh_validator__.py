import click
import conffwk
import getpass
import signal
from drunc.utils.utils import get_logger, setup_root_logger
from sh import Command

from drunc.process_manager.oks_parser import collect_apps
from drunc.process_manager.ssh_process_manager import on_parent_exit
from drunc.utils.configuration import find_configuration


def validate_ssh_connection(configuration:str, session_name:str):
    setup_root_logger("ERROR")
    log = get_logger("validate_ssh_connection.app", rich_handler=True)
    conf = find_configuration(configuration)
    db = conffwk.Configuration(f"oksconflibs:{conf}")
    session_dal = db.get_dal(class_name="Session", uid=session_name)
    # disabled_applications = [app.id for app in session_dal.disabled]
    hosts = set()

    for app in collect_apps(db, session_dal, session_dal.segment, {}):
        hosts.add(app["host"])

    ssh = Command('/usr/bin/ssh')
    for host in hosts:
        user_host = f"{getpass.getuser()}@{host}"
        ssh_args = [user_host, "-tt", "-o StrictHostKeyChecking=no", f"echo \"{user_host} established SSH successfully\";"]
        try:
            process = ssh(
                *ssh_args,
                _bg=False,
                _bg_exc=False,
                _new_session=True,
                _preexec_fn = on_parent_exit(signal.SIGTERM)
            )
            process.wait()
            log.info(f"SSH connection established successfully on host [green]{user_host}[/green]")
        except Exception as e:
            log.error(f"Failed to SSH onto host [red]{user_host}[/red]")
            log.exception(e)

@click.command()
@click.argument('configuration', type=str, nargs=1)
@click.argument('session', type=str, nargs=1)
def main(filename:str, session:str):
    """
    The script validates the ability to SSH onto all of the hosts required by the configuration <configuration> session <session> applications.
    """
    validate_ssh_connection(filename, session)

