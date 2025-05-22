import requests
import time
import threading

# Read the map
def read_map(filename):
    with open(filename, 'r') as file:
        rows, cols = map(int, file.readline().split())
        map_data = [list(map(int, line.split())) for line in file]
    return rows, cols, map_data

# Get rover commands from the API
def get_rover_commands(rover_id):
    url = f"https://coe892.reev.dev/lab1/rover/{rover_id}"
    response = requests.get(url)
    return response.text.strip()

# Calculate the path of the rover
def calculate_path(commands, map_data):
    x, y = 0, 0
    direction = 'S'  # Initial direction is South
    path = [[cell for cell in row] for row in map_data]  # Copy the map data
    path[x][y] = '*'  # Starting position

    i = 0
    while i < len(commands):
        cmd = commands[i]

        if cmd == 'L':
            if direction == 'S':
                direction = 'E'
            elif direction == 'E':
                direction = 'N'
            elif direction == 'N':
                direction = 'W'
            elif direction == 'W':
                direction = 'S'
        elif cmd == 'R':
            if direction == 'S':
                direction = 'W'
            elif direction == 'W':
                direction = 'N'
            elif direction == 'N':
                direction = 'E'
            elif direction == 'E':
                direction = 'S'
        elif cmd == 'M':
            # Calculate the next position
            next_x, next_y = x, y
            if direction == 'S' and x < len(map_data) - 1:
                next_x += 1
            elif direction == 'N' and x > 0:
                next_x -= 1
            elif direction == 'E' and y < len(map_data[0]) - 1:
                next_y += 1
            elif direction == 'W' and y > 0:
                next_y -= 1

            # Check if the next position is a mine
            if map_data[next_x][next_y] == 1:
                # Check if the next command is a dig (D)
                if i + 1 < len(commands) and commands[i + 1] == 'D':
                    # Dig the mine and move
                    map_data[next_x][next_y] = 0  # Dig the mine
                    i += 1  # Skip the next command (D)
                else:
                    # Rover explodes
                    path[next_x][next_y] = 'X'
                    break  # Stop processing further commands

            # Move to the next position
            x, y = next_x, next_y
            path[x][y] = '*'  # Mark the path

        elif cmd == 'D':
            # Dig command is handled in the 'M' case
            pass

        i += 1

    return path

# Write the path to a file (thread-safe)
def write_path_to_file(path, rover_id, lock):
    with lock:
        with open(f"path_{rover_id}.txt", 'w') as file:
            for row in path:
                file.write(' '.join([str(cell) for cell in row]) + '\n')

# Thread function to process a rover
def process_rover(rover_id, map_data, lock):
    commands = get_rover_commands(rover_id)
    print(f"Processing Rover {rover_id} with commands: {commands}")
    path = calculate_path(commands, [row[:] for row in map_data])
    write_path_to_file(path, rover_id, lock)

# Parallel processing using threading
def parallel_processing():
    rows, cols, map_data = read_map('map.txt')
    lock = threading.Lock()  # Lock for thread-safe file writing
    threads = []

    start_time = time.time()
    for rover_id in range(1, 11):
        thread = threading.Thread(target=process_rover, args=(rover_id, map_data, lock))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Parallel processing time: {end_time - start_time} seconds")

parallel_processing()