#!/usr/bin/env python

from time import time
import sys

import sdd
#from structure import cardinality
from collections import defaultdict

def global_model_count(alpha,manager):
    mc = sdd.sdd_model_count(alpha,manager)
    var_count = sdd.sdd_manager_var_count(manager)
    var_used = sdd.sdd_variables(alpha,manager)
    for used in var_used[1:]:
        if not used:
            mc = 2*mc
    return mc

def all_false_term(var_list,manager):
    alpha = sdd.sdd_manager_true(manager)
    for var in var_list:
        lit = sdd.sdd_manager_literal(-var,manager)
        alpha = sdd.sdd_conjoin(alpha,lit,manager)
    return alpha

class Graph:
    def __init__(self,nodes,edges,source=None,sink=None):
        if source is None: source = nodes[0]
        self.nodes,self.edges = nodes,edges
        self.source,self.sink = source,sink
        self._find_incident()
        self._sort_edges(source)

    def _find_incident(self):
        self.incident = defaultdict(list)
        for edge in self.edges:
            x,y = edge
            self.incident[x].append(edge)
            self.incident[y].append(edge)

    # sort edges by distance from source (using breadth-first search)
    def _sort_edges(self,source):
        visited_nodes = set()
        visited_edges = set()
        import Queue
        queue = Queue.Queue()

        queue.put(source)
        sorted_edges = []
        
        while not queue.empty():
            node = queue.get()
            visited_nodes.add(node)
            incident = self.incident[node]
            incident = sorted(incident)
            for edge in incident:
                if edge in visited_edges: continue
                visited_edges.add(edge)
                sorted_edges.append(edge)
                x,y = edge
                if x not in visited_nodes: queue.put(x)
                if y not in visited_nodes: queue.put(y)

        if len(self.edges) != len(sorted_edges):
            raise Exception("Graph is not connected");

        self.edges = sorted_edges
        self.edge_to_index = {}
        for i,edge in enumerate(self.edges):
            self.edge_to_index[edge] = i

    @staticmethod
    def grid_graph(m,n):
        nodes = [ (i,j) for i in xrange(m) for j in xrange(n) ]
        edges = []
        edge_ok = lambda (x,y): x < m and y < n

        for node in nodes:
            # extend right
            neighbor = (node[0],node[1]+1)
            edge = (node,neighbor)
            if edge_ok(neighbor): edges.append(edge)

            # extend down
            neighbor = (node[0]+1,node[1])
            edge = (node,neighbor)
            if edge_ok(neighbor): edges.append(edge)

        return Graph(nodes,edges)

    @staticmethod
    def neighbor(node,edge):
        if edge[0] == node: return edge[1]
        if edge[1] == node: return edge[0]
        raise Exception("Edge does not mention node");

    # is sink reachable from source, only using nodes
    def reachable(self,source,sink,nodes):
        nodes = list(nodes)
        stack = [source]
        while stack:
            node = stack.pop()
            if node == sink: return True
            for edge in self.incident[node]:
                nb = Graph.neighbor(node,edge)
                if nb not in nodes: continue
                nodes.remove(nb)
                stack.append(nb)
        return False

    def incident_edges(self,node,nodes=None):
        if nodes is None: nodes = self.nodes
        edges = []
        for edge in self.incident[node]:
            nbr = Graph.neighbor(node,edge)
            if nbr not in nodes: continue
            edges.append(edge)
        return edges

def draw_grid(model,m,n,g):
    for i in xrange(m):
        for j in xrange(n):
            sys.stdout.write('.')
            if j < n-1:
                edge = ((i,j),(i,j+1))
                index = g.edge_to_index[edge] + 1
                sys.stdout.write('-' if model[index] else ' ')
        sys.stdout.write('\n')
        if i < m-1:
            for j in xrange(n):
                edge = ((i,j),(i+1,j))
                index = g.edge_to_index[edge] + 1
                sys.stdout.write('|' if model[index] else ' ')
                sys.stdout.write(' ')
        sys.stdout.write('\n')

def print_grids(alpha,m,n,g,manager):
    from inf import models
    var_count = m*(n-1) + (m-1)*n
    #print "COUNT:", sdd.sdd_model_count(alpha,manager)
    print "COUNT:", global_model_count(alpha,manager)
    for model in models.models(alpha,sdd.sdd_manager_vtree(manager)):
        print models.str_model(model,var_count=var_count)
        draw_grid(model,m,n,g)

