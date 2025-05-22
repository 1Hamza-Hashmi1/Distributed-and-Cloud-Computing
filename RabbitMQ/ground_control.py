import grpc
from concurrent import futures
import pika
import rover_pb2
import rover_pb2_grpc
import threading
import requests  # Import requests to make API calls

class GroundControlServicer(rover_pb2_grpc.GroundControlServicer):
    def __init__(self):
        # Initialize the server by reading the map and mines
        self.mine_serials = self.read_mines("mines.txt")
        self.grid, self.rows, self.cols = self.read_map("map.txt")

    def read_map(self, file_name):
        """Read the map from a file and return it as a 2D list."""
        with open(file_name, "r") as file:
            lines = file.readlines()
            rows, cols = map(int, lines[0].strip().split())  # Read the first line for dimensions
            grid = [list(map(int, line.strip().split())) for line in lines[1:]]  # Read the grid
        return grid, rows, cols

    def read_mines(self, file_name):
        """Read the mine serial numbers from a file and return them as a list."""
        with open(file_name, "r") as file:
            return [line.strip() for line in file.readlines()]

    def GetMap(self, request, context):
        """Handle the GetMap RPC call."""
        print(f"Rover {request.rover_id} is requesting the map.")
        map_response = rover_pb2.MapResponse()
        map_response.map.extend([" ".join(map(str, row)) for row in self.grid])  # Convert the grid to strings
        print(f"Map information sent to Rover {request.rover_id}.")
        return map_response

    def GetCommands(self, request, context):
        """Handle the GetCommands RPC call."""
        print(f"Rover {request.rover_id} is requesting commands.")
        commands = self.fetch_rover_commands(request.rover_id)
        if commands:
            for command in commands:
                print(f"Sending command '{command}' to Rover {request.rover_id}.")
                yield rover_pb2.CommandResponse(command=command)
        else:
            print(f"Failed to retrieve commands for Rover {request.rover_id}.")

    def GetMineSerialNumber(self, request, context):
        """Handle the GetMineSerialNumber RPC call."""
        print(f"Rover {request.rover_id} is requesting a mine serial number.")
        if self.mine_serials:
            serial_number = self.mine_serials.pop(0)  # Get the next mine serial number
            print(f"Mine serial number '{serial_number}' sent to Rover {request.rover_id}.")
            return rover_pb2.MineSerialResponse(serial_number=serial_number)
        print(f"No mine serial numbers left for Rover {request.rover_id}.")
        return rover_pb2.MineSerialResponse(serial_number="")

    def fetch_rover_commands(self, rover_id):
        """Fetch rover commands from the public API."""
        url = f"https://coe892.reev.dev/lab1/rover/{rover_id}"  # API endpoint
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):  # Ensure valid response
                    commands = result["data"]["moves"]
                    print(f"Fetched commands for Rover {rover_id}: {commands}")
                    return list(commands)  # Return commands as a list
            print(f"Error fetching commands for Rover {rover_id}: {response.text}")
        except Exception as e:
            print(f"Exception fetching commands for Rover {rover_id}: {e}")
        return []

def subscribe_to_defused_mines():
    """Subscribe to the Defused-Mines RabbitMQ channel and log defused mine PINs."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Defused-Mines')

    def callback(ch, method, properties, body):
        print(f"Defused mine PIN: {body.decode()}")

    channel.basic_consume(queue='Defused-Mines', on_message_callback=callback, auto_ack=True)
    print("Ground Control is listening for defused mines...")
    channel.start_consuming()

def serve():
    """Start the gRPC server and RabbitMQ subscriber."""
    # Start the RabbitMQ subscriber in a separate thread
    rabbitmq_thread = threading.Thread(target=subscribe_to_defused_mines)
    rabbitmq_thread.daemon = True
    rabbitmq_thread.start()

    # Start the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rover_pb2_grpc.add_GroundControlServicer_to_server(GroundControlServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Ground Control Server started. Listening on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
