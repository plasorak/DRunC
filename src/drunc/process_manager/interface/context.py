from rich import print as rprint
from typing import Mapping

from drunc.broadcast.client.broadcast_handler import BroadcastHandler
from drunc.broadcast.client.configuration import BroadcastClientConfHandler
from drunc.process_manager.process_manager_driver import ProcessManagerDriver
from drunc.utils.configuration import ConfTypes
from drunc.utils.shell_utils import ShellContext, GRPCDriver, create_dummy_token_from_uname
from drunc.utils.utils import resolve_localhost_to_hostname

from druncschema.token_pb2 import Token


class ProcessManagerContext(ShellContext): # boilerplatefest
    def __init__(self):
        self.status_receiver = None
        super(ProcessManagerContext, self).__init__()

    def reset(self, address:str=None):
        self.address = resolve_localhost_to_hostname(address)
        super(ProcessManagerContext, self)._reset(
            name = 'process_manager_context',
            token_args = {},
            driver_args = {},
        )

    def create_drivers(self, **kwargs) -> Mapping[str, GRPCDriver]:
        self.log.debug("Creating drivers")
        if not self.address:
            return {}


        return {
            'process_manager': ProcessManagerDriver(
                self.address,
                self._token,
                aio_channel = True,
            )
        }

    def create_token(self, **kwargs) -> Token:
        self.log.debug("Creating token")
        return create_dummy_token_from_uname()


    def start_listening(self, broadcaster_conf):
        self.log.debug("starting to listen")
        bcch = BroadcastClientConfHandler(
            data = broadcaster_conf,
            type = ConfTypes.ProtobufAny,
        )
        self.log.debug(f'Broadcaster configuration:\n{broadcaster_conf}')
        self.status_receiver = BroadcastHandler(bcch)
        rprint(f':ear: Listening to the Process Manager at {self.address}')

    def terminate(self):
        self.log.debug("Terminating")
        if self.status_receiver:
            self.status_receiver.stop()
