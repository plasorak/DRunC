

class XxxTransition:
    def __init__(self, transition:Transition, pre_or_post = "pre"):
        self.transition = transition
        if pre_or_post not in ['pre', 'post']:
            from drunc.exceptions import DruncSetupException
            raise DruncSetupException(f"pre_or_post should be either 'pre' of 'post', you provided '{pre_or_post}'")

        self.prefix = pre_or_post

        self.sequence = []
        from logging import getLogger
        self._log = getLogger("PreOrPostTransitionSequence")

    def add_callback(self, action, mandatory=True):
        method = getattr(action, f'{self.prefix}_{self.transition.name}')

        if not method:
            from drunc.exceptions import DruncSetupException
            raise DruncSetupException(f'{self.prefix}_{self.transition.name} method not found in {action.name}')

        self.sequence += [
            Callback(
                method = method,
                mandatory = mandatory,
            )
        ]

    def __str__(self):
        return ', '.join([f'{cb.method.__name__} (mandatory={cb.mandatory})'for cb in self.sequence])


    def execute(self, transition_data, transition_args, ctx=None):
        self._log.debug(f'{transition_data=}, {transition_args=}')
        import json
        if not transition_data:
            transition_data = '{}'

        try:
            input_data = json.loads(transition_data)
        except:
            raise fsme.TransitionDataOfIncorrectFormat(transition_data)

        for callback in self.sequence:
            from drunc.exceptions import DruncException
            try:
                self._log.debug(f'data before callback: {input_data}')
                self._log.info(f'executing the callback: {callback.method.__name__} from {callback.method.__module__}')
                input_data = callback.method(_input_data=input_data, _context=ctx, **transition_args)
                self._log.debug(f'data after callback: {input_data}')
                from drunc.fsm.exceptions import InvalidDataReturnByFSMAction
                try:
                    import json
                    json.dumps(input_data)
                except TypeError as e:
                    raise InvalidDataReturnByFSMAction(input_data)

            except DruncException as e:
                import traceback
                self._log.error(traceback.format_exc())
                if callback.mandatory:
                    raise e

        self._log.debug(f'data returned: {input_data}')

        return json.dumps(input_data)

    def get_arguments(self):
        '''
        Creates a list of arguments
        This is a bit sloppy, as really, I shouldn't be using protobuf here, and convert them later, but...
        '''
        retr = []
        all_the_parameter_names = []

        from druncschema.controller_pb2 import Argument

        for callback in self.sequence:
            method = callback.method
            s = signature(method)

            for pname, p in s.parameters.items():

                if pname in ["_input_data", "_context", "args", "kwargs"]:
                    continue

                if pname in all_the_parameter_names:
                    raise fsme.DoubleArgument(f"Parameter {pname} is already in the list of parameters")
                all_the_parameter_names.append(p)

                default_value = ''

                t = Argument.Type.INT
                from druncschema.generic_pb2 import string_msg, float_msg, int_msg, bool_msg
                from drunc.utils.grpc_utils import pack_to_any

                if p.annotation is str:
                    t = Argument.Type.STRING

                    if p.default != Parameter.empty:
                        default_value = pack_to_any(string_msg(value = p.default))

                elif p.annotation is float:
                    t = Argument.Type.FLOAT

                    if p.default != Parameter.empty:
                        default_value = pack_to_any(float_msg(value = p.default))

                elif p.annotation is int:
                    t = Argument.Type.INT

                    if p.default != Parameter.empty:
                        default_value = pack_to_any(int_msg(value = p.default))

                elif p.annotation is bool:
                    t = Argument.Type.BOOL

                    if p.default != Parameter.empty:
                        default_value = pack_to_any(bool_msg(value = p.default))
                else:
                    raise fsme.UnhandledArgumentType(p.annotation)

                a = Argument(
                    name = p.name,
                    presence = Argument.Presence.MANDATORY if p.default == Parameter.empty else Argument.Presence.OPTIONAL,
                    type = t,
                    help = '',
                )

                if default_value:
                    a.default_value.CopyFrom(default_value)

                retr += [a]

        return retr




def PreTransition(XxxTransition):
    pass

def PostTransition(XxxTransition):
    pass

