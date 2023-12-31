import sys
import dask
import numpy as np
import dask.array as da
from dask.distributed import Client
from dask import delayed

def main():
    try:
        input_name = sys.argv[1]
    except IndexError:
        sys.exit("No output filename")
    try:
        output_name= sys.argv[2]
    except IndexError:
        sys.exit("No output filename")
    try:
        n = int (sys.argv[3])
    except:
        sys.exit(f"Entered value is not a nuber {sys.argv[3]}")
    try:
        chunk_size = int(sys.argv[4])
    except:
        sys.exit(f"Entered value is not a nuber {sys.argv[4]}") 
    
    dask.config.set(scheduler='processes')
    client = Client()   
    board = read_input_file(input_name, chunk_size)
    final_board = prepare_next_board(n, new_board, mask)
    write_output_file(output_name, final_board)
    client.shutdown()
          
def read_input_file(input_file):
    # initialize board
    with open(input_file) as f:
        w, h = [int(x) for x in next(f).split()]
        # use the smallest data type
        board = np.zeros((w, h),dtype=np.uint8)
        for line_count, line in enumerate(f, start=0):
            single_numbers = line.split()
            x, y = map(int, single_numbers[:2])
            board[x][y] = 1
        dask_board = da.from_array(board, chunks=(chunk_size, chunk_size))
    return dask_board
                
def write_output_file(output, board):
    w = board.shape[0]
    h = board.shape[1]
    live_cells = []
    for r in range(w):
        for c in range(h):
            if board[r][c] == 1:
                live_cells.append([r, c])
    f = open(output, "w")
    f.write(str(w)+ " "+ str(h)+"\n")
    for cell in live_cells:
        f.write(str(cell[0])+ " "+ str(cell[1])+ "\n")
    f.close()
    
def process_cell(board_chunk, block_id=None):
    width, height = board_chunk.shape
    #based on the index of chunks
    start_width = block_id[0] * width
    start_height = block_id[1] * height
    board_slice = board[start_width:(start_width + width), start_height:(start_height + height)].compute()

    # Apply the rules of the game.
    board_chunk[np.logical_or(board_chunk < 2, board_chunk > 3)] = 0
    board_chunk[board_chunk == 3] = 1
    # cell with two neighbours stay the same
    board_chunk[board_chunk == 2] = board_slice[board_chunk == 2]
    return board_chunk

def prepare_next_board(steps, board, mask):
    for _ in range(steps):
        # use the convolution
        num_live_neighbors = board.map_overlap(convolve, depth=1, boundary='none', weights=mask, mode='constant', cval=0)
        board = num_live_neighbors.map_blocks(process_cell, dtype=np.uint8)
    return board

                           
if __name__ == "__main__":
    main()
