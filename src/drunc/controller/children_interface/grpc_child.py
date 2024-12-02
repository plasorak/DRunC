import grpc
from logging import getLogger
from time import sleep

from druncschema.controller_pb2_grpc import ControllerStub
from druncschema.request_response_pb2 import Description, Response

from drunc.broadcast.client.broadcast_handler import BroadcastHandler
from drunc.controller.children_interface.child_node import ChildNode
from drunc.controller.children_interface.types import ControlType
from drunc.controller.utils import send_command
from drunc.exceptions import DruncSetupException
from drunc.utils.configuration import ConfTypes
from drunc.utils.grpc_utils import ServerUnreachable


class gRPCChildNode(ChildNode):
    def __init__(self, name, configuration, init_token, uri):
        super().__init__(
            name = name,
            node_type = ControlType.gRPC,
            configuration  = configuration
        )

        self.log = getLogger(f'{self.name}-grpc-child')

        host, port = uri.split(":")
        port = int(port)

        if port == 0:
            raise DruncSetupException(f"Application \'{name}\' does not expose a control service in the configuration, or has not advertised itself to the connectivity service, or the connectivity service is not reachable.")

        self.uri = f"{host}:{port}"

        self.channel = grpc.insecure_channel(self.uri)
        self.controller = ControllerStub(self.channel)

        desc = Description()
        ntries = 20


        for itry in range(ntries):
            try:
                response = send_command(
                    controller = self.controller,
                    token = init_token,
                    command = 'describe',
                    rethrow = True
                )
                response.data.Unpack(desc)
            except ServerUnreachable as e:
                if itry+1 == ntries:
                    raise e
                else:
                    self.log.info(f'Could not connect to the controller ({self.uri}), trial {itry+1} of {ntries}')
                    sleep(5)

            except ServerUnreachable as e:
                raise DruncSetupException from e
            else:
                self.log.info(f'Connected to the controller ({self.uri})!')
                break
        # self.start_listening(desc.broadcast)

    def __str__(self):
        return f'\'{self.name}@{self.uri}\' (type {self.node_type})'

    def get_endpoint(self):
        return self.uri


    def start_listening(self, bdesc):
        pass
        # self.broadcast = BroadcastHandler()

    def get_status(self, token) -> Response:
        return send_command(
            controller = self.controller,
            token = token,
            command = 'status',
            data = None
        )

    def terminate(self):
        if self.channel:
            self.channel.close()
            del self.channel
        if self.controller:
            del self.controller

        self.controller = None
        self.channel = None
        # self.broadcast.stop()
        pass

    def propagate_command(self, command, data, token) -> Response:
        return send_command(
            controller = self.controller,
            token = token,
            command = command,
            rethrow = True,
            data = data
        )
