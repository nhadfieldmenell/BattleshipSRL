#!/usr/bin/env python

from sdd import SddNode
from psdd import PSddNode

class SddManager:
    Node = SddNode # native node class

    def __init__(self,vtree):
        self.vtree = vtree
        self.var_count = vtree.var_count
        self.unique = {}
        self.id_counter = 0

        self.setup_var_to_vtree(vtree)
        self.setup_terminal_sdds()

    def setup_terminal_sdds(self):
        # create terminal SDDs
        self.false = self.Node(SddNode._FALSE,None,None,self)
        self.true = self.Node(SddNode._TRUE,None,None,self)
        self.setup_literal_sdds()

    def setup_literal_sdds(self):
        lit_type = SddNode._LITERAL
        self.literals = [None]*(2*self.var_count+1)
        for var in xrange(1,self.var_count+1):
            vtree = self.var_to_vtree[var]
            self.literals[var] = self.Node(lit_type,var,vtree,self)
            self.literals[-var] = self.Node(lit_type,-var,vtree,self)

    def setup_var_to_vtree(self,vtree):
        self.var_to_vtree = [None]*(self.var_count+1)
        for node in vtree:
            if node.is_leaf():
                self.var_to_vtree[node.var] = node

    """negate an SDD node."""
    def negate(self,node,vtree):
        if   node.is_false(): return self.true_sdds[vtree.id]
        elif node.is_true(): return self.false_sdds[vtree.id]
        elif node.is_literal(): return self.literals[-node.literal]
        elif node.negation is not None: return node.negation
        else: # node.is_decomposition()
            elements = []
            right = node.vtree.right
            for prime,sub in node.elements:
                neg_sub   = self.negate(sub,right)
                elements += [prime,neg_sub]
            neg = self.lookup_node(elements,vtree)
            neg.negation = node
            node.negation = neg
            return neg

    def _canonical_elements(self,elements):
        """given a flat list of elements, canonicalize them"""
        #elf = frozenset
        #elf = tuple # AC
        cmpf = lambda x,y: cmp(x[0].id,y[0].id)
        elf = lambda x: tuple(sorted(x,cmp=cmpf))
        elements = elf( element for element in pairs(elements) )
        return elements

    """lookup decomposition node.
       assumes elements is a flat list [ p1,s1,p2,s2,...,pn,sn ]"""
    def lookup_node(self,elements,vtree_node):
        elements = self._canonical_elements(elements)
        if elements not in self.unique:
            node_type = SddNode._DECOMPOSITION
            node = self.Node(node_type,elements,vtree_node,self)
            self.unique[elements] = node
        return self.unique[elements]

    """ given an SDD, make into a true (uncompressed) SDD.
        this version does look-ups and merges things it probably shouldn't"""
    """
    def make_true(self,node,first_call=True):
        if node.bit is True: return node
        node.bit = True

        if not node.is_decomposition():
            new_node = self.true
        else: # is decomposition
            elements = []
            for prime,sub in node.elements:
                sub = self.make_true(sub,first_call=False)
                elements += [prime,sub]
            new_node = self.lookup_node(elements,node.vtree)

        new_node.bit = True
        if first_call:
            node.clear_bits()
            new_node.clear_bits()
        return new_node
    """

