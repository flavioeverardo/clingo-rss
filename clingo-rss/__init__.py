import sys
from clingo.application import Application, clingo_main
import clingo as _clingo
from textwrap import dedent
from .utilities import util
from .utilities.gridPropagator import GridPropagator
import random
from clingo import Number, Function

approaches = ["plain", "grid-propagator", "inc-edges", "inc-squares", "inc-single-edge"]

def translate(mode, ctl, size, edges, answers, num_answer_sets, display):
    if mode == "grid-propagator":
        print("Grid Propagator registered!")
        ctl.register_propagator(GridPropagator(size, edges, answers, num_answer_sets, display))
        
    #if mode == "grid-check":
    #    print("Grid Check Propagator registered!")
    #    ctl.register_propagator(CheckPropagator(size, edges, answers, num_answer_sets, k))

    #elif mode == "grid-propagator":
    #    print("Grid Propagator registered!")
    #    ctl.register_propagator(GridPropagator(size, edges, answers, num_answer_sets, k, display))

class ClingoApp(Application):
    def __init__(self, name, version):
        self.program_name  = name
        self.version       = version
        self.__approach    = "plain"
#        self.__type = "representative"
        self.__grid_size   = 4
        self.__benchmark   = _clingo.Flag(False)
        self.__display     = _clingo.Flag(False)
        self.__diagonals   = _clingo.Flag(False)
        self.__colors_test = _clingo.Flag(False)
        
    def __parse_approach(self, value):
        """
        Parse approach argument.
        """
        self.__approach = str(value)
        return self.__approach in approaches

#    def __parse_type(self, value):
#        """
#        Parse type argument.
#        """
#        self.__type = str(value)
#        return self.__type in solving_types

    def __parse_grid_size(self, value):
        """
        Parse the grid-size value to generate a square map
        """
        self.__grid_size = int(value)
        return self.__grid_size >=2

        
    def register_options(self, options):
        """
        Extension point to add options to clingo-sp like choosing the
        transformation to apply.

        """
        group = "Clingo-rss Options"
        
        options.add(group, "approach", dedent("""\
        Approach to compute and represent search space [simple-opt]
              <arg>: {simple-opt|propagator-opt|another-one}
                plain             : complete asp encodings approach
                stratified        : stratified sampling using (unary) parity constraints
        """),
        self.__parse_approach)

