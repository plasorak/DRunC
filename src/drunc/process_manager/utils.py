import click
import copy as cp
from functools import update_wrapper
import json
from operator import attrgetter
from os import path,getenv
import re
from rich.console import Console
from rich.table import Table
from urllib.parse import urlparse

from appmodel import smart_daq_application_construct_commandline_parameters
from confmodel import daq_application_construct_commandline_parameters, rc_application_construct_commandline_parameters

from druncschema.process_manager_pb2 import ProcessUUID, ProcessQuery, ProcessInstance

from drunc.exceptions import DruncCommandException, DruncSetupException
from drunc.process_manager.k8s_process_manager import K8sProcessManager
from drunc.process_manager.ssh_process_manager import SSHProcessManager
from drunc.process_manager.types import ProcessManagerTypes

def generate_process_query(f, at_least_one:bool, all_processes_by_default:bool=False):

    @click.pass_context
    def new_func(ctx, session, name, user, uuid, **kwargs):
        is_trivial_query = bool((len(uuid) == 0) and (session is None) and (len(name) == 0) and (user is None))

        if is_trivial_query and at_least_one:
            raise click.BadParameter('You need to provide at least a \'--uuid\', \'--session\', \'--user\' or \'--name\'!\nAll these values are presented with \'ps\'.\nIf you want to kill everything, use \'ps\' and \'kill\'.')

        if all_processes_by_default and is_trivial_query:
            name = ['.*']

        uuids = [ProcessUUID(uuid=uuid_) for uuid_ in uuid]

        query = ProcessQuery(
            session = session,
            names = name,
            user = user,
            uuids = uuids,
        )
        #print(query)
        return ctx.invoke(f, query=query,**kwargs)

    return update_wrapper(new_func, f)

def make_tree(values):
    lines = []
    for result in values:
        m = result.process_description.metadata
        tree_levels = m.tree_id.split('.')
        indent_level = len(tree_levels) - 1
        indentation = "  " * indent_level
        lines.append(indentation + m.name)
    return lines

def tabulate_process_instance_list(pil, title, long=False):
    t = Table(title=title)
    t.add_column('session')
    t.add_column('friendly name')
    t.add_column('user')
    t.add_column('host')
    t.add_column('uuid')
    t.add_column('alive')
    t.add_column('exit-code')
    if long:
        t.add_column('executable')

    sorted_pil = sorted(pil.values, key=attrgetter('process_description.metadata.tree_id'))
    tree_str = make_tree(sorted_pil)
    try:
        for process, line in zip(sorted_pil, tree_str):
            m = process.process_description.metadata
            alive = 'True' if process.status_code == ProcessInstance.StatusCode.RUNNING else '[danger]False[/danger]'
            row = [m.session, line, m.user, m.hostname, process.uuid.uuid]
            if long:
                executables = [e.exec for e in process.process_description.executable_and_arguments]
                row += ['; '.join(executables)]
            row += [alive, f'{process.return_code}']
            t.add_row(*row)
    except TypeError:
        raise DruncCommandException("Unable to extract the parameters for tabulate_process_instance_list, exiting.")
    return t


def strip_env_for_rte(env):

    env_stripped = cp.deepcopy(env)
    for key in env.keys():
        if key in ["PATH","CET_PLUGIN_PATH","DUNEDAQ_SHARE_PATH","LD_LIBRARY_PATH","LIBRARY_PATH","PYTHONPATH"]:
            del env_stripped[key]
        if re.search(".*_SHARE", key) and key in env_stripped:
            del env_stripped[key]
    return env_stripped

def get_version():
    version = getenv("DUNE_DAQ_BASE_RELEASE")
    if not version:
        raise RuntimeError('Utils: dunedaq version not in the variable env DUNE_DAQ_BASE_RELEASE! Exit drunc and\nexport DUNE_DAQ_BASE_RELEASE=dunedaq-vX.XX.XX\n')
    return version

def get_releases_dir():
    releases_dir = getenv("SPACK_RELEASES_DIR")
    if not releases_dir:
        raise RuntimeError('Utils: cannot get env SPACK_RELEASES_DIR! Exit drunc and\nrun dbt-workarea-env or dbt-setup-release.')
    return releases_dir

def release_or_dev():
    is_release = getenv("DBT_SETUP_RELEASE_SCRIPT_SOURCED")
    if is_release:
        return 'rel'
    is_devenv = getenv("DBT_WORKAREA_ENV_SCRIPT_SOURCED")
    if is_devenv:
        return 'dev'
    return 'rel'

def get_rte_script():
    script = ''
    if release_or_dev() == 'rel':
        ver = get_version()
        releases_dir = get_releases_dir()
        script = path.join(releases_dir, ver, 'daq_app_rte.sh')

    else:
        dbt_install_dir = getenv('DBT_INSTALL_DIR')
        script = path.join(dbt_install_dir, 'daq_app_rte.sh')

    if not path.exists(script):
        raise DruncSetupException(f'Couldn\'t understand where to find the rte script tentative: {script}')
    return script


def get_process_manager(conf, **kwargs):
    console = Console()
    conf_parse = urlparse(conf)

    with open(conf_parse.path) as f:
        conf_data = json.load(f)

        match ProcessManagerTypes.from_str(conf_data['type']):
            case ProcessManagerTypes.SSH:
                console.print(f'Starting \'SSHProcessManager\'')
                return SSHProcessManager(conf_data, **kwargs)
            case ProcessManagerTypes.K8s:
                console.print(f'Starting \'K8sProcessManager\'')
                return K8sProcessManager(conf_data, **kwargs)
            case _:
                raise DruncSetupException(f'ProcessManager type {conf.get("type")} is unsupported!')


def get_cla(db, session_uid, obj):

    if hasattr(obj, "oksTypes"):
        if 'RCApplication' in obj.oksTypes():
            return rc_application_construct_commandline_parameters(db, session_uid, obj.id)

        elif 'SmartDaqApplication' in obj.oksTypes():
            return smart_daq_application_construct_commandline_parameters(db, session_uid, obj.id)

        elif 'DaqApplication' in obj.oksTypes():
            return daq_application_construct_commandline_parameters(db, session_uid, obj.id)

    return obj.commandline_parameters
