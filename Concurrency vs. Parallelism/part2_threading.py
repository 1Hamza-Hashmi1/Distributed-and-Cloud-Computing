import time
import requests
import hashlib
import threading
from copy import deepcopy


def read_map(file_name):
    """Read the map.txt file and return the map as a 2D list."""
    with open(file_name, "r") as file:
        lines = file.readlines()
        rows, cols = map(int, lines[0].strip().split())
        grid = [list(map(int, line.strip().split())) for line in lines[1:]]
    return grid, rows, cols


def read_mines(file_name):
    """Read the mines.txt file and return the serial numbers as a list."""
    with open(file_name, "r") as file:
        return [line.strip() for line in file.readlines()]


def fetch_rover_commands(rover_id):
    """Fetch rover commands from the API."""
    try:
        url = f"https://coe892.reev.dev/lab1/rover/{rover_id}"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                return result["data"]["moves"]
            else:
                print(f"Error fetching commands for Rover {rover_id}: {result}")
                return ""
        else:
            print(f"Failed to fetch commands for Rover {rover_id}, Status Code: {response.status_code}")
            return ""
    except Exception as e:
        print(f"Exception occurred while fetching commands for Rover {rover_id}: {e}")
        return ""


def find_valid_pin(serial_number):
    """Find a valid PIN by brute-forcing with SHA256."""
    pin = 0
    while True:
        # Concatenate PIN and serial number
        key = f"{pin}{serial_number}"
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        if hashed_key.startswith("000000"):  # Check for 6 leading zeros
            return pin
        pin += 1


def execute_commands(rover_id, commands, grid, rows, cols, mine_serials, serials_lock):
    """Execute commands for the rover and update its path on the map."""
    # Initial position and direction
    x, y = 0, 0  # Top-left corner
    direction = 2  # 0: North, 1: East, 2: South, 3: West
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, W
    path_grid = [["0" for _ in range(cols)] for _ in range(rows)]
    path_grid[x][y] = "*"  # Mark the starting position

    for command in commands:
        if command == "L":
            direction = (direction - 1) % 4  # Turn left
        elif command == "R":
            direction = (direction + 1) % 4  # Turn right
        elif command == "M":
            # Calculate the next position
            dx, dy = directions[direction]
            new_x, new_y = x + dx, y + dy

            # Debugging: Print movement
            print(f"Rover {rover_id} trying to move from ({x}, {y}) to ({new_x}, {new_y}).")

            # Check if the new position is within bounds
            if 0 <= new_x < rows and 0 <= new_y < cols:
                # Check for a mine
                if grid[new_x][new_y] == 1:
                    print(f"Rover {rover_id} encountered a mine at ({new_x}, {new_y})!")
                    with serials_lock:
                        if mine_serials:
                            serial_number = mine_serials.pop(0)  # Safely get the next serial number
                        else:
                            print(f"Rover {rover_id} cannot disarm the mine at ({new_x}, {new_y}) due to missing serial numbers.")
                            break

                    pin = find_valid_pin(serial_number)
                    print(f"Rover {rover_id} disarmed the mine at ({new_x}, {new_y}) with PIN: {pin}")
                    grid[new_x][new_y] = 0  # Mark the mine as disarmed
                    x, y = new_x, new_y  # Update position after disarming
                    path_grid[x][y] = "*"  # Mark the cell as visited
                else:
                    # Update position
                    x, y = new_x, new_y
                    path_grid[x][y] = "*"  # Mark the cell as visited
            else:
                # Ignore the move if it's out of bounds
                print(f"Rover {rover_id} cannot move out of bounds to ({new_x}, {new_y}).")
                continue
        elif command == "D":
            # Dig at the current position
            if grid[x][y] == 1:
                print(f"Rover {rover_id} dug and disarmed the mine at ({x}, {y})!")
                with serials_lock:
                    if mine_serials:
                        serial_number = mine_serials.pop(0)  # Safely get the next serial number
                    else:
                        print(f"Rover {rover_id} cannot disarm the mine at ({x}, {y}) due to missing serial numbers.")
                        break

                pin = find_valid_pin(serial_number)
                print(f"Rover {rover_id} disarmed the mine with PIN: {pin}")
                grid[x][y] = 0  # Mark the mine as disarmed
            else:
                print(f"Rover {rover_id} attempted to dig at ({x}, {y}), but no mine was present.")

    # Save the path grid to a file
    with open(f"path_{rover_id}.txt", "w") as file:
        for row in path_grid:
            file.write(" ".join(row) + "\n")


def process_rover(rover_id, original_grid, rows, cols, mine_serials, serials_lock):
    """Fetch commands and process a single rover."""
    grid = deepcopy(original_grid)  # Create a deep copy of the grid for the rover
    commands = fetch_rover_commands(rover_id)
    if commands:
        print(f"Processing Rover {rover_id} with commands: {commands}")
        execute_commands(rover_id, commands, grid, rows, cols, mine_serials, serials_lock)
    else:
        print(f"No commands available for Rover {rover_id}")


def main():
    # Read the original map
    original_grid, rows, cols = read_map("map.txt")

    # Read the mine serial numbers
    mine_serials = read_mines("mines.txt")
    serials_lock = threading.Lock()  # Lock for safely accessing serials

    # Start timing
    start_time = time.time()

    # Create and start threads for each rover
    threads = []
    for rover_id in range(1, 11):
        thread = threading.Thread(target=process_rover, args=(rover_id, original_grid, rows, cols, mine_serials, serials_lock))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # End timing
    end_time = time.time()
    print(f"Threaded execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
