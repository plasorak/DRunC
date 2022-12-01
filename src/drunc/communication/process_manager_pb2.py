# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: process_manager.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15process_manager.proto\x12\x12\x44UNEProcessManager\"G\n\x12ProcessRestriction\x12\x15\n\rallowed_hosts\x18\x01 \x03(\t\x12\x1a\n\x12\x61llowed_host_types\x18\x02 \x03(\t\"\x1b\n\x0bProcessUUID\x12\x0c\n\x04uuid\x18\x01 \x01(\t\"o\n\x0fProcessMetadata\x12-\n\x04uuid\x18\x01 \x01(\x0b\x32\x1f.DUNEProcessManager.ProcessUUID\x12\x0c\n\x04user\x18\x02 \x01(\t\x12\x11\n\tpartition\x18\x03 \x01(\t\x12\x0c\n\x04name\x18\x04 \x01(\t\"\xc3\x04\n\x12ProcessDescription\x12\x35\n\x08metadata\x18\x01 \x01(\x0b\x32#.DUNEProcessManager.ProcessMetadata\x12<\n\x03\x65nv\x18\x02 \x03(\x0b\x32/.DUNEProcessManager.ProcessDescription.EnvEntry\x12\x64\n\x18\x65xecutable_and_arguments\x18\x03 \x03(\x0b\x32\x42.DUNEProcessManager.ProcessDescription.ExecutableAndArgumentsEntry\x12[\n\x13runtime_environment\x18\x04 \x03(\x0b\x32>.DUNEProcessManager.ProcessDescription.RuntimeEnvironmentEntry\x1a\x1c\n\nStringList\x12\x0e\n\x06values\x18\x01 \x03(\t\x1a*\n\x08\x45nvEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1ap\n\x1b\x45xecutableAndArgumentsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12@\n\x05value\x18\x02 \x01(\x0b\x32\x31.DUNEProcessManager.ProcessDescription.StringList:\x02\x38\x01\x1a\x39\n\x17RuntimeEnvironmentEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\xb4\x02\n\x0fProcessInstance\x12\x43\n\x13process_description\x18\x01 \x01(\x0b\x32&.DUNEProcessManager.ProcessDescription\x12\x43\n\x13process_restriction\x18\x02 \x01(\x0b\x32&.DUNEProcessManager.ProcessRestriction\x12\x43\n\x0bstatus_code\x18\x03 \x01(\x0e\x32..DUNEProcessManager.ProcessInstance.StatusCode\x12-\n\x04uuid\x18\x04 \x01(\x0b\x32\x1f.DUNEProcessManager.ProcessUUID\"#\n\nStatusCode\x12\x0b\n\x07RUNNING\x10\x00\x12\x08\n\x04\x44\x45\x41\x44\x10\x01\"J\n\x13ProcessInstanceList\x12\x33\n\x06values\x18\x01 \x03(\x0b\x32#.DUNEProcessManager.ProcessInstance\"\x97\x01\n\x0b\x42ootRequest\x12\x43\n\x13process_description\x18\x01 \x01(\x0b\x32&.DUNEProcessManager.ProcessDescription\x12\x43\n\x13process_restriction\x18\x02 \x01(\x0b\x32&.DUNEProcessManager.ProcessRestriction2\xda\x04\n\x0eProcessManager\x12J\n\x04\x62oot\x12\x1f.DUNEProcessManager.BootRequest\x1a\x1f.DUNEProcessManager.ProcessUUID\"\x00\x12S\n\tresurrect\x12\x1f.DUNEProcessManager.ProcessUUID\x1a#.DUNEProcessManager.ProcessInstance\"\x00\x12Q\n\x07restart\x12\x1f.DUNEProcessManager.ProcessUUID\x1a#.DUNEProcessManager.ProcessInstance\"\x00\x12R\n\x08is_alive\x12\x1f.DUNEProcessManager.ProcessUUID\x1a#.DUNEProcessManager.ProcessInstance\"\x00\x12N\n\x04kill\x12\x1f.DUNEProcessManager.ProcessUUID\x1a#.DUNEProcessManager.ProcessInstance\"\x00\x12P\n\x04poll\x12\x1f.DUNEProcessManager.ProcessUUID\x1a#.DUNEProcessManager.ProcessInstance\"\x00\x30\x01\x12^\n\x0clist_process\x12#.DUNEProcessManager.ProcessMetadata\x1a\'.DUNEProcessManager.ProcessInstanceList\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'process_manager_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PROCESSDESCRIPTION_ENVENTRY._options = None
  _PROCESSDESCRIPTION_ENVENTRY._serialized_options = b'8\001'
  _PROCESSDESCRIPTION_EXECUTABLEANDARGUMENTSENTRY._options = None
  _PROCESSDESCRIPTION_EXECUTABLEANDARGUMENTSENTRY._serialized_options = b'8\001'
  _PROCESSDESCRIPTION_RUNTIMEENVIRONMENTENTRY._options = None
  _PROCESSDESCRIPTION_RUNTIMEENVIRONMENTENTRY._serialized_options = b'8\001'
  _PROCESSRESTRICTION._serialized_start=45
  _PROCESSRESTRICTION._serialized_end=116
  _PROCESSUUID._serialized_start=118
  _PROCESSUUID._serialized_end=145
  _PROCESSMETADATA._serialized_start=147
  _PROCESSMETADATA._serialized_end=258
  _PROCESSDESCRIPTION._serialized_start=261
  _PROCESSDESCRIPTION._serialized_end=840
  _PROCESSDESCRIPTION_STRINGLIST._serialized_start=595
  _PROCESSDESCRIPTION_STRINGLIST._serialized_end=623
  _PROCESSDESCRIPTION_ENVENTRY._serialized_start=625
  _PROCESSDESCRIPTION_ENVENTRY._serialized_end=667
  _PROCESSDESCRIPTION_EXECUTABLEANDARGUMENTSENTRY._serialized_start=669
  _PROCESSDESCRIPTION_EXECUTABLEANDARGUMENTSENTRY._serialized_end=781
  _PROCESSDESCRIPTION_RUNTIMEENVIRONMENTENTRY._serialized_start=783
  _PROCESSDESCRIPTION_RUNTIMEENVIRONMENTENTRY._serialized_end=840
  _PROCESSINSTANCE._serialized_start=843
  _PROCESSINSTANCE._serialized_end=1151
  _PROCESSINSTANCE_STATUSCODE._serialized_start=1116
  _PROCESSINSTANCE_STATUSCODE._serialized_end=1151
  _PROCESSINSTANCELIST._serialized_start=1153
  _PROCESSINSTANCELIST._serialized_end=1227
  _BOOTREQUEST._serialized_start=1230
  _BOOTREQUEST._serialized_end=1381
  _PROCESSMANAGER._serialized_start=1384
  _PROCESSMANAGER._serialized_end=1986
# @@protoc_insertion_point(module_scope)
