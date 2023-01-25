# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: controller.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10\x63ontroller.proto\x12\x05\x44runc\"J\n\x04Ping\x12\x17\n\x0f\x63ontrolled_name\x18\x01 \x01(\t\x12\x17\n\x0f\x63ontroller_name\x18\x02 \x01(\t\x12\x10\n\x08\x64\x61tetime\x18\x03 \x01(\t\"\x19\n\x06\x43lient\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\" \n\x10\x42roadcastMessage\x12\x0c\n\x04text\x18\x01 \x01(\t\"A\n\x04Node\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\x12\x1d\n\x08\x63hildren\x18\x03 \x03(\x0b\x32\x0b.Drunc.Node\",\n\x0b\x43ontrolTree\x12\x1d\n\x08top_node\x18\x01 \x01(\x0b\x32\x0b.Drunc.Node\"\x8e\x01\n\x08\x41rgument\x12\x0c\n\x04name\x18\x01 \x01(\t\x12*\n\x04type\x18\x02 \x01(\x0e\x32\x1c.Drunc.Argument.ArgumentType\x12\r\n\x05\x64\x65\x66lt\x18\x03 \x01(\t\x12\x0c\n\x04help\x18\x04 \x01(\t\"+\n\x0c\x41rgumentType\x12\r\n\tMANDATORY\x10\x00\x12\x0c\n\x08OPTIONAL\x10\x01\"V\n\x14\x43ommandSpecification\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\"\n\targuments\x18\x02 \x03(\x0b\x32\x0f.Drunc.Argument\x12\x0c\n\x04help\x18\x03 \x01(\t\">\n\x0eListOfCommands\x12,\n\x07\x63ommand\x18\x01 \x03(\x0b\x32\x1b.Drunc.CommandSpecification\"\x91\x01\n\x07\x43ommand\x12,\n\x07\x63ommand\x18\x01 \x01(\x0b\x32\x1b.Drunc.CommandSpecification\x12\x14\n\x0c\x63ommand_data\x18\x02 \x01(\t\x12\x17\n\x0f\x63ontrolled_name\x18\x03 \x01(\t\x12\x17\n\x0f\x63ontroller_name\x18\x04 \x01(\t\x12\x10\n\x08\x64\x61tetime\x18\x05 \x01(\t\"K\n\x0c\x43hildCommand\x12\x1f\n\x07\x63ommand\x18\x01 \x01(\x0b\x32\x0e.Drunc.Command\x12\x1a\n\x05\x63hild\x18\x02 \x01(\x0b\x32\x0b.Drunc.Node\"\xaf\x02\n\x0f\x43ommandResponse\x12:\n\rresponse_code\x18\x01 \x01(\x0e\x32#.Drunc.CommandResponse.ResponseCode\x12\x15\n\rresponse_text\x18\x02 \x01(\t\x12,\n\x07\x63ommand\x18\x03 \x01(\x0b\x32\x1b.Drunc.CommandSpecification\x12\x14\n\x0c\x63ommand_data\x18\x04 \x01(\t\x12\x17\n\x0f\x63ontrolled_name\x18\x05 \x01(\t\x12\x17\n\x0f\x63ontroller_name\x18\x06 \x01(\t\x12\x10\n\x08\x64\x61tetime\x18\x07 \x01(\t\"A\n\x0cResponseCode\x12\x07\n\x03\x41\x43K\x10\x00\x12\x08\n\x04\x44ONE\x10\x01\x12\n\n\x06\x46\x41ILED\x10\x02\x12\x12\n\x0eNOT_AUTHORISED\x10\x03\x32\xd0\x02\n\nController\x12\x35\n\x10get_control_tree\x12\x0b.Drunc.Ping\x1a\x12.Drunc.ControlTree\"\x00\x12>\n\x16get_available_commands\x12\x0b.Drunc.Ping\x1a\x15.Drunc.ListOfCommands\"\x00\x12=\n\x0f\x65xecute_command\x12\x0e.Drunc.Command\x1a\x16.Drunc.CommandResponse\"\x00\x30\x01\x12K\n\x18\x65xecute_command_on_child\x12\x13.Drunc.ChildCommand\x1a\x16.Drunc.CommandResponse\"\x00\x30\x01\x12?\n\x11request_broadcast\x12\r.Drunc.Client\x1a\x17.Drunc.BroadcastMessage\"\x00\x30\x01\x32\x35\n\rPingProcessor\x12$\n\x04ping\x12\x0b.Drunc.Ping\x1a\x0b.Drunc.Ping\"\x00\x30\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'controller_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PING._serialized_start=27
  _PING._serialized_end=101
  _CLIENT._serialized_start=103
  _CLIENT._serialized_end=128
  _BROADCASTMESSAGE._serialized_start=130
  _BROADCASTMESSAGE._serialized_end=162
  _NODE._serialized_start=164
  _NODE._serialized_end=229
  _CONTROLTREE._serialized_start=231
  _CONTROLTREE._serialized_end=275
  _ARGUMENT._serialized_start=278
  _ARGUMENT._serialized_end=420
  _ARGUMENT_ARGUMENTTYPE._serialized_start=377
  _ARGUMENT_ARGUMENTTYPE._serialized_end=420
  _COMMANDSPECIFICATION._serialized_start=422
  _COMMANDSPECIFICATION._serialized_end=508
  _LISTOFCOMMANDS._serialized_start=510
  _LISTOFCOMMANDS._serialized_end=572
  _COMMAND._serialized_start=575
  _COMMAND._serialized_end=720
  _CHILDCOMMAND._serialized_start=722
  _CHILDCOMMAND._serialized_end=797
  _COMMANDRESPONSE._serialized_start=800
  _COMMANDRESPONSE._serialized_end=1103
  _COMMANDRESPONSE_RESPONSECODE._serialized_start=1038
  _COMMANDRESPONSE_RESPONSECODE._serialized_end=1103
  _CONTROLLER._serialized_start=1106
  _CONTROLLER._serialized_end=1442
  _PINGPROCESSOR._serialized_start=1444
  _PINGPROCESSOR._serialized_end=1497
# @@protoc_insertion_point(module_scope)
