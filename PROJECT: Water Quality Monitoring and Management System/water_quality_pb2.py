# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: water_quality.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'water_quality.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13water_quality.proto\x12\x0cwaterquality\"@\n\x0bQualityData\x12\n\n\x02pH\x18\x01 \x01(\x02\x12\x11\n\tturbidity\x18\x02 \x01(\x02\x12\x12\n\npollutants\x18\x03 \x01(\x02\"$\n\x0eStationRequest\x12\x12\n\nstation_id\x18\x01 \x01(\t\"X\n\x0fStationResponse\x12\x12\n\nstation_id\x18\x01 \x01(\t\x12\n\n\x02pH\x18\x02 \x01(\x02\x12\x11\n\tturbidity\x18\x03 \x01(\x02\x12\x12\n\npollutants\x18\x04 \x01(\x02\"5\n\x0cNeighborList\x12\x12\n\nstation_id\x18\x01 \x01(\t\x12\x11\n\tneighbors\x18\x02 \x03(\t\"H\n\x0bIssueReport\x12\x12\n\nstation_id\x18\x01 \x01(\t\x12\x12\n\nissue_type\x18\x02 \x01(\t\x12\x11\n\ttimestamp\x18\x03 \x01(\x01\"2\n\x0eStatusResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\"?\n\x13\x41\x64\x64NeighbourRequest\x12\x12\n\nstation_id\x18\x01 \x01(\t\x12\x14\n\x0cneighbour_id\x18\x02 \x01(\t\"?\n\x15NeighbourNotification\x12\x12\n\nstation_id\x18\x01 \x01(\t\x12\x12\n\nissue_type\x18\x02 \x01(\t\",\n\x16RegisterStationRequest\x12\x12\n\nstation_id\x18\x01 \x01(\t\";\n\x17RegisterStationResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\x32\xfd\x03\n\x12WaterControlCenter\x12M\n\x0eGetQualityData\x12\x1c.waterquality.StationRequest\x1a\x1d.waterquality.StationResponse\x12\x46\n\x0bReportIssue\x12\x19.waterquality.IssueReport\x1a\x1c.waterquality.StatusResponse\x12O\n\x0c\x41\x64\x64Neighbour\x12!.waterquality.AddNeighbourRequest\x1a\x1c.waterquality.StatusResponse\x12U\n\x10NotifyNeighbours\x12#.waterquality.NeighbourNotification\x1a\x1c.waterquality.StatusResponse\x12^\n\x0fRegisterStation\x12$.waterquality.RegisterStationRequest\x1a%.waterquality.RegisterStationResponse\x12H\n\x0cGetNeighbors\x12\x1c.waterquality.StationRequest\x1a\x1a.waterquality.NeighborListb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'water_quality_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_QUALITYDATA']._serialized_start=37
  _globals['_QUALITYDATA']._serialized_end=101
  _globals['_STATIONREQUEST']._serialized_start=103
  _globals['_STATIONREQUEST']._serialized_end=139
  _globals['_STATIONRESPONSE']._serialized_start=141
  _globals['_STATIONRESPONSE']._serialized_end=229
  _globals['_NEIGHBORLIST']._serialized_start=231
  _globals['_NEIGHBORLIST']._serialized_end=284
  _globals['_ISSUEREPORT']._serialized_start=286
  _globals['_ISSUEREPORT']._serialized_end=358
  _globals['_STATUSRESPONSE']._serialized_start=360
  _globals['_STATUSRESPONSE']._serialized_end=410
  _globals['_ADDNEIGHBOURREQUEST']._serialized_start=412
  _globals['_ADDNEIGHBOURREQUEST']._serialized_end=475
  _globals['_NEIGHBOURNOTIFICATION']._serialized_start=477
  _globals['_NEIGHBOURNOTIFICATION']._serialized_end=540
  _globals['_REGISTERSTATIONREQUEST']._serialized_start=542
  _globals['_REGISTERSTATIONREQUEST']._serialized_end=586
  _globals['_REGISTERSTATIONRESPONSE']._serialized_start=588
  _globals['_REGISTERSTATIONRESPONSE']._serialized_end=647
  _globals['_WATERCONTROLCENTER']._serialized_start=650
  _globals['_WATERCONTROLCENTER']._serialized_end=1159
# @@protoc_insertion_point(module_scope)