class PSddManager(SddManager):
    Node = PSddNode # native node class

    def __init__(self,vtree):
        SddManager.__init__(self,vtree)
        self.setup_true_false_sdds()

    """input sdd should belong to a different manager"""
    def copy_and_normalize_sdd(self,sdd,vtree):
        for node in sdd:
            if   node.is_false():   node.data = self.false
            elif node.is_true():    node.data = self.true
            elif node.is_literal(): node.data = self.literals[node.literal]
            else: # node.is_decomposition()
                elements = []
                left,right = node.vtree.left,node.vtree.right
                for prime,sub in node.elements:
                    copy_prime = self._normalize_sdd(prime.data,left)
                    copy_sub   = self._normalize_sdd(sub.data,right)
                    elements += [copy_prime,copy_sub]
                copy_node = self.lookup_node(elements,node.vtree)
                node.data = copy_node
        root_sdd = self._normalize_sdd(node.data,vtree)
        node.clear_data()
        return root_sdd

    """normalize sdd for current manager"""
    def _normalize_sdd(self,sdd,vtree):
        # first, cover the basic cases
        if sdd.is_false(): return self.false_sdds[vtree.id]
        elif sdd.is_true(): return self.true_sdds[vtree.id]
        elif sdd.vtree is vtree: return sdd

        if sdd.vtree.id < vtree.id: # left child
            left = self._normalize_sdd(sdd,vtree.left)
            right = self.true_sdds[vtree.right.id]
            neg_left = self.negate(left,vtree.left)
            false_right = self.false_sdds[vtree.right.id]
            elements = [ left,right,neg_left,false_right ]
        elif sdd.vtree.id > vtree.id: # right child
            left = self.true_sdds[vtree.left.id]
            right = self._normalize_sdd(sdd,vtree.right)
            elements = [ left,right ]
        return self.lookup_node(elements,vtree)

    """setup true SDDs for each vtree node"""
    def setup_true_false_sdds(self):
        node_count = 2*self.var_count - 1
        self.true_sdds = [None]*node_count
        self.false_sdds = [None]*node_count

        for vtree_node in self.vtree.post_order():
            # setup true SDDs
            if vtree_node.is_leaf():
                node_type = SddNode._TRUE
                node = self.Node(node_type,None,vtree_node,self)
            else:
                left_true  = self.true_sdds[vtree_node.left.id]
                right_true = self.true_sdds[vtree_node.right.id]
                elements = [left_true,right_true]
                node = self.lookup_node(elements,vtree_node)
            self.true_sdds[vtree_node.id] = node
            true_node = node

            # setup false SDDs
            if vtree_node.is_leaf():
                node_type = SddNode._FALSE
                node = self.Node(node_type,None,vtree_node,self)
            else:
                left_true   = self.true_sdds[vtree_node.left.id]
                right_false = self.false_sdds[vtree_node.right.id]
                elements = [left_true,right_false]
                node = self.lookup_node(elements,vtree_node)
            self.false_sdds[vtree_node.id] = node
            false_node = node
            false_node.is_false_sdd = True

            true_node.negation = false_node
            false_node.negation = true_node

    def make_unique_true_sdds(self,sdd,make_true=False):
        """If true appears in a decomposition, we make it a unique true node.

        If make_true is True, then the SDD is converted to one
        equivalent to a true function.  To do this, we need to
        recursively make all subs true.  To do this, It suffices to
        make all nodes normalized for the right-most vtree node to
        True.
        """

        last_node = sdd.vtree.last_node()
        for node in sdd:
            if not node.is_decomposition(): continue

            new_elements = []
            replace_elements = False
            for prime,sub in node.elements:
                new_elements.append(prime)
                new_elements.append(sub)

            for i,alpha in enumerate(new_elements):
                if alpha.is_true() or \
                   ( make_true and alpha.vtree is last_node ):
                    replace_elements = True
                    node_type = SddNode._TRUE
                    new_node = self.Node(node_type,None,alpha.vtree,self)
                    new_elements[i] = new_node

            if replace_elements:
                node.elements = self._canonical_elements(new_elements)

        # clear old true bits
        for node in self.true_sdds: node.bit = False
        sdd.array = None

    def create_node_map(self,psdd,pmanager):
        """given a psdd created for a different manager, 
        where the same psdd exists in the current manager,
        create a map from nodes of the other manager
        to nodes in the current manager"""

        if pmanager.var_count != self.var_count:
            print "error: var count is not compatible"
            raise Exception

        # map the basic psdds
        node_map = {}
        node_map[pmanager.true] = self.true
        node_map[pmanager.false] = self.false
        for node,my_node in zip(pmanager.true_sdds,self.true_sdds):
            node_map[node] = my_node
        for node,my_node in zip(pmanager.false_sdds,self.false_sdds):
            node_map[node] = my_node
        for node,my_node in zip(pmanager.literals,self.literals):
            node_map[node] = my_node

        psdd.linearize()
        for node in psdd.array:
            if node.is_decomposition():
                elements = []
                for p,s in node.elements:
                    elements.append(node_map[p])
                    elements.append(node_map[s])
                elements = self._canonical_elements(elements)

                if elements not in self.unique:
                    print "error: node not found in manager"
                    raise Exception

                my_node = self.unique[elements]
                node_map[node] = my_node

        return node_map

def pairs(my_list):
    """a generator for (prime,sub) pairs"""
    if my_list is None: return
    it = iter(my_list)
    for x in it:
        y = it.next()
        yield (x,y)

########################################
# COMPUTED CACHE
########################################

class Computed:
    def __init__(self,value):
        self.value = value
        self.pr_context = 0.0
        self.pr_node = 0.0
        self.bit = False

class ComputedKey:
    def __init__(self,alpha,beta):
        self.alpha = alpha
        self.beta = beta

    def __hash__(self):
        return self.alpha.id + self.beta.id

    def __cmp__(self,other):
        x = cmp(self.alpha.id,other.alpha.id)
        if x != 0:
            x = cmp(self.beta.id,other.beta.id)
        return x

    def __eq__(self,other):
        return (self.alpha is other.alpha) and (self.beta is other.beta)

class ComputedCache:

    def __init__(self,vtree):
        self.size = 2*vtree.var_count - 1
        self.cache = [ dict() for i in xrange(self.size) ]

    def put(self,alpha,beta,value):
        """alpha is a psdd and beta is an sdd constraint"""
        key = (alpha,beta)
        #key = ComputedKey(alpha,beta)
        value = Computed(value)
        cache = self.cache[alpha.vtree.id]
        cache[key] = value

    def get(self,alpha,beta):
        """alpha is a psdd and beta is an sdd constraint"""
        key = (alpha,beta)
        #key = ComputedKey(alpha,beta)
        cache = self.cache[alpha.vtree.id]
        return cache.get(key,None)

    def clear(self):
        for cache in self.cache:
            cache.clear()
