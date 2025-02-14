import abc
from drunc.exceptions import DruncSetupException
from drunc.utils.utils import ControlType, get_control_type_and_uri_from_connectivity_service, get_control_type_and_uri_from_cli
import logging
from drunc.utils.grpc_utils import pack_to_any
from druncschema.token_pb2 import Token
from druncschema.request_response_pb2 import Response, ResponseFlag, Description
import os
from drunc.connectivity_service.client import ApplicationLookupUnsuccessful

class ChildInterfaceTechnologyUnknown(DruncSetupException):
    def __init__(self, t, name):
        super().__init__(f'The type {t} is not supported for the ChildNode {name}')


class ChildNode(abc.ABC):
    def __init__(self, name:str, configuration, node_type:ControlType, **kwargs) -> None:
        super().__init__(**kwargs)

        self.node_type = node_type
        import logging
        self.log = logging.getLogger(f"{name}-child-node")
        self.name = name
        self.configuration = configuration

    @abc.abstractmethod
    def __str__(self):
        pass
        return f'\'{self.name}@{self.uri}\' (type {self.node_type})'


    @abc.abstractmethod
    def terminate(self):
        pass


    @abc.abstractmethod
    def propagate_command(self, command, data, token):
        pass

    # @abc.abstractmethod
    # def get_status(self, token):
    #     pass

    @abc.abstractmethod
    def get_endpoint(self):
        pass

    def describe(self, token:Token) -> Response:
        descriptionType = None
        descriptionName = None

        if self.configuration is not None:
            if hasattr(self.configuration.data, "application_name"): # Get the application name and type
                descriptionType = self.configuration.data.application_name
                descriptionName = self.configuration.data.id
            elif hasattr(self.configuration.data, "controller") and hasattr(self.configuration.data.controller, "application_name"): # Get the controller name and type
                descriptionType = self.configuration.data.controller.application_name
                descriptionName = self.configuration.data.controller.id

        from drunc.controller.utils import get_detector_name
        d = Description(
            type = descriptionType,
            name = descriptionName,
            endpoint = self.get_endpoint(),
            info = get_detector_name(self.configuration) if self.configuration is not None else None,
            session = os.getenv("DUNEDAQ_SESSION"),
            commands = None,
            broadcast = None,
        )

        resp = Response(
            name = self.name,
            token = token,
            data = pack_to_any(d),
            flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
            children = None
        )
        return resp


    @staticmethod
    def get_child(name:str, cli, configuration, init_token=None, connectivity_service=None, timeout=60, **kwargs):

        from drunc.utils.configuration import ConfTypes
        import logging
        log = logging.getLogger("ChildNode.get_child")

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
                    configuration = gRCPChildConfHandler(configuration, ConfTypes.PyObject),
                    init_token = init_token,
                    name = name,
                    uri = uri,
                    **kwargs,
                )


            case ControlType.REST_API:
                from drunc.controller.children_interface.rest_api_child import RESTAPIChildNode,RESTAPIChildNodeConfHandler

                return RESTAPIChildNode(
                    configuration =  RESTAPIChildNodeConfHandler(configuration, ConfTypes.PyObject),
                    name = name,
                    uri = uri,
                    # init_token = init_token, # No authentication for RESTAPI
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

