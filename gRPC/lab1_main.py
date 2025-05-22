import requests
import json

def get_rover_commands(rover_id):
    """
    Function grabs the rover commands from the api
    :param rover_id: The rover id
    :return: Rover commands in JSON
    """
    api = 'https://coe892.reev.dev/lab1/rover'
    r = requests.get(f'{api}/{rover_id}')
    if r.ok:
        content = json.loads(r.content)
        return content['data']['moves']
    else:
        raise Exception("Failed to fetch api")