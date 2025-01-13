from drunc.utils.shell_utils import ShellContext, GRPCDriver, add_traceback_flag
from drunc.utils.utils import get_logger
from druncschema.token_pb2 import Token
from typing import Mapping

class UnifiedShellContext(ShellContext): # boilerplatefest
    def __init__(self):
        self.status_receiver_pm = None
        self.status_receiver_controller = None
        self.took_control = False
        self.pm_process = None
        self.address_pm = ''
        self.address_controller = ''
        self.boot_configuration = ''
        self.session_name = ''
        super(UnifiedShellContext, self).__init__()

    def reset(self, address_pm:str=''):
        self.address_pm = address_pm
        self.log = get_logger("unified_shell.context", rich_handler = True)
        self.log.debug("Resetting context")
        super(UnifiedShellContext, self)._reset(
            name = 'unified_shell',
            token_args = {},
            driver_args = {},
        )

    def create_drivers(self, **kwargs) -> Mapping[str, GRPCDriver]:
        self.log.debug("Creating drivers")
        ret = {}
        if self.address_pm != '':
            from drunc.process_manager.process_manager_driver import ProcessManagerDriver
            self.log.debug("Setting up process_manager driver")
            ret['process_manager'] = ProcessManagerDriver(
                self.address_pm,
                self._token,
                aio_channel = True,
            )
        if self.address_controller != '':
            from drunc.controller.controller_driver import ControllerDriver
            self.log.debug("Setting up controller driver")
            ret['controller'] = ControllerDriver(
                self.address,
                self._token,
                aio_channel = False,
            )
        self.log.debug("Drivers created and assigned")
        return ret

    def set_controller_driver(self, address_controller, **kwargs) -> None:
        self.log.debug("Setting controller address")
        self.address_controller = address_controller
        from drunc.controller.controller_driver import ControllerDriver
        self._drivers['controller'] = ControllerDriver(
            self.address_controller,
            self._token,
            aio_channel = False,
        )
        self.log.debug("Controller address set and assigned")

    def create_token(self, **kwargs) -> Token:
        self.log.debug("Creating dummy token")
        from drunc.utils.shell_utils import create_dummy_token_from_uname
        token = create_dummy_token_from_uname()
        self.log.debug("Dummy token created")
        return token

    def start_listening_pm(self, broadcaster_conf) -> None:
        self.log.debug("Setting up BroadcastHandler")
        from drunc.broadcast.client.broadcast_handler import BroadcastHandler
        from drunc.broadcast.client.configuration import BroadcastClientConfHandler
        from drunc.utils.configuration import ConfTypes
        bcch = BroadcastClientConfHandler(
            type = ConfTypes.ProtobufAny,
            data = broadcaster_conf,
        )
        self.status_receiver_pm = BroadcastHandler(
            broadcast_configuration = bcch
        )
        self.log.debug("BroadcastHandler set up and assigned")

    def start_listening_controller(self, broadcaster_conf) -> None:
        self.log.debug("Setting up the BroadcastHandler")
        from drunc.broadcast.client.broadcast_handler import BroadcastHandler
        from drunc.broadcast.client.configuration import BroadcastClientConfHandler
        from drunc.utils.configuration import ConfTypes
        bcch = BroadcastClientConfHandler(
            type = ConfTypes.ProtobufAny,
            data = broadcaster_conf,
        )
        self.status_receiver_controller = BroadcastHandler(
            broadcast_configuration = bcch
        )
        self.log.debug("BroadcastHandler set up and assigned")

    def terminate(self) -> None:
        self.log.debug("Terminating")
        if self.status_receiver_pm:
            self.status_receiver_pm.stop()
        if self.status_receiver_controller:
            self.status_receiver_controller.stop()
        self.log.debug("Terminated")

