import random

def generate_map_grid(row=None, col=None, noChange=True) -> list[list[int]]:    
    if noChange:
        try:
            f = open('map.txt', 'r')
            if ((f == None) or (len(f.readline()) == 0)):
                raise Exception
            else:
                return fetch_map_info()
            
        
        except:              
    
            if row == None:
                row = random.randint(3, 10)
            if col == None:
                col = random.randint(3, 10)


            grid = []
            
            for i in range(row):
                curr_row = []
                for _ in range(col):            
                    if random.randint(1, 10) < 3:
                        curr_row.append(1)
                    else:
                        curr_row.append(0)
                grid.append(curr_row)
            
            
            generate_text_map(grid)
    
    else:
        if row == None:
                row = random.randint(3, 10)
        if col == None:
            col = random.randint(3, 10)


        grid = []
        
        for i in range(row):
            curr_row = []
            for _ in range(col):            
                if random.randint(1, 10) < 3:
                    curr_row.append(1)
                else:
                    curr_row.append(0)
            grid.append(curr_row)
        
        
        generate_text_map(grid)
    return fetch_map_info()

def generate_text_map(grid: list[list[int]]):
    
    with open(f'map.txt', 'w') as f:
        f.write(f'{len(grid)} {len(grid[0])}\n')
        i = 0
        j = 0
        for row in grid:
            i += 1
            for col in row:
                f.write(str (col))
                j += 1
                if (j < len(row)):
                    f.write(' ')
            if (i == len(grid)):
                break
            f.write('\n')
            j = 0

    for i in range(1, 11):
        with open(f'map_{i}.txt', 'w') as f:
            f.write(f'{len(grid)} {len(grid[0])}\n')
            i = 0
            j = 0
            for row in grid:
                i += 1
                for col in row:
                    f.write(str (col))
                    j += 1
                    if (j < len(row)):
                        f.write(' ')
                if (i == len(grid)):
                    break
                f.write('\n')
                j = 0
 

def update_rover_path(rover_id: int, row: int, col: int) -> None:
    """
    Updates the rover path given the row and col    
    :param rover_id: Rover id
    :param row: Row to update
    :param col: Col to update
    :return:
    """
    rover_path = open(f'rover_{rover_id}.txt', 'rb+')
    for i in range(row):  # Align file pointer to correct row
        next(rover_path)

    rover_path.seek(col, 1)  # Align file pointer to correct col
    rover_path.write(bytes('*', 'utf-8'))  # Marking rover path
    rover_path.close()


def mine_check(row, col, rover_id=None, disable=False):
    """
    Checks if mine exists map for the given row, col
    :param disable:
    :param rover_id:
    :param row: Row in the map
    :param col: Col in the map
    :return:
    """

    if rover_id is None:
        rover_map = open(f'map.txt', 'rb+')
    else:
        rover_map = open(f'map_{rover_id}.txt', 'rb+')

    for i in range(row):
        next(rover_map)

    rover_map.seek(col, 1)

    if rover_map.read(1).decode('utf-8') == '1':  # Checking for mine
        if disable:
            rover_map.seek(-1, 1)  # Move the pointer 1 back to reset
            rover_map.write(bytes('X', 'utf-8'))  # Mark mine as X (for now)
        rover_map.close()
        return True

    rover_map.close()
    return False


def create_rover_path(rover_id, rows, cols):
    """
    Initializes the map for each rover
    :param rover_id:  id
    :param rows: Total number of rows
    :param cols: Total number of cols
    :return:
    """
    with open(f'rover_{rover_id}.txt', 'w') as f:
        f.write('\n')
        for i in range(rows):
            for j in range(cols):
                f.write('0')
                if j < (cols - 1):
                    f.write(' ')
            if i < (rows - 1):  # This removes extra line in the map
                f.write('\n')

def fetch_map_info() -> list[list[int]]:
    
    with open('map.txt', 'r') as f:
        x = f.readline()
        grid = []
        row = []
        while(len(x) != 0):
            if (x == '\n'):
                grid.append(row)
                row = []
            elif (x == '0'):  
                row.append(0)            
            elif (x == '1'):
                row.append(1)
            x = f.read(1)
        grid.append(row)
    return grid