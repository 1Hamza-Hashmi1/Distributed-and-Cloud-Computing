from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List
import asyncio
import json
import pika
import grpc
import water_quality_pb2
import water_quality_pb2_grpc
import time
import threading

app = FastAPI()
app.mount("/static", StaticFiles(directory="api/static"), name="static")


class GRPCClient:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = water_quality_pb2_grpc.WaterControlCenterStub(self.channel)

    def _convert_neighbors(self, neighbor_list):
        """Convert gRPC NeighborList to serializable format"""
        if neighbor_list:
            return {
                "station_id": neighbor_list.station_id,
                "neighbors": list(neighbor_list.neighbors)
            }
        return None

    def get_all_stations(self):
        stations = []
        for station_id in ["Station1", "Station2", "Station3"]:
            try:
                station = self.get_station(station_id)
                if station:
                    stations.append(station)
            except grpc.RpcError as e:
                print(f"gRPC error for {station_id}: {e}")
        return stations

    def get_station(self, station_id: str):
        try:
            request = water_quality_pb2.StationRequest(station_id=station_id)
            response = self.stub.GetQualityData(request)
            neighbors = self.get_neighbors(station_id)
            return {
                "id": response.station_id,
                "name": f"Station {response.station_id}",
                "coordinates": self._get_station_coordinates(response.station_id),
                "metrics": {
                    "ph": response.pH,
                    "turbidity": response.turbidity,
                    "pollutants": response.pollutants
                },
                "status": self._get_status(response.pollutants, response.pH, response.turbidity),
                "neighbors": neighbors["neighbors"] if neighbors else []
            }
        except grpc.RpcError as e:
            print(f"gRPC error getting station {station_id}: {e.code()}: {e.details()}")
            return None

    def get_neighbors(self, station_id: str):
        try:
            request = water_quality_pb2.StationRequest(station_id=station_id)
            neighbor_list = self.stub.GetNeighbors(request)
            return self._convert_neighbors(neighbor_list)
        except grpc.RpcError as e:
            print(f"gRPC error getting neighbors for {station_id}: {e}")
            return None

    def add_neighbor(self, station_id: str, neighbor_id: str):
        try:
            request = water_quality_pb2.AddNeighbourRequest(
                station_id=station_id,
                neighbour_id=neighbor_id
            )
            return self.stub.AddNeighbour(request)
        except grpc.RpcError as e:
            print(f"gRPC error adding neighbor: {e}")
            raise

    def _get_station_coordinates(self, station_id: str):
        coordinates_map = {
            "Station1": [43.6532, -79.3832],
            "Station2": [43.6512, -79.3682],
            "Station3": [43.6550, -79.3800]
        }
        return coordinates_map.get(station_id, [43.6532, -79.3832])

    def _get_status(self, pollutants: float, ph: float, turbidity: float):
        if pollutants > 90 or ph < 6 or ph > 8 or turbidity > 9:
            return "critical"
        elif pollutants > 70 or turbidity > 7:
            return "warning"
        return "normal"


grpc_client = GRPCClient()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


def setup_rabbitmq_consumer():
    def on_message(channel, method, properties, body):
        try:
            message = json.loads(body)
            print(f"Received RabbitMQ message: {message}")

            if message.get('type') == 'neighbor_update':
                asyncio.run(manager.broadcast(json.dumps({
                    "type": "neighbor_update",
                    "station_id": message.get("station_id"),
                    "neighbour_id": message.get("neighbour_id"),
                    "action": message.get("action")
                })))
            elif 'issue_type' in message:
                asyncio.run(manager.broadcast(json.dumps({
                    "type": "alert",
                    "data": {
                        "station_id": message["station_id"],
                        "message": message["issue_type"],
                        "timestamp": message["timestamp"]
                    }
                })))
            elif 'metrics' in message:
                asyncio.run(manager.broadcast(json.dumps({
                    "type": "sensor_update",
                    "data": {
                        "station_id": message["station_id"],
                        "metrics": message["metrics"],
                        "status": grpc_client._get_status(
                            message["metrics"].get("pollutants", 0),
                            message["metrics"].get("ph", 7),
                            message["metrics"].get("turbidity", 5)
                        )
                    }
                })))
        except Exception as e:
            print(f"Error processing RabbitMQ message: {e}")

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost', heartbeat=600))
        channel = connection.channel()

        channel.exchange_declare(exchange='water_quality_updates', exchange_type='fanout')
        queue = channel.queue_declare(queue='', exclusive=True).method.queue
        channel.queue_bind(exchange='water_quality_updates', queue=queue)

        channel.basic_consume(
            queue=queue,
            on_message_callback=on_message,
            auto_ack=True
        )

        thread = threading.Thread(target=channel.start_consuming)
        thread.daemon = True
        thread.start()
    except Exception as e:
        print(f"Failed to setup RabbitMQ consumer: {e}")


@app.on_event("startup")
async def startup_event():
    setup_rabbitmq_consumer()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("api/static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/api/stations")
async def get_all_stations():
    stations = grpc_client.get_all_stations()
    return {"stations": stations}


@app.get("/api/stations/{station_id}")
async def get_station(station_id: str):
    station = grpc_client.get_station(station_id)
    if station:
        return station
    raise HTTPException(status_code=404, detail="Station not found")


@app.get("/api/stations/{station_id}/neighbors")
async def get_neighbors(station_id: str):
    neighbors = grpc_client.get_neighbors(station_id)
    if neighbors:
        return neighbors
    raise HTTPException(status_code=404, detail="Failed to get neighbors")


@app.post("/api/stations/{station_id}/neighbors")
async def add_neighbor(station_id: str, neighbor: dict = Body(...)):
    try:
        # Input validation
        if not station_id or not neighbor.get("neighbor_id"):
            raise HTTPException(
                status_code=400,
                detail="Both station_id and neighbor_id are required"
            )

        if station_id == neighbor["neighbor_id"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot add self as neighbor"
            )

        # Call gRPC service
        request = water_quality_pb2.AddNeighbourRequest(
            station_id=station_id,
            neighbour_id=neighbor["neighbor_id"]
        )

        try:
            response = grpc_client.stub.AddNeighbour(request)

            if not response.success:
                raise HTTPException(
                    status_code=400,
                    detail=response.message
                )

            # Get updated neighbor list
            neighbors = grpc_client.get_neighbors(station_id)
            if not neighbors:
                raise HTTPException(
                    status_code=404,
                    detail="Failed to get updated neighbor list"
                )

            return JSONResponse({
                "status": "success",
                "message": response.message,
                "data": neighbors
            })

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(
                    status_code=404,
                    detail=str(e.details()))
            raise HTTPException(
                status_code=400,
                detail=str(e.details()))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add neighbor: {str(e)}"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)