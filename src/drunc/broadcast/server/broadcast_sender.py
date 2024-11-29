from logging import getLogger
from google.rpc import code_pb2
from google.rpc import code_pb2

from druncschema.broadcast_pb2 import BroadcastMessage, Emitter, BroadcastType
from druncschema.generic_pb2 import PlainText

from drunc.broadcast.server.kafka_sender import KafkaSender
from drunc.broadcast.types import BroadcastTypes
from drunc.broadcast.utils import broadcast_types_loglevels, get_broadcast_level_from_broadcast_type
from drunc.exceptions import DruncException, DruncSetupException
from drunc.utils.grpc_utils import pack_to_any


class BroadcastSender:

    implementation = None

    def __init__(self, name:str, configuration, session:str='no_session'):
        super().__init__()

        self.configuration = configuration

        self.name = name
        self.session = session
        self.identifier = f'{self.session}.{self.name}'

        self.logger = getLogger('Broadcast')

        self.logger.info('Initialising broadcast')

        self.broadcast_types_loglevels = broadcast_types_loglevels

        # TODO
        # self.broadcast_types_loglevels.update(self.configuration.get_raw('broadcast_types_loglevels', {}))

        self.impl_technology = BroadcastTypes.from_str(self.configuration.dal.type)

        self.implementation = None

        if self.impl_technology == BroadcastTypes.Unknown:
            self.logger.info('There is no broadcasting service!')
            return

        match self.impl_technology:
            case BroadcastTypes.Kafka:
                self.implementation = KafkaSender(
                    self.configuration.dal.address,
                    self.configuration.dal.publish_timeout,
                    topic=f'control.{self.identifier}',
                )
            case _:
                raise DruncSetupException(f"Broadcaster cannot be {self.impl_technology}")

    def describe_broadcast(self):
        if self.implementation:
            return self.implementation.describe_broadcast()
        else:
            return None

    def can_broadcast(self):
        if not self.implementation:
            return False

        return self.implementation.can_broadcast()

    def broadcast(self, message, btype):

        if self.logger:
            get_broadcast_level_from_broadcast_type(btype, self.logger, self.broadcast_types_loglevels)(message)

        if self.implementation is None:
            # nice and easy case
            return


        any = pack_to_any(PlainText(text=message))
        emitter = Emitter(
            process = self.name,
            session = self.session,
        )
        bm = BroadcastMessage(
            emitter = emitter,
            type = btype,
            data = any,
        )
        bm.type = btype

        self.implementation._send(bm)


    def _interrupt_with_exception(self, exception, context, stack=''):
        txt = f'\'{exception.__class__.__name__}\' exception thrown: {exception}'

        self.broadcast(
            btype = BroadcastType.DRUNC_EXCEPTION_RAISED if isinstance(exception, DruncException) else BroadcastType.UNHANDLED_EXCEPTION_RAISED,
            message = txt,
        )

        if stack:
            txt += '\n\n'+stack

        error_code = getattr(exception, 'grpc_error_code', code_pb2.INTERNAL)
        context.abort(
            code = error_code,
            details = txt,
        )


    async def _async_interrupt_with_exception(self, exception, context, stack=''):
        txt = f'\'{exception.__class__.__name__}\' exception thrown: {exception}'

        self.broadcast(
            btype = BroadcastType.DRUNC_EXCEPTION_RAISED if isinstance(exception, DruncException) else BroadcastType.UNHANDLED_EXCEPTION_RAISED,
            message = txt,
        )

        if stack:
            txt += '\n\n'+stack

        error_code = getattr(exception, 'grpc_error_code', code_pb2.INTERNAL)
        await context.abort(
            code = error_code,
            details = txt,
        )