#        options.add(group, "type", dedent("""\
#        Type of problem to solve [representative]
#              <arg>: {representative}
#                representative    : emblematic answer set in cluster towards sparse search space
#        """),
#        self.__parse_type)

        options.add(group, "grid-size", dedent("""\
        Integer value to build a square map. Default=4"""), self.__parse_grid_size)
        
        options.add_flag(group, "benchmark", dedent("""\
        Disable printing for benchmark purposes"""), self.__benchmark)

        options.add_flag(group, "display-sp", dedent("""\
        Display specific information from clingo-sp"""), self.__display)

        options.add_flag(group, "diagonals", dedent("""\
        Enable diagonal edges to verify distances"""), self.__diagonals)

        options.add_flag(group, "colors-test", dedent("""\
        Runs colors test for a visual solution space representation"""), self.__colors_test)


    def main(self, ctl, files):
        """
        1) Read the given program or run the colors test
        2) Get all the symbols from a clingo object
        3) Build the XORs to generate the desired number of clusters
        4) For loop... for each XORs configuration
          5) Create a new clingo object
          6) Add the encodings and the XORs
          7) Ground, Solve and store answer set
        8) If all SAT, proceed... else restart
        opt... we could check the satisfiability of the XORs
        """
        
        ## clingo object for the input encoding/instance
        control = _clingo.Control()

        display = self.__display

        ## 1) Read the given program or run the colors test
        ## Color test
        if self.__colors_test:
            print("Running colors test")
            
            ## 3) Build the XORs to generate the n^n clusters
            grid_size = self.__grid_size
            num_clusters = grid_size * grid_size
            print("Number of clusters:", num_clusters)

            ## Build 2^n combinatios for XOR constraints and
            ## check the number of xors and the number of clusters
            num_xors = grid_size * grid_size
            print("Grid of", grid_size, "x", grid_size, "=", num_clusters, "clusters and we need", num_xors, "xors which returns", 2**num_xors, "solutions")

            ## Calculate the colors
            answer_sets, colors = util.build_colors_test_instance(num_xors)                    

        else:
            for f in files:
                control.load(f)
            if not files:
                control.load("-")

            ## Ground
            print("Grounding...")
            control.ground([("base", [])])

            print("Solving...")
            answer_sets = []
            with control.solve(yield_=True) as hnd:
                for m in hnd:
                    if self.__display and not self.__benchmark:
                        print("Answer: %s"%m.number)
                        print(m)
                    atoms_list = m.symbols(shown=True)
                    answer_sets.append(atoms_list)

                if (str(hnd.get()) == "SAT"):
                    print("SATISFIABLE")
                elif (str(hnd.get()) == "UNSAT"):
                    print("UNSATISFIABLE")
                else:
                    print("UNKNOWN")

        print("")
        ## Calculate edges and build the instance
        size = self.__grid_size
        add_diagonals = self.__diagonals


        ## The standard (encoding-based) approach ---------------------------------------------------------------------------
        if self.__approach == "plain":
            """
            A complete encoding-based approach (eager style)
            calculating the grid and the distances beforehand,
            ground everything and let clingo optimize solutions
            """
            ## If colors test or users instance
            if self.__colors_test:
                add_distances = True
                add_nodes = True
                add_edges = True
                answers = colors
            else:
                answers = answer_sets

            ## Build instance
            instance, edges = util.build_instance(answers, 1, size, add_diagonals, add_distances, add_nodes, add_edges)

            ## Display the instance for optimization
            if self.__display and not self.__benchmark:
                print(instance)
            
            ## Use the original clingo control object ctl
            ctl.add("base", [], instance)

            ## Load encoding
            ctl.load("clingo-rss/lp/representative.lp")

            print("Grounding...")
            ctl.ground([("base", [])])

            ## Solve
            with ctl.solve(yield_=True) as hnd:
                for m in hnd:
                    if self.__colors_test:
                        util.build_colors_solution(answer_sets, m, m.number, m.cost, size, self.__approach)
                    ## Non color benchmark

        ## Grid propagator mode ---------------------------------------------------------------------------------------------
        elif self.__approach == "grid-propagator":
            """
            A basic lazy type propagator.
            Distances are not calcultated beforehand but when the solving requires them.
            The propagator performs minimization with the help of python
            """
            ## If colors test or users instance
            if self.__colors_test:
                add_distances = True ## Should be False
                add_nodes = True
                add_edges = True
                answers = colors
            else:
                answers = answer_sets

            ## Build instance
            instance, edges = util.build_instance(answers, 1, size, add_diagonals, add_distances, add_nodes, add_edges)
            
            ## Use the original clingo control object ctl
            ctl.add("base", [], instance)

            ## Load encoding
            ctl.load("clingo-rss/lp/representative.lp")

            print("Grounding...")
            ctl.ground([("base", [])])

            ## Register the proper options
            if self.__colors_test:
                translate(self.__approach, ctl, size, edges, colors, len(colors), self.__display)
            else:
                translate(self.__approach, ctl, size, edges, answer_sets, len(answer_sets), self.__display)
            ## Solve
            with ctl.solve(yield_=True) as hnd:
                for m in hnd:
                    if self.__colors_test:
                        util.build_colors_solution(answer_sets, m, m.number, m.cost, size, self.__approach)

        ## Incremental edges mode -------------------------------------------------------------------------------------------
        elif self.__approach == "inc-edges":
            """
            The incremental edge approach adds information per iteration
            Distances are calculated beforehand and only new edges are given at each step
            """
            
            ## If colors test or users instance
            if self.__colors_test:
                add_distances = True ## Should this be False?
                add_nodes = True
                add_edges = False
                answers = colors
            else:
                answers = answer_sets

            ## Build instance
            instance, edges = util.build_instance(answers, 1, size, add_diagonals, add_distances, add_nodes, add_edges)

            ctl.add("base", [], instance)

            ## Load encoding
            ctl.load("clingo-rss/lp/inc-representative.lp")
                        
            ## Normalized edges
            # Add 1 to each value
            edges = [[a + 1, b + 1] for a, b in edges]

            N = size
            print(instance)
            print()
            print(edges)
            print("incremental edges mode")
            print("For N:", N)

            # Create a dictionary to store connections
            connections  = {}

            # Populate the dictionary
            for edge in edges:
                a, b = edge
                if a not in connections:
                    connections[a] = []
                if b not in connections:
                    connections[b] = []
                connections[a].append(b)
                connections[b].append(a)  # Since the edges are undirected

            # Display the connections
            for node, neighbors in connections.items():
                print(f"Node {node} is connected to: {neighbors}")

            total_nodes = N*N
            ## Add edges
            # Initialize the traversal
            start_node = 1
            visited = set()
            to_process = [start_node]

            iteration = 1

            print("Grounding...")
            ctl.ground([("base", [])])

            brave = []

            parts = []
            nodes = set()
            
            while to_process:
                print(f"Processing nodes: {to_process}")

                # Nodes to process in this iteration
                next_nodes = []

                for node in to_process:
                    if node not in visited:
                        # Mark the node as visited
                        visited.add(node)

                        # Get connections of the current node
                        neighbors = connections.get(node, [])
                        for neighbor in neighbors:
                            if neighbor not in visited:
                                x = node
                                y = neighbor
                                parts.append(("edges", [Number(x), Number(y)]))
                                nodes.add(x)
                                nodes.add(y)
                                ctl.cleanup()
                            
                        # Add unvisited neighbors to the next round of processing
                        next_nodes.extend([n for n in neighbors if n not in visited])

                #print("Ground parts")
                #print(parts)
                ctl.ground(parts)

                # Update the nodes to process in the next iteration
                to_process = next_nodes

                print("-------------------------------------------------------------------------------------")
                
                iteration +=1

                ctl.enable_cleanup = True
                ## Solve
                optimal = []
                with ctl.solve(yield_=True) as hnd:
                    for m in hnd:
                        if self.__colors_test:
                            iter_model = "%s_%s"%(iteration, m.number)
                            util.build_colors_solution(answer_sets, m, iter_model, m.cost, size, self.__approach)
                            optimal = m.symbols(shown=True)
                    #print(nodes)
                    #print(total_nodes)
                    #print(iteration, N)
                    if len(nodes) < total_nodes:
                        for atom in optimal:                        
                            if atom.name == "cluster":
                                if int(str(atom.arguments[0])) in nodes:
                                    #print(atom)
                                    x = Number(int(str(atom.arguments[0])))
                                    y = Number(int(str(atom.arguments[1])))
                                    t = ("brave", [x, y])
                                    #print(t)
                                    if t not in brave:
                                        brave.append(t)
                                #else:
                                #    print("Nothing more to add")    
                        #print("brave set", brave)
                        ctl.ground(brave)
                        ## Non color benchmark

                            
        ## Incremental squares mode -------------------------------------------------------------------------------------------
        elif self.__approach == "inc-squares":
            """
            The incremental squares approach adds information per iteration
            Distances are calculated beforehand and only sub-squares are solved at each step
            """

            ## If colors test or users instance
            if self.__colors_test:
                add_distances = True ## Should this be False?
                add_nodes = True
                add_edges = False
                answers = colors
            else:
                answers = answer_sets

            ## Build instance
            instance, edges = util.build_instance(answers, 1, size, add_diagonals, add_distances, add_nodes, add_edges)

            ctl.add("base", [], instance)

            ## Load encoding
            ctl.load("clingo-rss/lp/inc-representative.lp")
             
            ## Normalized edges
            # Add 1 to each value
            edges = [[a + 1, b + 1] for a, b in edges]

            N = size
            #print(instance)
            #print()
            #print(edges)
            print("incremental squares mode")
            print("For N:", N)
            sub_squares_dict = {}
            for sub_square_N in range(2, N):
                sub_square = util.extract_square_edges(edges, 1, sub_square_N, N)
                sub_squares_dict[sub_square_N] = sub_square
            sub_squares_dict[N] = edges
            util.print_squares(sub_squares_dict)

            iteration = 1

            print("Grounding...")
            ctl.ground([("base", [])])

            brave = []

            parts = []
            nodes = set()
            for key, values in sub_squares_dict.items():
                print(key, values)
                for edge in values:
                    x = edge[0]
                    y = edge[1]
                    parts.append(("edges", [Number(x), Number(y)]))
                    nodes.add(x)
                    nodes.add(y)
                    ctl.cleanup()

                #print("Ground parts")
                #print(parts)
                ctl.ground(parts)

                print("-------------------------------------------------------------------------------------")
                
                iteration +=1

                ctl.enable_cleanup = True
                ## Solve
                optimal = []
                with ctl.solve(yield_=True) as hnd:
                    for m in hnd:
                        if self.__colors_test:
                            iter_model = "%s_%s"%(iteration, m.number)
                            util.build_colors_solution(answer_sets, m, iter_model, m.cost, size, self.__approach)
                            optimal = m.symbols(shown=True)
                    #print(nodes)
                    #print(iteration, key, N)
                    if iteration < N:
                        for atom in optimal:                        
                            if atom.name == "cluster":
                                if int(str(atom.arguments[0])) in nodes:
                                    #print(atom)
                                    x = Number(int(str(atom.arguments[0])))
                                    y = Number(int(str(atom.arguments[1])))
                                    t = ("brave", [x, y])
                                    #print(t)
                                    if t not in brave:
                                        brave.append(t)
                                #else:
                                #    print("Nothing more to add")    
                        #print("brave set", brave)
                        ctl.ground(brave)
                        ## Non color benchmark
            
        ## Incremental single edge mode -------------------------------------------------------------------------------------------
        elif self.__approach == "inc-single-edge":
            """
            The incremental single-edge approach adds informationa single edge per iteration
            Distances are calculated beforehand and only one cluster is solved at each step
            """

            ## If colors test or users instance
            if self.__colors_test:
                add_distances = True ## Should this be False?
                add_nodes = True
                add_edges = False
                answers = colors
            else:
                answers = answer_sets

            ## Build instance
            instance, edges = util.build_instance(answers, 1, size, add_diagonals, add_distances, add_nodes, add_edges)

            ctl.add("base", [], instance)

            ## Load encoding
            ctl.load("clingo-rss/lp/inc-representative.lp")
             
            ## Normalized edges
            # Add 1 to each value
            edges = sorted([[a + 1, b + 1] for a, b in edges])

            N = size
            #print(edges)
            print("incremental single-edge mode")
            print("For N:", N)

            iteration = 1

            print("Grounding...")
            ctl.ground([("base", [])])

            brave = []

            parts = []
            nodes = set()
            for edge in edges:
                print("Processing edge:", edge)
                x = edge[0]
                y = edge[1]
                parts.append(("edges", [Number(x), Number(y)]))
                nodes.add(x)
                nodes.add(y)
                ctl.cleanup()

                ctl.ground(parts)

                print("-------------------------------------------------------------------------------------")
                
                iteration +=1

                ctl.enable_cleanup = True
                ## Solve
                optimal = []
                with ctl.solve(yield_=True) as hnd:
                    for m in hnd:
                        if self.__colors_test:
                            iter_model = "%s_%s"%(iteration, m.number)
                            util.build_colors_solution(answer_sets, m, iter_model, m.cost, size, self.__approach)
                            optimal = m.symbols(shown=True)
                    #print(nodes)
                    #print(iteration, key, N)
                    if iteration < len(edges):
                        for atom in optimal:                        
                            if atom.name == "cluster":
                                if int(str(atom.arguments[0])) in nodes:
                                    #print(atom)
                                    x = Number(int(str(atom.arguments[0])))
                                    y = Number(int(str(atom.arguments[1])))
                                    t = ("brave", [x, y])
                                    #print(t)
                                    if t not in brave:
                                        brave.append(t)
                                #else:
                                #    print("Nothing more to add")    
                        #print("brave set", brave)
                        ctl.ground(brave)
                        ## Non color benchmark

        
        

## Entry point
sys.exit(int(clingo_main(ClingoApp("clingo-rss", "0.1.0"), sys.argv[1:])))
