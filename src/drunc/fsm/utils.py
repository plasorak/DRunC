import logging

# Good ol' moo import
from dunedaq.env import get_moo_model_path
import moo.io
moo.io.default_load_path = get_moo_model_path()
import moo.otypes
import moo.oschema as moosc
moo.otypes.load_types('rcif/cmd.jsonnet')
moo.otypes.load_types('cmdlib/cmd.jsonnet')
import dunedaq.rcif.cmd as rccmd
import dunedaq.cmdlib.cmd as cmd

from druncschema.controller_pb2 import Argument, FSMTransitionsDescription, FSMTransitionDescription

import drunc.fsm.exceptions as fsme
from drunc.utils.grpc_utils import unpack_any


def convert_fsm_transition(transitions):
    desc = FSMCommandsDescription()
    for t in transitions:
        desc.commands.append(
            FSMCommandDescription(
                name = t.id,
                data_type = ['controller_pb2.FSMCommand'],
                help = None,
                return_type = 'controller_pb2.FSMCommandResponse',
                arguments = t.arguments
            )
        )
    return desc


def decode_fsm_arguments(arguments, arguments_format):

    def get_argument(name, arguments):
        for n, k in arguments.items():
            if n == name:
                return k
        return None

    out_dict = {}
    for arg in arguments_format:
        arg_value = get_argument(arg.name, arguments)

        if arg.presence == Argument.Presence.MANDATORY and arg_value is None:
            raise fsme.MissingArgument(arg.name, '')

        if arg_value is None:
            arg_value = arg.default_value

        match arg.type:
            case Argument.Type.INT:
                out_dict[arg.name] = unpack_any(arg_value, int_msg).value
            case Argument.Type.FLOAT:
                out_dict[arg.name] = unpack_any(arg_value, float_msg).value
            case Argument.Type.STRING:
                out_dict[arg.name] = unpack_any(arg_value, string_msg).value
            case Argument.Type.BOOL:
                out_dict[arg.name] = unpack_any(arg_value, bool_msg).value
            case _:
                raise fsme.UnhandledArgumentType(arg.type)
    l = logging.getLogger('decode_fsm_arguments')
    l.debug(f'Parsed FSM arguments: {out_dict}')
    return out_dict


def convert_rcif_type_to_protobuf(rcif_type:dict) -> str:
    if rcif_type in ["i2", "i4", "i8", "u2", "u4", "u8"]:
        return "int"
    elif rcif_type == "string":
        return "string"
    elif rcif_type in ["f4", "f8"]:
        return "double"
    elif rcif_type == "boolean":
        return "boolean"
    else:
        raise fsme.UnhandledArgumentType(rcif_type)


def get_underlying_schema(field_ost:dict) -> str:

    if field_ost.get('dtype'):
        return convert_rcif_type_to_protobuf(field_ost['dtype'])

    if field_ost.get('item'):
        underlying_schema_name = field_ost['item'].split('.')[-1]
        underlying_schema = getattr(rccmd, underlying_schema_name, None)
        if underlying_schema is None:
            raise fsme.SchemaNotSupportedByRCIF(underlying_schema_name)

        underlying_schema_ost = underlying_schema.__dict__["_ost"]

        if underlying_schema_ost.get('item'):
            return get_underlying_schema(underlying_schema)

        if 'dtype' in underlying_schema_ost:
            return convert_rcif_type_to_protobuf(underlying_schema_ost['dtype'])
        if 'schema' in underlying_schema_ost:
            return convert_rcif_type_to_protobuf(underlying_schema_ost['schema'])



def build_arguments_from_rcif(rcif_schema:str) -> [Argument]:
    log = logging.getLogger('build_arguments_from_rcif')

    if rcif_schema == "":
        return []

    log.debug(f'Parsing the rcif_schema: \'{rcif_schema}\'')

    schema = getattr(rccmd, rcif_schema, None)
    if schema is None:
        raise fsme.SchemaNotSupportedByRCIF(rcif_schema)

    arguments = []

    for field in schema.__dict__["_ost"]["fields"]:
        log.debug(f" - field {field}")
        arg_type = get_underlying_schema(field)
        log.debug(f"   ... of type \'{arg_type}\'")

        arg_kwargs = {
            "name": field['name'],
            "type": arg_type,
            "help": field['doc'],
            "mandatory": not field.get('optional', False),
        }

        if 'choices' in field:
            arg_kwargs.update({
                f"{arg_type}_choices": field['choices'],
            })

        if 'default' in field:
            arg_kwargs.update({
                f"{arg_type}_default": field['default'],
            })

        a = Argument(**arg_kwargs)

        log.debug(f"Argument produced:\n{a}")
        default_arg = getattr(a, arg_type+"_default")
        arguments += [a]
    return arguments
