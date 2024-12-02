from logging import getLogger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
import time

from drunc.connectivity_service.client import ApplicationLookupUnsuccessful, ConnectivityServiceClient
from drunc.controller.children_interface.exceptions import ChildInterfaceTechnologyUnknown, DruncSetupException
from drunc.controller.children_interface.grpc_child import gRPCChildNode
from drunc.controller.children_interface.rest_api_child import RESTAPIChildNode
from drunc.controller.children_interface.types import ControlType
from drunc.utils.utils import resolve_localhost_and_127_ip_to_network_ip


def get_control_type_and_uri_from_cli(CLAs:list[str]) -> (ControlType, str):
    for CLA in CLAs:
        if   CLA.startswith("rest://"): return ControlType.REST_API, resolve_localhost_and_127_ip_to_network_ip(CLA.replace("rest://", ""))
        elif CLA.startswith("grpc://"): return ControlType.gRPC    , resolve_localhost_and_127_ip_to_network_ip(CLA.replace("grpc://", ""))

    raise DruncSetupException("Could not find if the child was controlled by gRPC or a REST API")


def get_control_type_and_uri_from_connectivity_service(
    connectivity_service:ConnectivityServiceClient,
    name:str,
    timeout:int=10, # seconds
    retry_wait:float=0.1, # seconds
    progress_bar:bool=False,
    title:str=None,
) -> tuple[ControlType, str]:

    uris = []
    logger = getLogger('drunc.get_control_type_and_uri_from_connectivity_service')
    logger.info(f"""
{connectivity_service=}
{name=}
{timeout=}
{retry_wait=}
{progress_bar=}
{title=}
""")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn()
    ) as progress:

        task = progress.add_task(f'[yellow]{title}', total=timeout, visible=progress_bar)
        start = time.time()

        while time.time() - start < timeout:
            progress.update(task, completed=time.time() - start)
            logger.info(f"Trying to resolve \'{name}_control\'")
            try:
                uris = connectivity_service.resolve(name+'_control', 'RunControlMessage')
                if len(uris) == 0:
                    raise ApplicationLookupUnsuccessful
                else:
                    break

            except ApplicationLookupUnsuccessful as e:
                el = time.time() - start
                logger.info(f"Could not resolve \'{name}_control\' elapsed {el:.2f}s/{timeout}s")
                time.sleep(retry_wait)



    if len(uris) != 1:
        raise ApplicationLookupUnsuccessful(f"Could not resolve the URI for \'{name}_control\' in the connectivity service, got response {uris}")

    uri = uris[0]['uri']

    return get_control_type_and_uri_from_cli([uri])


def get_child(name:str, cli, configuration, init_token=None, connectivity_service=None, **kwargs):
    log = getLogger("drunc.get_child")

    ctype = ControlType.Unknown
    uri = None
    if connectivity_service:
        log.info(f'Trying to get control type and URI from the connectivity service, for child {name}')
        ctype, uri = get_control_type_and_uri_from_connectivity_service(connectivity_service, name, timeout=60)

    if ctype == ControlType.Unknown:
        log.info(f'Trying to get control type and URI from command line, for child {name}')
        ctype, uri = get_control_type_and_uri_from_cli(cli)

    if uri is None or ctype == ControlType.Unknown:
        log.error(f"Could not understand how to talk to \'{name}\'")
        raise DruncSetupException(f"Could not understand how to talk to \'{name}\'")

    log.info(f"Child {name} is of type {ctype} and has the URI {uri}")

    match ctype:
        case ControlType.gRPC:

            return gRPCChildNode(
                configuration = configuration,
                init_token = init_token,
                name = name,
                uri = uri,
                **kwargs,
            )


        case ControlType.REST_API:

            return RESTAPIChildNode(
                configuration = configuration,
                name = name,
                uri = uri,
                # init_token = init_token, # No authentication for RESTAPI
                **kwargs,
            )
        case _:

            raise ChildInterfaceTechnologyUnknown(ctype, name)

