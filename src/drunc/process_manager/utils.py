
def generate_process_query(f, at_least_one:bool, all_processes_by_default:bool=False):
    import click

    @click.pass_context
    def new_func(ctx, session, name, user, uuid, **kwargs):
        is_trivial_query = bool((len(uuid) == 0) and (session is None) and (len(name) == 0) and (user is None))

        if is_trivial_query and at_least_one:
            raise click.BadParameter('You need to provide at least a \'--uuid\', \'--session\', \'--user\' or \'--name\'!\nAll these values are presented with \'ps\'.\nIf you want to kill everything, use \'ps\' and \'kill\'.')

        if all_processes_by_default and is_trivial_query:
            name = ['.*']

        from druncschema.process_manager_pb2 import ProcessUUID, ProcessQuery

        uuids = [ProcessUUID(uuid=uuid_) for uuid_ in uuid]

        query = ProcessQuery(
            session = session,
            names = name,
            user = user,
            uuids = uuids,
        )
        #print(query)
        return ctx.invoke(f, query=query,**kwargs)

    from functools import update_wrapper
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
    from rich.table import Table
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

    from operator import attrgetter
    sorted_pil = sorted(pil.values, key=attrgetter('process_description.metadata.tree_id'))
    tree_str = make_tree(sorted_pil)
    try:
        for process, line in zip(sorted_pil, tree_str):
            m = process.process_description.metadata
            from druncschema.process_manager_pb2 import ProcessInstance
            alive = 'True' if process.status_code == ProcessInstance.StatusCode.RUNNING else '[danger]False[/danger]'
            row = [m.session, line, m.user, m.hostname, process.uuid.uuid]
            if long:
                executables = [e.exec for e in process.process_description.executable_and_arguments]
                row += ['; '.join(executables)]
            row += [alive, f'{process.return_code}']
            t.add_row(*row)
    except TypeError:
        from drunc.exceptions import DruncCommandException
        raise DruncCommandException("Unable to extract the parameters for tabulate_process_instance_list, exiting.")
    return t


def strip_env_for_rte(env):
    import copy as cp
    import re
    env_stripped = cp.deepcopy(env)
    for key in env.keys():
        if key in ["PATH","CET_PLUGIN_PATH","DUNEDAQ_SHARE_PATH","LD_LIBRARY_PATH","LIBRARY_PATH","PYTHONPATH"]:
            del env_stripped[key]
        if re.search(".*_SHARE", key) and key in env_stripped:
            del env_stripped[key]
    return env_stripped

def get_version():
    from os import getenv
    version = getenv("DUNE_DAQ_BASE_RELEASE")
    if not version:
        raise RuntimeError('Utils: dunedaq version not in the variable env DUNE_DAQ_BASE_RELEASE! Exit drunc and\nexport DUNE_DAQ_BASE_RELEASE=dunedaq-vX.XX.XX\n')
    return version

def get_releases_dir():
    from os import getenv
    releases_dir = getenv("SPACK_RELEASES_DIR")
    if not releases_dir:
        raise RuntimeError('Utils: cannot get env SPACK_RELEASES_DIR! Exit drunc and\nrun dbt-workarea-env or dbt-setup-release.')
    return releases_dir

def release_or_dev():
    from os import getenv
    is_release = getenv("DBT_SETUP_RELEASE_SCRIPT_SOURCED")
    if is_release:
        return 'rel'
    is_devenv = getenv("DBT_WORKAREA_ENV_SCRIPT_SOURCED")
    if is_devenv:
        return 'dev'
    return 'rel'

def get_rte_script():
    from os import path,getenv
    script = ''
    if release_or_dev() == 'rel':
        ver = get_version()
        releases_dir = get_releases_dir()
        script = path.join(releases_dir, ver, 'daq_app_rte.sh')

    else:
        dbt_install_dir = getenv('DBT_INSTALL_DIR')
        script = path.join(dbt_install_dir, 'daq_app_rte.sh')

    if not path.exists(script):
        from drunc.exceptions import DruncSetupException
        raise DruncSetupException(f'Couldn\'t understand where to find the rte script tentative: {script}')
    return script

def get_log_path(user:str, session_name:str, application_name:str, override_logs:bool, app_log_path:str = None, session_log_path:str = None):
    import os
    from drunc.utils.utils import now_str
    pwd = os.getcwd()
    log_path = None
    if app_log_path: # if the user wants to write to a specific path, we never override
        log_path = f'{app_log_path}/log_{user}_{session_name}_{application_name}_{now_str(True)}.txt'
    elif session_log_path: # if the user wants the session to write to a specific path, we never override
        log_path = f'{session_log_path}/log_{user}_{session_name}_{application_name}_{now_str(True)}.txt'
    elif override_logs: # else we check for the override flag
        log_path = f'{pwd}/log_{user}_{session_name}_{application_name}.txt'
    else:
        log_path = f'{pwd}/log_{user}_{session_name}_{application_name}_{now_str(True)}.txt'
    return log_path

def get_pm_conf_name_from_dir(pm_conf_path:str) -> str:
    return pm_conf_path.split('/')[-1].split('.')[0]