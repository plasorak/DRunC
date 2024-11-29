from google.protobuf import any_pb2
import grpc
from grpc_status import rpc_status
import logging

from druncschema.controller_pb2 import Status
from druncschema.generic_pb2 import Stacktrace, PlainText
from druncschema.request_response_pb2 import Response, ResponseFlag, Request
from druncschema.token_pb2 import Token

from drunc.stateful import Stateful
from drunc.utils.grpc_utils import pack_to_any
from drunc.utils.grpc_utils import rethrow_if_unreachable_server, unpack_any

log = logging.getLogger('controller_utils')


def get_status_message(stateful:Stateful):
    state_string = stateful.get_node_operational_state()
    if state_string != stateful.get_node_operational_sub_state():
        state_string += f' ({stateful.get_node_operational_sub_state()})'

    return Status(
        state = state_string,
        sub_state = stateful.get_node_operational_sub_state(),
        in_error = stateful.node_is_in_error(),
        included = stateful.node_is_included(),
    )

def get_detector_name(configuration) -> str:
    detector_name = None
    if hasattr(configuration.data, "contains") and len(configuration.data.contains) > 0:
        if len(configuration.data.contains) > 0:
            log.debug(f"Application {configuration.data.id} has multiple contains, using the first one")
        detector_name = configuration.data.contains[0].id.replace("-", "_").replace("_", " ")
    else:
        log.debug(f"Application {configuration.data.id} has no \"contains\" relation, hence no detector")
    return detector_name

def send_command(controller, token, command:str, data=None, rethrow=False):

    log = logging.getLogger("send_command")

    # Grab the command from the controller stub in the context
    # Add the token to the data (which can be of any protobuf type)
    # Send the command to the controller

    if not controller:
        raise RuntimeError('No controller initialised')

    cmd = getattr(controller, command) # this throws if the command doesn't exist

    request = Request(
        token = token,
    )

    try:
        if data:
            data_detail = any_pb2.Any()
            data_detail.Pack(data)
            request.data.CopyFrom(data_detail)

        log.debug(f'Sending: {command} to the controller, with {request=}')

        response = cmd(request)
    except grpc.RpcError as e:
        rethrow_if_unreachable_server(e)

        status = rpc_status.from_call(e)

        log.error(f'Error sending command "{command}" to controller')

        if hasattr(status, 'message'):
            log.error(status.message)

        if hasattr(status, 'details'):
            for detail in status.details:
                if detail.Is(Stacktrace.DESCRIPTOR):
                    # text = '[bold red]Stacktrace on remote server![/bold red]\n' # Temporary - bold red doesn't work
                    text = 'Stacktrace on remote server!\n'
                    stack = unpack_any(detail, Stacktrace)
                    for l in stack.text:
                        text += l+"\n"
                    log.error(text, extra={"markup": True})
                elif detail.Is(PlainText.DESCRIPTOR):
                    txt = unpack_any(detail, PlainText)
                    log.error(txt)

        if rethrow:
            raise e
        return None

    return response

def get_segment_from_controller_id(segment_configuration, controller_id):
    if segment_configuration.controller.id == controller_id:
        return segment_configuration

    for segment in segment_configuration.segments:
        if get_segment_from_controller_id(segment, controller_id) is not None:
            return segment

    return None