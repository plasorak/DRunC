"""The session manager service."""

from druncschema.request_response_pb2 import CommandDescription, Description, Response, ResponseFlag
from druncschema.session_manager_pb2_grpc import SessionManagerServicer
from druncschema.token_pb2 import Token

from drunc.utils.grpc_utils import pack_to_any, unpack_request_data_to
from drunc.utils.utils import pid_info_str

import abc
import logging

class SessionManager(abc.ABC, SessionManagerServicer):

    def __init__(self, configuration, name: str, session: str, **kwargs):
        super().__init__()

        self.log = logging.getLogger("drunc.session_manager")
        self.log.debug(pid_info_str())
        self.log.debug("Initialized SessionManager")

        self.name = name
        self.session = session
        self.configuration = configuration

    @unpack_request_data_to(None, pass_token=True)
    def describe(self, token: Token) -> Response:
        self.log.debug(f"{self.name} running describe")

        command_descriptions = [
            CommandDescription(
                name="describe",
                data_type=["None"],
                help="Describe self (return a list of commands, the type of endpoint, the name and session).",
                return_type="request_response_pb2.Description",
            ),
            CommandDescription(
                name="list_all_sessions",
                data_type=["None"],
                help="List all active sessions.",
                return_type="session_manager_pb2.AllActiveSessions",
            ),
            CommandDescription(
                name="list_all_configs",
                data_type=["None"],
                help="List all available configurations.",
                return_type="session_manager_pb2.AllConfigKeys",
            ),
        ]

        description = Description(
            type="session_manager",
            name=self.name,
            session="no_session" if not self.session else self.session,
            commands=command_descriptions,
        )

        return Response(
            name=self.name,
            token=None,
            data=pack_to_any(description),
            flag=ResponseFlag.EXECUTED_SUCCESSFULLY,
            children=[],
        )

    @unpack_request_data_to(None, pass_token=True)
    def list_all_sessions(self, token: Token) -> Response:
        self.log.debug(f"{self.name} running list_all_sessions")

        sessions = None

        return Response(
            name=self.name,
            token=None,
            data=pack_to_any(sessions),
            flag=ResponseFlag.EXECUTED_SUCCESSFULLY,
            children=[],
        )

    # TODO: next PR.
    # @unpack_request_data_to(None, pass_token=True)
    # def list_all_configs(self, token: Token) -> Response:
    #     pass
