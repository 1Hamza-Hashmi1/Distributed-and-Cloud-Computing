from hashlib import sha256
import random
from map import mine_check

def disarm_mine(serialNum: str) -> int:    
    pin = 0
    while True:
        temp_mine_key = str(pin) + serialNum
        hashed_data = sha256(temp_mine_key.encode()).hexdigest()
        if hashed_data[0:6] == '000000':
            return pin

        pin += 1


def get_mines_location(row, col):
    location_list = []
    for i in range(row):
        for j in range(col):
            if mine_check(i + 1, j * 2):
                location_list.append((i + 1, j * 2))
    return location_list


def generate_mines_txt(row, col):
    mine_info_list = []
    mine_list = get_mines_location(row, col)
    f = open("mines.txt", "w")
    serial_num_list = random.sample(range(1000, 10000), len(mine_list))

    for row, col in mine_list:
        serial_num = serial_num_list.pop()
        f.write(f'{row - 1} {int(col/2)} {serial_num}\n')
        mine_info_list.append(f'{row - 1} {int(col/2)} {serial_num}')

    f.close()

    return mine_info_list