import clingo

def distance(l1, l2):
    l3 = list(set(l1) & set(l2)) # Intersect
    l4 = list(set(l1)-set(l3))   # Difference
    l5 = list(set(l2)-set(l3))   # Difference
    return len(l4)+len(l5)

class GridPropagator:
    def __init__(self, size, edges, answers, num_answers, display):
        self.__states   = []
        self.__clusters = []
        #self.__grid     = {}
        self.__literals = {}
        #self.__k        = 0
        self.__optimal  = 10**100
        self.__edges    = edges
        self.__answers  = {x+1:answers[x] for x in range(len(answers))}
        self.__display  = display
        self.__k_edges  = {}
        #self.__node_answer = {}
        #self.__node_literal = {}
        
    #def __build_graph_state(self, edges):
    #    for edge in edges:
    #        x, y = 0, 1
    #        #for thread_id in thread_ids:
    #        self.__grid.setdefault(edge[x]+1, []).append(edge[y]+1)
    #        self.__grid.setdefault(edge[y]+1, []).append(edge[x]+1)
        
    def init(self, init):

        ## Thread safe
        for thread_id in range(len(self.__states), init.number_of_threads):
            self.__states.append({})
            #self.__clusters.append({})
        
        #self.__build_graph_state(self.__edges)
        #if self.__display:
        #    print(self.__grid)
            
        for atom in init.symbolic_atoms.by_signature("active_edge",4):
            lit = init.solver_literal(atom.literal)
            x       = int(str(atom.symbol.arguments[0]))
            y       = int(str(atom.symbol.arguments[1]))
            answer1 = int(str(atom.symbol.arguments[2]))
            answer2 = int(str(atom.symbol.arguments[3]))
            self.__literals[lit] = (x, y, answer1, answer2)
            init.add_watch( lit)

        init.check_mode = clingo.PropagatorCheckMode.Total

        for edge in self.__edges:
            x = edge[0]
            y = edge[1]
            self.__k_edges[x+1, y+1] = self.__optimal
            
        #print("literals", self.__literals)
        #print()
        #print("grid", self.__grid)
        #print()
        #print("k_edges", self.__k_edges)
        #print()
        #print("clusters", self.__clusters)
        #print()
        #print("answers", self.__answers)
        #print()
        

        
    def propagate(self, control, changes):
        states   = self.__states[control.thread_id]
        #clusters = self.__clusters[control.thread_id]
        literals = self.__literals
        #grid     = self.__grid
        answers  = self.__answers
        #k        = self.__k
        display  = self.__display

        #print("begin propagate")

        for lit in changes:
            #print("propagate lit", lit)

            edge_answer = literals[lit]
            states[lit] = edge_answer

            x    = edge_answer[0]
            y    = edge_answer[1]
            ans1 = edge_answer[2]
            ans2 = edge_answer[3]

            edge = (x,y)

            answer_set_1 = answers[ans1]
            answer_set_2 = answers[ans2]
            dist = distance(answer_set_1, answer_set_2)
            #print("  dist:", dist, "prev dist", self.__k_edges[edge])
            if dist < self.__k_edges[edge]:
                #print("  update distance k")
                self.__k_edges[edge] = dist
            elif dist > self.__k_edges[edge]:                
                nogood = []
                for lit, value in states.items():
                    nogood.append(lit)                
                #print("nogood", nogood)
                if not control.add_nogood(nogood) or not control.propagate():
                    return

            #print("states", states)
            #print("k", self.__k_edges)
            #print()
            
        #print("end propagate")
        #print()
        if self.__display:
            print("states", states)
            print("clusters", clusters)
            print("k after propagate:", self.__k)
            print("")

    def undo(self, thread_id, assignment, changes):
        states = self.__states[thread_id]
        #clusters = self.__clusters[thread_id]
        literals = self.__literals
        #grid     = self.__grid
        answers  = self.__answers
        #k        = self.__k
        display  = self.__display

        #print("begin undo")
        
        for lit in changes:
            if lit in states:
                #print("undo lit", lit)
                del states[lit]

                edge_answer = literals[lit]

                x    = edge_answer[0]
                y    = edge_answer[1]
                edge = (x,y)

                self.__k_edges[edge] = self.__optimal
               
                #print("states", states)
        #print("end undo")

    def check(self, control):
        print("Check................................................................................")
        #if self.__k <= self.__optimal:
        #    self.__optimal = self.__k
        #    print("optimal", self.__optimal)
