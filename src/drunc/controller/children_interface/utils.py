from logging import getLogger

from drunc.controller.children_interface.grpc_child import gRPCChildNode
from drunc.controller.children_interface.rest_api_child import RESTAPIChildNode
from drunc.controller.children_interface.exceptions import ChildInterfaceTechnologyUnknown, DruncSetupException
from drunc.utils.utils import ControlType, get_control_type_and_uri_from_connectivity_service, get_control_type_and_uri_from_cli


def get_child(name:str, cli, configuration, init_token=None, connectivity_service=None, **kwargs):
    log = getLogger("get_child")

    ctype = ControlType.Unknown
    uri = None
    if connectivity_service:
        ctype, uri = get_control_type_and_uri_from_connectivity_service(connectivity_service, name, timeout=60)

    if ctype == ControlType.Unknown:
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

