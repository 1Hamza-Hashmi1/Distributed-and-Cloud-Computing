import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Tuple

# Configuration
BASE_DIR = Path(__file__).parent.absolute()
STATIC_DIR = BASE_DIR / "static"
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Data storage
map_data: List[List[int]] = []
mines: List[Dict] = []
rovers: Dict[int, Dict] = {}
next_rover_id: int = 1


# Helper functions
def read_map(file_name: str) -> None:
    """Initialize map from file"""
    global map_data
    with open(file_name, "r") as f:
        lines = f.readlines()
        rows, cols = map(int, lines[0].strip().split())
        map_data = [list(map(int, line.strip().split())) for line in lines[1:rows + 1]]


def read_mines(file_name: str) -> None:
    """Initialize mines from file"""
    global mines
    with open(file_name, "r") as f:
        serials = [line.strip() for line in f.readlines()]
        for row in range(len(map_data)):
            for col in range(len(map_data[0])):
                if map_data[row][col] == 1 and serials:
                    mines.append({
                        "id": len(mines) + 1,
                        "serial_number": serials.pop(0),
                        "x": row,
                        "y": col
                    })


# Load initial data
read_map("map.txt")
read_mines("mines.txt")


# Pydantic Models
class MapUpdate(BaseModel):
    rows: int
    cols: int


class MineCreate(BaseModel):
    serial_number: str
    x: int
    y: int


class MineUpdate(BaseModel):
    serial_number: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None


class RoverCreate(BaseModel):
    commands: str


class RoverUpdate(BaseModel):
    commands: str


# Map Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/map")
async def get_map():
    return {
        "rows": len(map_data),
        "cols": len(map_data[0]),
        "map": map_data,
        "mine_locations": [(m["x"], m["y"]) for m in mines]
    }


@app.put("/map")
async def update_map(data: MapUpdate):
    global map_data
    map_data = [[0 for _ in range(data.cols)] for _ in range(data.rows)]
    mines.clear()
    return {"message": f"Map reset to {data.rows}x{data.cols}"}


# Mine Endpoints
@app.get("/mines")
async def list_mines():
    return mines


@app.get("/mines/{mine_id}")
async def get_mine(mine_id: int):
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")
    return mine


@app.post("/mines", status_code=201)
async def create_mine(data: MineCreate):
    if not (0 <= data.x < len(map_data) and 0 <= data.y < len(map_data[0])):
        raise HTTPException(status_code=400, detail="Coordinates out of bounds")

    new_mine = {
        "id": len(mines) + 1,
        "serial_number": data.serial_number,
        "x": data.x,
        "y": data.y
    }
    mines.append(new_mine)
    map_data[data.x][data.y] = 1
    return new_mine


@app.put("/mines/{mine_id}")
async def update_mine(mine_id: int, data: MineUpdate):
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")

    if data.serial_number:
        mine["serial_number"] = data.serial_number

    if data.x is not None and data.y is not None:
        if not (0 <= data.x < len(map_data) and 0 <= data.y < len(map_data[0])):
            raise HTTPException(status_code=400, detail="New coordinates out of bounds")
        map_data[mine["x"]][mine["y"]] = 0
        mine["x"], mine["y"] = data.x, data.y
        map_data[data.x][data.y] = 1

    return mine


@app.delete("/mines/{mine_id}")
async def delete_mine(mine_id: int):
    global mines
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")

    map_data[mine["x"]][mine["y"]] = 0
    mines = [m for m in mines if m["id"] != mine_id]
    return {"message": f"Mine {mine_id} deleted"}


# Rover Endpoints
@app.get("/rovers")
async def list_rovers():
    return [
        {
            "id": r["id"],
            "status": r["status"],
            "position": (r["x"], r["y"]),
            "commands": r["commands"]
        }
        for r in rovers.values()
    ]


@app.get("/rovers/{rover_id}")
async def get_rover(rover_id: int):
    if rover_id not in rovers:
        raise HTTPException(status_code=404, detail="Rover not found")
    return rovers[rover_id]


@app.post("/rovers", status_code=201)
async def create_rover(data: RoverCreate):
    global next_rover_id
    rover = {
        "id": next_rover_id,
        "commands": data.commands,
        "status": "Not Started",
        "x": 0,
        "y": 0,
        "direction": "N",
        "path": [(0, 0)]
    }
    rovers[next_rover_id] = rover
    next_rover_id += 1
    return rover


@app.put("/rovers/{rover_id}")
async def update_rover(rover_id: int, data: RoverUpdate):
    if rover_id not in rovers:
        raise HTTPException(status_code=404, detail="Rover not found")
    if rovers[rover_id]["status"] not in ["Not Started", "Finished"]:
        raise HTTPException(status_code=400, detail="Cannot update commands while rover is active")

    rovers[rover_id]["commands"] = data.commands
    return {"message": f"Rover {rover_id} commands updated"}


@app.post("/rovers/{rover_id}/dispatch")
async def dispatch_rover(rover_id: int):
    if rover_id not in rovers:
        raise HTTPException(status_code=404, detail="Rover not found")

    rover = rovers[rover_id]
    if rover["status"] != "Not Started":
        raise HTTPException(status_code=400, detail="Rover already active")

    rover["status"] = "Moving"
    x, y = 0, 0
    direction = "N"
    path = [(x, y)]
    eliminated_at = None

    direction_vectors = {
        "N": (-1, 0),
        "E": (0, 1),
        "S": (1, 0),
        "W": (0, -1)
    }

    for cmd in rover["commands"]:
        if cmd in ["L", "R"]:
            directions = ["N", "E", "S", "W"]
            current_idx = directions.index(direction)
            direction = directions[(current_idx + (1 if cmd == "R" else -1)) % 4]
        elif cmd == "M":
            dx, dy = direction_vectors[direction]
            new_x, new_y = x + dx, y + dy

            # Boundary check
            if not (0 <= new_x < len(map_data) and 0 <= new_y < len(map_data[0])):
                eliminated_at = (x, y)  # Eliminated at last valid position
                break

            x, y = new_x, new_y
            path.append((x, y))

            # Mine check
            if map_data[x][y] == 1:
                eliminated_at = (x, y)
                break

    rover.update({
        "x": x,
        "y": y,
        "direction": direction,
        "path": path,
        "status": "Eliminated" if eliminated_at else "Finished",
        "eliminated_at": eliminated_at
    })

    return {
        "status": rover["status"],
        "final_position": (x, y),
        "path": path,
        "eliminated_at": eliminated_at,
        "hit_mine": eliminated_at in [(m["x"], m["y"]) for m in mines] if eliminated_at else False
    }


@app.delete("/rovers/{rover_id}")
async def delete_rover(rover_id: int):
    if rover_id not in rovers:
        raise HTTPException(status_code=404, detail="Rover not found")
    del rovers[rover_id]
    return {"message": f"Rover {rover_id} deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)