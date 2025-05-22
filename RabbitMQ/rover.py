import grpc
import pika
import rover_pb2
import rover_pb2_grpc
import sys

def publish_mine_details(mine_id, serial_number, x, y):
    """Publish mine details to the Demine-Queue RabbitMQ channel."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Demine-Queue')

    message = f"{mine_id},{serial_number},{x},{y}"
    channel.basic_publish(exchange='', routing_key='Demine-Queue', body=message)
    print(f"Rover published mine details: {message}")
    connection.close()

def execute_commands(rover_id, commands, grid, rows, cols, stub):
    """Execute commands for the rover and explore the map."""
    x, y = 0, 0  # Starting position (top-left corner)
    direction = 2  # 0: North, 1: East, 2: South, 3: West
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, W
    mine_id = 1  # Unique ID for each mine

    print(f"Rover {rover_id} starting at position ({x}, {y}).")

    for command in commands:
        print(f"Rover {rover_id} executing command: {command}")
        if command == "L":
            direction = (direction - 1) % 4  # Turn left
            print(f"Rover {rover_id} turned left. New direction: {['North', 'East', 'South', 'West'][direction]}")
        elif command == "R":
            direction = (direction + 1) % 4  # Turn right
            print(f"Rover {rover_id} turned right. New direction: {['North', 'East', 'South', 'West'][direction]}")
        elif command == "M":
            dx, dy = directions[direction]
            new_x, new_y = x + dx, y + dy

            if 0 <= new_x < rows and 0 <= new_y < cols:
                if grid[new_x][new_y] == 1:
                    print(f"Rover {rover_id} encountered a mine at ({new_x}, {new_y})!")
                    # Get the mine serial number from the ground control
                    serial_response = stub.GetMineSerialNumber(rover_pb2.RoverRequest(rover_id=rover_id))
                    if serial_response.serial_number:
                        print(f"Rover {rover_id} retrieved serial number: {serial_response.serial_number}")
                        # Publish mine details to RabbitMQ
                        publish_mine_details(mine_id, serial_response.serial_number, new_x, new_y)
                        mine_id += 1
                    else:
                        print(f"Rover {rover_id} could not retrieve a serial number for the mine.")
                x, y = new_x, new_y
                print(f"Rover {rover_id} moved to ({x}, {y}).")
            else:
                print(f"Rover {rover_id} cannot move out of bounds to ({new_x}, {new_y}).")

def main():
    """Main function for the rover."""
    if len(sys.argv) != 2:
        print("Usage: python rover.py <rover_id>")
        return

    rover_id = int(sys.argv[1])
    print(f"Starting Rover {rover_id}...")

    # Connect to the ground control server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = rover_pb2_grpc.GroundControlStub(channel)

        # Get the map from the ground control
        print(f"Rover {rover_id} requesting the map...")
        map_response = stub.GetMap(rover_pb2.RoverRequest(rover_id=rover_id))
        grid = [list(map(int, row.split())) for row in map_response.map]
        rows, cols = len(grid), len(grid[0])
        print(f"Rover {rover_id} received the map. Grid size: {rows}x{cols}.")

        # Get the commands from the ground control
        print(f"Rover {rover_id} requesting commands...")
        commands = [cmd.command for cmd in stub.GetCommands(rover_pb2.RoverRequest(rover_id=rover_id))]
        print(f"Rover {rover_id} received commands: {''.join(commands)}")

        # Execute the commands
        execute_commands(rover_id, commands, grid, rows, cols, stub)

if __name__ == '__main__':
    main()