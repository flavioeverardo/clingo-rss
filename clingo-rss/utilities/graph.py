import typing
import itertools

class Graph(object):
    def __init__(self, shape: typing.Tuple[int,int], diagonals):

        self.nodes = {}
        self.shape = shape
        self.diagonals = diagonals
        self._init_nodes()

    def _init_nodes(self):
        # Iterate through all combinations of coordinates
        neighbors = []
        for x, y in itertools.product(range(self.shape[0]), range(self.shape[1])):
            ## Build the grid with all possible neighbors
            if self.diagonals:
                ## All: [(x-1,y), (x+1,y), (x,y-1), (x,y+1), (x-1,y-1), (x+1,y-1), (x-1,y+1), (x+1,y+1)]
                neighbors = [(x-1,y), (x+1,y), (x,y-1), (x,y+1), (x-1,y-1), (x+1,y-1), (x-1,y+1), (x+1,y+1)]
            else:
                ## Only the square: [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
                neighbors = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
            ## Filter impossible neighbors
            neighbors = [n for n in neighbors if 0 <= n[0] <= self.shape[0]-1 and 0 <= n[1] <= self.shape[1]-1]
            self.nodes[(x,y)] = neighbors
            
        
