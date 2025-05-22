import grpc
import proto_file_pb2
import proto_file_pb2_grpc
from concurrent import futures
import logging
from lab1_main import get_rover_commands
from map import generate_map_grid, generate_text_map
from mines import generate_mines_txt

class MyGreeter(proto_file_pb2_grpc.MyGreeterServicer):
    
    def GetMap(self, request, context):      
        grid = generate_map_grid() 
        generate_text_map(grid)
        map_info = proto_file_pb2.MapInfo()
        
        row_size = len(grid)
        col_size = len(grid[0])               
        
        map_info.row = row_size
        map_info.col = col_size
        
        self.mine_info_list = generate_mines_txt(row_size, col_size)              
        
        
        for row in grid:
            map_info_row = map_info.map_row.add()
            map_info_row.mine_val.extend(row)
                   
        return map_info
    
    def GetCommands(self, request, context):
        return proto_file_pb2.Commands(commands=get_rover_commands(request.id))    
    
    def GetMineSerialNum(self, request, context):
        for mine_info in self.mine_info_list:
            info = mine_info.split(' ')
            
            if ((int(info[0]) == request.row) and (int(info[1]) == request.col)):
                return proto_file_pb2.SerialNum(serialNum=info[2])


    def NotifyServer(self, request, context):
        print(request._message)
        return proto_file_pb2.Empty()

    def MinePin(self, request, context):
        print(f'Mine defused at row: {request.row }, col: {request.col}')
        print(f'Pin Recieved: {request.pin_num}')
        print(f'RoverId: {request.rover_id}')
        return proto_file_pb2.Empty()
    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    proto_file_pb2_grpc.add_MyGreeterServicer_to_server(MyGreeter(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
    
if __name__ == '__main__':
    logging.basicConfig()
    serve()