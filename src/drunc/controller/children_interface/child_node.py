import abc
import os
import logging

from druncschema.token_pb2 import Token
from druncschema.request_response_pb2 import Response, ResponseFlag, Description

from drunc.controller.children_interface.types import ControlType
from drunc.controller.utils import get_detector_name
from drunc.utils.grpc_utils import pack_to_any


class ChildNode(abc.ABC):
    def __init__(self, name:str, configuration, node_type:ControlType, **kwargs) -> None:
        super().__init__(**kwargs)

        self.node_type = node_type
        self.log = logging.getLogger(f"{name}-child-node")
        self.name = name
        self.configuration = configuration


    @abc.abstractmethod
    def __str__(self):
        return f'\'{self.name}@{self.uri}\' (type {self.node_type})'


    @abc.abstractmethod
    def terminate(self):
        pass


    @abc.abstractmethod
    def propagate_command(self, command, data, token):
        pass


    @abc.abstractmethod
    def get_status(self, token):
        pass


    @abc.abstractmethod
    def get_endpoint(self):
        pass


    def describe(self, token:Token) -> Response:
        descriptionType = None
        descriptionName = None

        if self.configuration is not None:
            if hasattr(self.configuration, "application_name"): # Get the application name and type
                descriptionType = self.configuration.application_name
                descriptionName = self.configuration.id
            elif hasattr(self.configuration, "controller") and hasattr(self.configuration.controller, "application_name"): # Get the controller name and type
                descriptionType = self.configuration.controller.application_name
                descriptionName = self.configuration.controller.id

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
