from importlib.resources import path
import os
from rich import print as rprint
from urllib.parse import urlparse


def get_process_manager_configuration(process_manager_conf_filename:str) -> str:
    ## Make the configuration name finding easier
    if os.path.splitext(process_manager_conf_filename)[1] != '.json':
        process_manager_conf_filename += '.json'
    ## If no scheme is provided, assume that it is an internal packaged configuration.
    ## First check it's not an existing external file
    if os.path.isfile(process_manager_conf_filename):
        if urlparse(process_manager_conf_filename).scheme == '':
            process_manager_conf_filename = 'file://' + process_manager_conf_filename
    else:
        ## Check if the file is in the list of packaged configurations
        packaged_configurations = os.listdir(path('drunc.data.process_manager', ''))
        if process_manager_conf_filename in packaged_configurations:
            process_manager_conf_filename = 'file://' + str(path('drunc.data.process_manager', '')) + '/' + process_manager_conf_filename
        else:
            rprint(f"Configuration [red]{process_manager_conf_filename}[/red] not found, check filename spelling or use a packaged configuration as one of [green]{packaged_configurations}[/green]")
            exit()

    return process_manager_conf_filename
