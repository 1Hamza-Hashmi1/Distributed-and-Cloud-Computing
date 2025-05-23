# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import rover_pb2 as rover__pb2

GRPC_GENERATED_VERSION = '1.70.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in rover_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class GroundControlStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetMap = channel.unary_unary(
                '/rover.GroundControl/GetMap',
                request_serializer=rover__pb2.RoverRequest.SerializeToString,
                response_deserializer=rover__pb2.MapResponse.FromString,
                _registered_method=True)
        self.GetCommands = channel.unary_stream(
                '/rover.GroundControl/GetCommands',
                request_serializer=rover__pb2.RoverRequest.SerializeToString,
                response_deserializer=rover__pb2.CommandResponse.FromString,
                _registered_method=True)
        self.GetMineSerialNumber = channel.unary_unary(
                '/rover.GroundControl/GetMineSerialNumber',
                request_serializer=rover__pb2.RoverRequest.SerializeToString,
                response_deserializer=rover__pb2.MineSerialResponse.FromString,
                _registered_method=True)


class GroundControlServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetMap(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetCommands(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMineSerialNumber(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_GroundControlServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetMap': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMap,
                    request_deserializer=rover__pb2.RoverRequest.FromString,
                    response_serializer=rover__pb2.MapResponse.SerializeToString,
            ),
            'GetCommands': grpc.unary_stream_rpc_method_handler(
                    servicer.GetCommands,
                    request_deserializer=rover__pb2.RoverRequest.FromString,
                    response_serializer=rover__pb2.CommandResponse.SerializeToString,
            ),
            'GetMineSerialNumber': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMineSerialNumber,
                    request_deserializer=rover__pb2.RoverRequest.FromString,
                    response_serializer=rover__pb2.MineSerialResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'rover.GroundControl', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('rover.GroundControl', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class GroundControl(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetMap(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/rover.GroundControl/GetMap',
            rover__pb2.RoverRequest.SerializeToString,
            rover__pb2.MapResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetCommands(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/rover.GroundControl/GetCommands',
            rover__pb2.RoverRequest.SerializeToString,
            rover__pb2.CommandResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetMineSerialNumber(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/rover.GroundControl/GetMineSerialNumber',
            rover__pb2.RoverRequest.SerializeToString,
            rover__pb2.MineSerialResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
