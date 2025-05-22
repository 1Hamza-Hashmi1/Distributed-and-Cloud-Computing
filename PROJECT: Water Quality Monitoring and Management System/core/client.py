import grpc
import time
import threading
import sys
import water_quality_pb2
import water_quality_pb2_grpc
from core import sensor


class WaterMonitoringStation:
    def __init__(self, station_id, server_address):
        self.station_id = station_id
        self.server_address = server_address
        self.channel = grpc.insecure_channel(
            server_address,
            options=[('grpc.keepalive_time_ms', 10000)]
        )
        self.stub = water_quality_pb2_grpc.WaterControlCenterStub(self.channel)
        self.sensors = [
            sensor.Sensor(f"{self.station_id}-1", self, count=0),
            sensor.Sensor(f"{self.station_id}-2", self, count=0)
        ]
        self.neighbors = set()
        self.register_station()

    def register_station(self):
        request = water_quality_pb2.RegisterStationRequest(station_id=self.station_id)
        try:
            response = self.stub.RegisterStation(request)
            print(f"Station {self.station_id} registration: {response.message}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                print(f"Station {self.station_id} already registered")
            else:
                print(f"Registration failed for {self.station_id}: {e}")

    def add_neighbor(self, neighbor_id: str):
        """Establish neighbor relationship with another station"""
        if neighbor_id == self.station_id:
            print("Cannot add self as neighbor")
            return None

        request = water_quality_pb2.AddNeighbourRequest(
            station_id=self.station_id,
            neighbour_id=neighbor_id
        )
        try:
            response = self.stub.AddNeighbour(request)
            if response.success:
                self.neighbors.add(neighbor_id)
                print(f"Added {neighbor_id} as neighbor to {self.station_id}")
            return response
        except grpc.RpcError as e:
            print(f"Failed to add neighbor {neighbor_id}: {e}")
            return None

    def get_neighbors(self):
        """Fetch current list of neighbors"""
        request = water_quality_pb2.StationRequest(station_id=self.station_id)
        try:
            response = self.stub.GetNeighbors(request)
            self.neighbors = set(response.neighbors)
            return list(self.neighbors)
        except grpc.RpcError as e:
            print(f"Failed to get neighbors: {e}")
            return []

    def notify_neighbors(self, issue_type: str):
        """Alert all neighbor stations about an issue"""
        if not self.neighbors:
            return

        request = water_quality_pb2.NeighbourNotification(
            station_id=self.station_id,
            issue_type=issue_type
        )
        try:
            response = self.stub.NotifyNeighbours(request)
            print(f"Neighbor notification status: {response.message}")
        except grpc.RpcError as e:
            print(f"Failed to notify neighbors: {e}")

    def run_sensors(self):
        """Main execution loop for sensor monitoring"""
        while True:
            threads = []
            for s in self.sensors:
                t = threading.Thread(target=s.check_contaminants)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            time.sleep(10)  # Check every 10 seconds


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python -m core.client <station_id>")
        print("Example: python -m core.client Station2")
        sys.exit(1)

    station = WaterMonitoringStation(sys.argv[1], "localhost:50051")

    try:
        # Initialize with existing neighbors
        station.get_neighbors()

        # Start sensor monitoring
        station.run_sensors()
    except KeyboardInterrupt:
        print(f"\nShutting down {sys.argv[1]}...")
        station.channel.close()