import grpc
from concurrent import futures
import time
import pika
import json
from collections import defaultdict
from grpc_health.v1 import health_pb2, health_pb2_grpc
import water_quality_pb2
import water_quality_pb2_grpc
import threading


class WaterControlCenterServicer(water_quality_pb2_grpc.WaterControlCenterServicer):
    def __init__(self):
        self.stations = defaultdict(lambda: {
            "ph": 7.0,
            "turbidity": 5.0,
            "pollutants": 0.0,
            "neighbours": set(),
            "sensors": set()
        })
        self.received_issues = set()

        # RabbitMQ setup
        self.rabbit_connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        self.channel = self.rabbit_connection.channel()
        self.channel.exchange_declare(exchange='water_quality_updates', exchange_type='fanout')
        self.channel.exchange_declare(exchange='status_updates', exchange_type='fanout')

    def GetQualityData(self, request, context):
        station_id = request.station_id
        if station_id in self.stations:
            data = self.stations[station_id]
            return water_quality_pb2.StationResponse(
                station_id=station_id,
                pH=data["ph"],
                turbidity=data["turbidity"],
                pollutants=data["pollutants"]
            )
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f'Station {station_id} not found')
        return water_quality_pb2.StationResponse()

    def GetNeighbors(self, request, context):
        """New method for neighbor visualization"""
        if request.station_id in self.stations:
            return water_quality_pb2.NeighborList(
                station_id=request.station_id,
                neighbors=list(self.stations[request.station_id]["neighbours"])
            )
        context.set_code(grpc.StatusCode.NOT_FOUND)
        return water_quality_pb2.NeighborList()

    def ReportIssue(self, request, context):
        issue_key = f"{request.station_id}-{request.issue_type}-{int(request.timestamp // 10)}"

        if issue_key in self.received_issues:
            return water_quality_pb2.StatusResponse(
                message="Duplicate issue ignored",
                success=False
            )

        self.received_issues.add(issue_key)

        # Update station metrics
        if "Pollution" in request.issue_type:
            self.stations[request.station_id]["pollutants"] = 95.0
        elif "pH" in request.issue_type:
            self.stations[request.station_id]["ph"] = 5.5 if "low" in request.issue_type else 8.5
        elif "Turbulence" in request.issue_type:
            self.stations[request.station_id]["turbidity"] = 9.5

        # Publish to RabbitMQ
        self._publish_update({
            "type": "issue",
            "station_id": request.station_id,
            "issue_type": request.issue_type,
            "timestamp": request.timestamp
        })

        # Notify neighbors
        self.NotifyNeighbours(
            water_quality_pb2.NeighbourNotification(
                station_id=request.station_id,
                issue_type=request.issue_type
            ),
            context
        )

        return water_quality_pb2.StatusResponse(
            message=f"Issue '{request.issue_type}' reported",
            success=True
        )

    def AddNeighbour(self, request, context):
        station_id = request.station_id
        neighbour_id = request.neighbour_id

        # Input validation
        if not station_id or not neighbour_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return water_quality_pb2.StatusResponse(
                message="Both station_id and neighbour_id are required",
                success=False
            )

        if station_id == neighbour_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return water_quality_pb2.StatusResponse(
                message="Cannot add self as neighbor",
                success=False
            )

        # Check if stations exist
        if station_id not in self.stations:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return water_quality_pb2.StatusResponse(
                message=f"Station {station_id} not found",
                success=False
            )

        if neighbour_id not in self.stations:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return water_quality_pb2.StatusResponse(
                message=f"Neighbor station {neighbour_id} not found",
                success=False
            )

        # Add the neighbor relationship
        if neighbour_id not in self.stations[station_id]["neighbours"]:
            self.stations[station_id]["neighbours"].add(neighbour_id)
            self.stations[neighbour_id]["neighbours"].add(station_id)

            # Publish update
            self._publish_update({
                "type": "neighbour_update",
                "station_id": station_id,
                "neighbour_id": neighbour_id,
                "action": "added"
            })

        return water_quality_pb2.StatusResponse(
            message=f"Added {neighbour_id} as neighbour to {station_id}",
            success=True
        )

    def NotifyNeighbours(self, request, context):
        for neighbour_id in self.stations[request.station_id]["neighbours"]:
            print(f"Notifying {neighbour_id} about issue from {request.station_id}")
            self._publish_update({
                "type": "neighbour_alert",
                "origin_station": request.station_id,
                "target_station": neighbour_id,
                "issue_type": request.issue_type,
                "timestamp": time.time()
            })

        return water_quality_pb2.StatusResponse(
            message=f"Notified neighbors about {request.issue_type}",
            success=True
        )

    def RegisterStation(self, request, context):
        station_id = request.station_id

        if station_id in self.stations:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            return water_quality_pb2.RegisterStationResponse(
                message=f"Station {station_id} already exists",
                success=False
            )

        self.stations[station_id] = {
            "ph": 7.0,
            "turbidity": 5.0,
            "pollutants": 0.0,
            "neighbours": set(),
            "sensors": set()
        }

        self._publish_update({
            "type": "station_registered",
            "station_id": station_id,
            "timestamp": time.time()
        })

        return water_quality_pb2.RegisterStationResponse(
            message=f"Station {station_id} registered successfully",
            success=True
        )

    def _publish_update(self, message):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.rabbit_connection or self.rabbit_connection.is_closed:
                    self.rabbit_connection = pika.BlockingConnection(
                        pika.ConnectionParameters('localhost'))
                    self.channel = self.rabbit_connection.channel()
                    self.channel.exchange_declare(exchange='water_quality_updates', exchange_type='fanout')

                self.channel.basic_publish(
                    exchange='water_quality_updates',
                    routing_key='',
                    body=json.dumps(message)
                )
                return
            except (pika.exceptions.AMQPError, ConnectionResetError) as e:
                if attempt == max_retries - 1:
                    print(f"Failed to publish after {max_retries} attempts: {e}")
                time.sleep(1)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.max_connection_age_ms', 30000)
        ]
    )

    water_quality_pb2_grpc.add_WaterControlCenterServicer_to_server(
        WaterControlCenterServicer(), server)
    health_pb2_grpc.add_HealthServicer_to_server(
        health_pb2_grpc.HealthServicer(), server)

    server.add_insecure_port('[::]:50051')
    print("gRPC server running on [::]:50051")
    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        server.stop(0)


if __name__ == '__main__':
    serve()