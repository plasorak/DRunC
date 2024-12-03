from logging import getLogger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
import time

from drunc.connectivity_service.client import ApplicationLookupUnsuccessful, ConnectivityServiceClient
from drunc.controller.children_interface.exceptions import ChildInterfaceTechnologyUnknown, DruncSetupException
from drunc.controller.children_interface.grpc_child import gRPCChildNode
from drunc.controller.children_interface.rest_api_child import RESTAPIChildNode
from drunc.controller.children_interface.types import ControlType
from drunc.utils.utils import resolve_localhost_and_127_ip_to_network_ip


def get_control_type_and_uri_from_cli(CLAs:list[str]) -> ControlType:
    for CLA in CLAs:
        if   CLA.startswith("rest://"): return ControlType.REST_API, resolve_localhost_and_127_ip_to_network_ip(CLA.replace("rest://", ""))
        elif CLA.startswith("grpc://"): return ControlType.gRPC, resolve_localhost_and_127_ip_to_network_ip(CLA.replace("grpc://", ""))

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
    from drunc.connectivity_service.client import ApplicationLookupUnsuccessful
    logger = getLogger('get_control_type_and_uri_from_connectivity_service')
    import time
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn

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

            try:
                uris = connectivity_service.resolve(name+'_control', 'RunControlMessage')
                if len(uris) == 0:
                    raise ApplicationLookupUnsuccessful
                else:
                    break

            except ApplicationLookupUnsuccessful as e:
                el = time.time() - start
                logger.debug(f"Could not resolve \'{name}_control\' elapsed {el:.2f}s/{timeout}s")
                time.sleep(retry_wait)



    if len(uris) != 1:
        raise ApplicationLookupUnsuccessful(f"Could not resolve the URI for \'{name}_control\' in the connectivity service, got response {uris}")

    uri = uris[0]['uri']

    return get_control_type_and_uri_from_cli([uri])



def get_child(name:str, cli, configuration, init_token=None, connectivity_service=None, timeout=60, **kwargs):

    log = getLogger("drunc.controller.get_child")

    ctype = ControlType.Unknown
    uri = None
    node_in_error = False

    if connectivity_service:
        try:
            ctype, uri = get_control_type_and_uri_from_connectivity_service(connectivity_service, name, timeout=timeout)
        except ApplicationLookupUnsuccessful as alu:
            log.error(f"Could not find the application \'{name}\' in the connectivity service: {alu}")

    if ctype == ControlType.Unknown:
        try:
            ctype, uri = get_control_type_and_uri_from_cli(cli)
        except DruncSetupException as e:
            log.error(f"Could not understand how to talk to the application \'{name}\' from its CLI: {e}")


    address = None
    port = 0
    if uri is not None:
        try:
            address, port = uri.split(":")
            port = int(port)
        except ValueError as e:
            log.debug(f"Could not split the URI {uri} into address and port: {e}")


    if ctype == ControlType.Unknown or address is None or port == 0:
        log.error(f"Could not understand how to talk to \'{name}\'")
        node_in_error = True
        ctype = ControlType.Direct

    log.info(f"Child {name} is of type {ctype} and has the URI {uri}")

    match ctype:
        case ControlType.gRPC:
            from drunc.controller.children_interface.grpc_child import gRPCChildNode, gRCPChildConfHandler

            return gRPCChildNode(
                configuration = configuration,
                init_token = init_token,
                name = name,
                uri = uri,
                **kwargs,
            )


        case ControlType.REST_API:
            from drunc.controller.children_interface.rest_api_child import RESTAPIChildNode,RESTAPIChildNodeConfHandler

            return RESTAPIChildNode(
                configuration = configuration,
                name = name,
                uri = uri,
                **kwargs,
            )

        case ControlType.Direct:
            from drunc.controller.children_interface.client_side_child import ClientSideChild

            node = ClientSideChild(
                name = name,
                **kwargs,
            )
            if node_in_error:
                node.state.to_error()

            return node

        case _:
            raise ChildInterfaceTechnologyUnknown(ctype, name)