def _encode_grid_aux(source,sink,nodes,graph,manager,
                     base=None,cache=None,verbose=False):
    nodes = sorted(nodes)
    key = (source,tuple(nodes))

    if cache and key in cache:
        return cache[key]

    if True: # INITIALIZATION FOR (S,T) PATHS
        if sink not in nodes: # unreachable
            return sdd.sdd_manager_false(manager)

        if len(nodes) == 1: # must be sink
            return sdd.sdd_manager_true(manager)

        if not g.reachable(source,sink,nodes):
            alpha = sdd.sdd_manager_false(manager)
            cache[key] = alpha
            return alpha

        if source == sink:
            # turn off all other edges
            alpha = sdd.sdd_manager_true(manager)
            sdd.sdd_ref(alpha,manager)

            my_nodes = list(nodes)
            my_nodes.remove(source)
            for node in my_nodes: # for all unused nodes
                edges = graph.incident_edges(node,nodes=nodes)
                sdd_vars = [ graph.edge_to_index[edge] + 1 for edge in edges ]
                all_false = all_false_term(sdd_vars,manager)
                alpha,tmp = sdd.sdd_conjoin(alpha,all_false,manager),alpha
                sdd.sdd_ref(alpha,manager); sdd.sdd_deref(tmp,manager)

            cache[key] = alpha
            return alpha

        alpha = sdd.sdd_manager_false(manager)
        sdd.sdd_ref(alpha,manager)

    else: # INITIALIZATION FOR ALL PATHS STARTING FROM S

        # empty graph, source should equal sink
        if len(nodes) == 1:
            return sdd.sdd_manager_true(manager)

        # initial case: no more paths
        alpha = sdd.sdd_manager_true(manager)
        sdd.sdd_ref(alpha,manager)

        my_nodes = list(nodes)
        my_nodes.remove(source)
        for node in my_nodes: # for all unused nodes
            edges = graph.incident_edges(node,nodes=nodes)
            sdd_vars = [ graph.edge_to_index[edge] + 1 for edge in edges ]
            all_false = all_false_term(sdd_vars,manager)
            alpha,tmp = sdd.sdd_conjoin(alpha,all_false,manager),alpha
            sdd.sdd_ref(alpha,manager); sdd.sdd_deref(tmp,manager)

    # after this, try to extend the paths
    # first, find incident edges
    edges = graph.incident_edges(source,nodes=nodes)
    sdd_vars = [ graph.edge_to_index[edge] + 1 for edge in edges ]
    all_false = all_false_term(sdd_vars,manager)
    sdd.sdd_ref(all_false,manager)

    # for each incident edge
    my_nodes = list(nodes)
    my_nodes.remove(source)
    for edge,sdd_var in zip(edges,sdd_vars):

        # recurse
        neighbor = Graph.neighbor(source,edge)
        gamma = _encode_grid_aux(neighbor,sink,my_nodes,graph,manager,
                                 base=base,cache=cache,verbose=verbose)
        if sdd.sdd_node_is_false(gamma): continue

        # exactly one edge on
        sdd_lit = sdd.sdd_manager_literal(sdd_var,manager)
        beta = sdd.sdd_exists(sdd_var,all_false,manager)
        beta = sdd.sdd_conjoin(beta,sdd_lit,manager)
        beta = sdd.sdd_conjoin(beta,gamma,manager)

        # accumulate
        alpha,tmp = sdd.sdd_disjoin(alpha,beta,manager),alpha
        sdd.sdd_ref(alpha,manager); sdd.sdd_deref(tmp,manager)
        
    sdd.sdd_deref(all_false,manager)
    cache[key] = alpha

    return alpha

def _encode_graph(g,manager):

    # init structures
    cache = defaultdict(dict)
    base = sdd.sdd_manager_true(manager)

    sink = g.nodes[-1]
    alpha = _encode_grid_aux(g.source,sink,g.nodes,g,manager,
                             base=base,cache=cache,verbose=False)

    # deref everything in cache
    for key in cache:
        beta = cache[key]
        sdd.sdd_deref(beta,manager)

    #sdd.sdd_ref(alpha,manager)

    return alpha

def encode_graph(g,manager):
    print "encoding graphs ..."
    start = time()    
    sdd.sdd_manager_auto_gc_and_minimize_off(manager) # ACACAC
    alpha = _encode_graph(g,manager)
    print "done! (%.3fs)" % (time()-start)

    print "model count..."
    print "sdd mc  :", sdd.sdd_model_count(alpha,manager)
    print "sdd mc-g:", global_model_count(alpha,manager)

    #print "minimizing ..."
    #sdd.sdd_ref(alpha,manager)
    #sdd.sdd_manager_minimize(manager)
    #sdd.sdd_deref(alpha,manager)
    print "sdd size:", sdd.sdd_size(alpha)
    print "sdd nc  :", sdd.sdd_count(alpha)
    return alpha

def start_manager(graph):
    var_count = len(graph.edges)
    vtree = sdd.sdd_vtree_new(var_count,"right")
    manager = sdd.sdd_manager_new(vtree)
    sdd.sdd_vtree_free(vtree)
    return manager

########################################
# MAIN
########################################

# THESE ARE THE COUNTS FOR (S,T) PATHS ON NxN GRIDS
# 2
# 12
# 184
# 8512
# 1262816
# 575780564
# 789360053252
# 3266598486981642
# 41044208702632496804
# 1568758030464750013214100
# 182413291514248049241470885236 
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "usage: %s [GRID-M] [GRID-N]" % sys.argv[0]
        exit(1)
    m,n = (int(sys.argv[1]),int(sys.argv[2]))
    g = Graph.grid_graph(m,n)

    manager = start_manager(g)
    alpha = encode_graph(g,manager)
    #sdd.sdd_deref(alpha,manager)
    print_grids(alpha,m,n,g,manager)

    """ UNCOMMENT TO SAVE SDD/VTREE
    sdd_filename = "paths-%d-%d.sdd" % (m,n)
    sdd_vtree_filename = "paths-%d-%d.vtree" % (m,n)
    sdd.sdd_save(sdd_filename,alpha)
    sdd.sdd_vtree_save(sdd_vtree_filename,sdd.sdd_manager_vtree(manager))
    """

    print "===================="
    print "before garbage collecting..." 
    print "live size:", sdd.sdd_manager_live_count(manager)
    print "dead size:", sdd.sdd_manager_dead_count(manager)
    print "garbage collecting..."
    sdd.sdd_manager_garbage_collect(manager)
    print "live size:", sdd.sdd_manager_live_count(manager)
    print "dead size:", sdd.sdd_manager_dead_count(manager)
