import abc
import os
import getpass
import logging

from drunc.authoriser.decorators import authentified_and_authorised, async_authentified_and_authorised
from drunc.broadcast.server.decorators import broadcasted, async_broadcasted
from drunc.exceptions import DruncCommandException
from drunc.process_manager.configuration import ProcessManagerConfHandler, ProcessManagerTypes
from drunc.process_manager.utils import get_log_path, get_pm_conf_name_from_dir
from drunc.utils.grpc_utils import unpack_request_data_to, async_unpack_request_data_to,pack_to_any
from drunc.utils.utils import get_logger, pid_info_str

from druncschema.authoriser_pb2 import ActionType, SystemType
from druncschema.broadcast_pb2 import BroadcastType
from druncschema.process_manager_pb2 import BootRequest, ProcessQuery, ProcessInstance, ProcessRestriction, ProcessDescription, ProcessUUID, ProcessInstanceList, LogRequest, LogLine
from druncschema.process_manager_pb2_grpc import ProcessManagerServicer
from druncschema.request_response_pb2 import Request, Response, ResponseFlag


class BadQuery(DruncCommandException):
    def __init__(self, txt):
        from google.rpc import code_pb2
        super(BadQuery, self).__init__(txt, code_pb2.INVALID_ARGUMENT)

class ProcessManager(abc.ABC, ProcessManagerServicer):

    def __init__(self, configuration:ProcessManagerConfHandler, name:str, session:str=None, **kwargs):
        super().__init__()
        self.log = get_logger(logger_name = f"process_manager.{configuration.data.type._name_}_process_manager")
        self.log.debug(pid_info_str())
        self.log.debug("Initialized ProcessManager")

        self.configuration = configuration
        self.name = name
        self.session = session

        from drunc.broadcast.server.configuration import BroadcastSenderConfHandler
        from drunc.utils.configuration import ConfTypes
        bsch = BroadcastSenderConfHandler(
            data = self.configuration.data.broadcaster,
            type = ConfTypes.PyObject
        )

        from drunc.broadcast.server.broadcast_sender import BroadcastSender
        self.broadcast_service = BroadcastSender(
            name = name,
            session = session,
            configuration = bsch,
        ) if bsch.data else None

        from drunc.authoriser.configuration import DummyAuthoriserConfHandler
        from drunc.utils.configuration import ConfTypes
        dach = DummyAuthoriserConfHandler(
            data = self.configuration.data.authoriser,
            type = ConfTypes.PyObject
        )

        from drunc.authoriser.dummy_authoriser import DummyAuthoriser
        from druncschema.authoriser_pb2 import SystemType
        self.authoriser = DummyAuthoriser(
            dach,
            SystemType.PROCESS_MANAGER
        )

        self.process_store = {} # dict[str, sh.RunningCommand]
        self.boot_request = {} # dict[str, BootRequest]

        from druncschema.request_response_pb2 import CommandDescription
        # TODO, probably need to think of a better way to do this?
        # Maybe I should "bind" the commands to their methods, and have something looping over this list to generate the gRPC functions
        # Not particularly pretty...
        self.commands = [
            CommandDescription(
                name = 'describe',
                data_type = ['None'],
                help = 'Describe self (return a list of commands, the type of endpoint, the name and session).',
                return_type = 'request_response_pb2.Description'
            ),

            CommandDescription(
                name = 'kill',
                data_type = ['process_manager_pb2.ProcessQuery'],
                help = 'Kill listed process from the process query input (can be multiple).',
                return_type = 'process_manager_pb2.ProcessInstanceList'
            ),

            CommandDescription(
                name = 'restart',
                data_type = ['process_manager_pb2.ProcessQuery'],
                help = 'Restart the process from the process query (which must correspond to one process).',
                return_type = 'process_manager_pb2.ProcessInstance'
            ),

            CommandDescription(
                name = 'boot',
                data_type = ['generic_pb2.BootRequest','None'],
                help = 'Start a process.',
                return_type = 'process_manager_pb2.ProcessInstance'
            ),

            CommandDescription(
                name = 'terminate',
                data_type = ['process_manager_pb2.ProcessQuery'],
                help = 'Kill all processes in session.',
                return_type = 'process_manager_pb2.ProcessInstanceList'
            ),

            CommandDescription(
                name = 'flush',
                data_type = ['process_manager_pb2.ProcessQuery'],
                help = 'Remove the processes from the list that are dead',
                return_type = 'process_manager_pb2.ProcessInstanceList'
            ),

            CommandDescription(
                name = 'logs',
                data_type = ['process_manager_pb2.LogRequest'],
                help = 'Returns the logs from the process ( must correspond to one process). Note this is an ASYNC function',
                return_type = 'process_manager_pb2.LogLine'
            ),

            CommandDescription(
                name = 'ps',
                data_type = ['process_manager_pb2.ProcessQuery'],
                help = 'Get the status of the listed process from the process query input (can be multiple).',
                return_type = 'process_manager_pb2.ProcessInstance'
            ),
        ]

        self.broadcast(
            message = 'ready',
            btype = BroadcastType.SERVER_READY
        )
    '''
    A couple of simple pass-through functions to the broadcasting service
    '''
    def broadcast(self, *args, **kwargs):
        self.log.debug(f"{self.name} broadcasting")
        return self.broadcast_service.broadcast(*args, **kwargs) if self.broadcast_service else None

    def can_broadcast(self, *args, **kwargs):
        self.log.debug(f"Checking if {self.name} can broadcast")
        return self.broadcast_service.can_broadcast(*args, **kwargs) if self.broadcast_service else False

    def describe_broadcast(self, *args, **kwargs):
        self.log.debug(f"Describing {self.name} broadcast")
        return self.broadcast_service.describe_broadcast(*args, **kwargs) if self.broadcast_service else None

    def interrupt_with_exception(self, *args, **kwargs):
        self.log.debug(f"Interrupting {self.name} broadcast with exception")
        return self.broadcast_service._interrupt_with_exception(*args, **kwargs) if self.broadcast_service else None

    def async_interrupt_with_exception(self, *args, **kwargs):
        self.log.debug(f"Interrupting {self.name} broadcast asynchronously with exception")
        return self.broadcast_service._async_interrupt_with_exception(*args, **kwargs) if self.broadcast_service else None


    @abc.abstractmethod
    def _boot_impl(self, br:BootRequest) -> ProcessInstance:
        raise NotImplementedError

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.CREATE,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(BootRequest) # 3rd step
    def boot(self, br:BootRequest) -> Response:
        self.log.debug(f"{self.name} booting \'{br.process_description.metadata.name}\' from session \'{br.process_description.metadata.session}\'")
        try:
            resp = self._boot_impl(br)
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = [],
            )
        except NotImplementedError:
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )


    @abc.abstractmethod
    def _terminate_impl(self) -> ProcessInstanceList:
        raise NotImplementedError

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.DELETE,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(None) # 3rd step
    def terminate(self) -> Response:
        self.log.debug(f"{self.name} terminating")
        try:
            resp = self._terminate_impl()
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = [],
            )
        except NotImplementedError:
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )

    @abc.abstractmethod
    def _restart_impl(self, q:ProcessQuery) -> ProcessInstanceList:
        raise NotImplementedError

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.DELETE,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(ProcessQuery) # 3rd step
    def restart(self, q:ProcessQuery)-> Response:
        self.log.debug(f"{self.name} running restart")
        try:
            resp = self._restart_impl(q)
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = [],
            )
        except NotImplementedError:
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )


    @abc.abstractmethod
    def _kill_impl(self, q:ProcessQuery) -> ProcessInstanceList:
        raise NotImplementedError

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.DELETE,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(ProcessQuery) # 3rd step
    def kill(self, q:ProcessQuery) -> Response:
        self.log.debug(f"{self.name} running kill")
        try:
            resp = self._kill_impl(q)
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = [],
            )
        except NotImplementedError:
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )


    @abc.abstractmethod
    def _ps_impl(self, q:ProcessQuery) -> ProcessInstanceList:
        raise NotImplementedError

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.READ,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(ProcessQuery) # 3rd step
    def ps(self, q:ProcessQuery) -> Response:
        self.log.debug(f"{self.name} running ps")
        try:
            resp = self._ps_impl(q)
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                children = [],
            )
        except NotImplementedError:
            return Response(
                name = self.name,
                token = None,
                data = pack_to_any(resp),
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )

    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.DELETE,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(ProcessQuery) # 3rd step
    def flush(self, query:ProcessQuery) -> Response:
        self.log.debug(f"{self.name} running flush")
        ret = []

        for uuid in self._get_process_uid(query):

            if uuid not in self.boot_request:
                pu = ProcessUUID(uuid=uuid)
                pi = ProcessInstance(
                    process_description = ProcessDescription(),
                    process_restriction = ProcessRestriction(),
                    status_code = ProcessInstance.StatusCode.DEAD,
                    return_code = None,
                    uuid = pu
                )
                ret += [pi]
                continue

            pd = ProcessDescription()
            pd.CopyFrom(self.boot_request[uuid].process_description)
            pr = ProcessRestriction()
            pr.CopyFrom(self.boot_request[uuid].process_restriction)
            pu = ProcessUUID(uuid=uuid)

            return_code = None
            try:
                if not self.process_store[uuid].is_alive(): # OMG!! remove this implementation code
                    return_code = self.process_store[uuid].exit_code
            except Exception as e:
                pass

            if not self.process_store[uuid].is_alive():
                pi = ProcessInstance(
                    process_description = pd,
                    process_restriction = pr,
                    status_code = ProcessInstance.StatusCode.RUNNING if self.process_store[uuid].is_alive() else ProcessInstance.StatusCode.DEAD,
                    return_code = return_code,
                    uuid = pu
                )
                del self.process_store[uuid]
                ret += [pi]

        pil = ProcessInstanceList(
            values=ret
        )

        return Response(
            name = self.name,
            token = None,
            data = pack_to_any(pil),
            flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
            children = [],
        )


    # ORDER MATTERS!
    @broadcasted # outer most wrapper 1st step
    @authentified_and_authorised(
        action=ActionType.READ,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @unpack_request_data_to(None) # 3rd step
    def describe(self) -> Response:
        self.log.debug(f"{self.name} running describe")
        from druncschema.request_response_pb2 import Description
        from drunc.utils.grpc_utils import pack_to_any
        bd = self.describe_broadcast()
        d = Description(
            type = 'process_manager',
            name = self.name,
            info = self.configuration.log_path,
            session = 'no_session' if not self.session else self.session,
            commands = self.commands,
        )
        if bd:
            d.broadcast.CopyFrom(pack_to_any(bd))

        return Response(
            name = self.name,
            token = None,
            data = pack_to_any(d),
            flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
            children = [],
        )



    @abc.abstractmethod
    async def _logs_impl(self, req:Request, context) -> LogLine:
        raise NotImplementedError

    # ORDER MATTERS!
    @async_broadcasted # outer most wrapper 1st step
    @async_authentified_and_authorised(
        action=ActionType.READ,
        system=SystemType.PROCESS_MANAGER
    ) # 2nd step
    @async_unpack_request_data_to(LogRequest) # 3rd step
    async def logs(self, lr:LogRequest) -> Response:
        self.log.debug(f"Getting logs")
        try:
            async for r in self._logs_impl(lr):
                yield Response(
                    name = self.name,
                    token = None,
                    data = pack_to_any(r),
                    flag = ResponseFlag.EXECUTED_SUCCESSFULLY,
                    children = [],
                )
        except NotImplementedError:
            yield Response(
                name = self.name,
                token = None,
                data = None,
                flag = ResponseFlag.NOT_EXECUTED_NOT_IMPLEMENTED,
                children = [],
            )

    def _ensure_one_process(self, uuids:[str], in_boot_request:bool=False) -> str:
        if uuids == []:
            raise BadQuery(f'The process corresponding to the query doesn\'t exist')
        elif len(uuids)>1:
            raise BadQuery(f'There are more than 1 processes corresponding to the query')

        if in_boot_request:
            if not uuids[0] in self.boot_request:
                raise BadQuery(f'Couldn\'t find the process corresponding to the UUID {uuids[0]} in the boot requests')
        else:
            if not uuids[0] in self.process_store:
                raise BadQuery(f'Couldn\'t find the process corresponding to the UUID {uuids[0]} in the process store')
        return uuids[0]


    def _get_process_uid(self, query:ProcessQuery, in_boot_request:bool=False) -> [str]:
        import re

        uuid_selector = []
        name_selector = query.names
        user_selector = query.user
        session_selector = query.session
        # relevant reading here: https://github.com/protocolbuffers/protobuf/blob/main/docs/field_presence.md

        for uid in query.uuids:
            uuid_selector += [uid.uuid]

        processes = []
        all_the_uuids = self.process_store.keys() if not in_boot_request else self.boot_request.keys()

        for uuid in all_the_uuids:
            accepted = False
            meta = self.boot_request[uuid].process_description.metadata

            if uuid in uuid_selector: accepted = True

            for name_reg in name_selector:
                if re.search(name_reg, meta.name):
                    accepted = True

            if session_selector == meta.session: accepted = True

            if user_selector == meta.user: accepted = True

            if accepted: processes.append(uuid)

        return processes

    @staticmethod
    def get(conf, **kwargs):
        from drunc.utils.utils import get_logger
        log = get_logger("process_manager.get")

        if conf.data.type == ProcessManagerTypes.SSH:
            log.info(f'Starting [green]SSH process_manager[/green]', extra={'markup': True})
            from drunc.process_manager.ssh_process_manager import SSHProcessManager
            return SSHProcessManager(conf, **kwargs)
        elif conf.data.type == ProcessManagerTypes.K8s:
            log.info(f'Starting [green]K8s process_manager[/green]', extra={'markup': True})
            from drunc.process_manager.k8s_process_manager import K8sProcessManager
            return K8sProcessManager(conf, **kwargs)
        else:
            log.error(f'ProcessManager type {conf.get("type")} is unsupported!')
            raise RuntimeError(f'ProcessManager type {conf.get("type")} is unsupported!')


