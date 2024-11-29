from importlib.resources import path
import os
from rich import print as rprint
from urllib.parse import urlparse


def get_process_manager_configuration(process_manager):

    ## Make the configuration name finding easier
    if os.path.splitext(process_manager)[1] != '.json':
        process_manager += '.json'

    ## If no scheme is provided, assume that it is an internal packaged configuration.
    ## First check it's not an existing external file
    if os.path.isfile(process_manager):
        if urlparse(process_manager).scheme == '':
            process_manager = 'file://' + process_manager
    else:
        ## Check if the file is in the list of packaged configurations
        packaged_configurations = os.listdir(path('drunc.data.process_manager', ''))
        if process_manager in packaged_configurations:
            process_manager = 'file://' + str(path('drunc.data.process_manager', '')) + '/' + process_manager
        else:
            rprint(f"Configuration [red]{process_manager}[/red] not found, check filename spelling or use a packaged configuration as one of [green]{packaged_configurations}[/green]")
            exit()

    return process_manager
