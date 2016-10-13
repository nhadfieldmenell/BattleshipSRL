#!/usr/bin/env python

########################################
# VTREE STUFF
########################################

class Vtree:
    def __init__(self,left,right,var):
        self.parent = None
        self.left = left
        self.right = right
        self.var = var
        self.id = None
        if self.var: # leaf
            self.var_count = 1
        else:
            self.var_count = left.var_count + right.var_count

    def __iter__(self):
        if self.is_leaf():
            yield self
        else:
            for node in self.left:  yield node
            yield self
            for node in self.right: yield node

    """pre-order generator"""
    def pre_order(self):
        if self.is_leaf():
            yield self
        else:
            yield self
            for node in self.left.pre_order():  yield node
            for node in self.right.pre_order(): yield node

    """post-order generator"""
    def post_order(self):
        if self.is_leaf():
            yield self
        else:
            for node in self.left.post_order():  yield node
            for node in self.right.post_order(): yield node
            yield self

    def is_leaf(self):
        return self.left is None # and self.right is None

    vtree_file_header = """c ids of vtree nodes start at 0
c ids of variables start at 1
c vtree nodes appear bottom-up, children before parents
c
c file syntax:
c vtree number-of-nodes-in-vtree
c L id-of-leaf-vtree-node id-of-variable
c I id-of-internal-vtree-node id-of-left-child id-of-right-child
c
"""

    def save(self,filename):
        self.set_ids()

        # open, write header
        f = open(filename,'w')
        f.write(Vtree.vtree_file_header)
        node_count = 2*self.var_count - 1
        f.write('vtree %d\n' % node_count)

        # write nodes
        for n in self.post_order(): f.write('%s\n' % n)

        f.close()

    def set_ids(self,start=0):
        for node_id,node in enumerate(self,start):
            node.id = node_id

    def __repr__(self):
        if self.is_leaf():
            st = 'L %d %d' % (self.id,self.var)
        else:
            st = 'I %d %d %d' % (self.id,self.left.id,self.right.id)
        return st

# right linear vtree over variables [start,start+size)
def right_linear_vtree(start,size):
    vtree = Vtree(None,None,start+size-1)
    for var in xrange(start+size-2,start-1,-1):
        var_vtree = Vtree(None,None,var)
        vtree = Vtree(var_vtree,vtree,None)
    return vtree

def right_linear_ordering_vtree(n):
    vtree = right_linear_vtree(n*(n-1)+1,n)
    #vtree = balanced_vtree(n*(n-1)+1,n)
    for var in xrange(n-1,0,-1):
        element_vtree = right_linear_vtree(n*(var-1)+1,n)
        vtree = Vtree(element_vtree,vtree,None)
    return vtree

def alt_right_linear_ordering_vtree():
    n = 9
    #ordering = [2,4,6,8,1,3,5,7,9]
    #ordering = [9,8,7,6,5,4,3,2,1]
    #ordering = [1,3,5,7,9,2,4,6,8]

    # var = ordering[-1]
    # vtree = right_linear_vtree(n*(var-1)+1,n)
    # for var in ordering[-2::-1]:
    #     element_vtree = right_linear_vtree(n*(var-1)+1,n)
    #     vtree = Vtree(element_vtree,vtree,None)
    # return vtree

    ordering = [1]
    var = ordering[-1]
    vtree = right_linear_vtree(n*(var-1)+1,n)
    for var in ordering[-2::-1]:
        element_vtree = right_linear_vtree(n*(var-1)+1,n)
        vtree = Vtree(element_vtree,vtree,None)
    vtree_left = vtree

    ordering = [2,3,4,5,6,7,8,9]
    var = ordering[-1]
    vtree = right_linear_vtree(n*(var-1)+1,n)
    for var in ordering[-2::-1]:
        element_vtree = right_linear_vtree(n*(var-1)+1,n)
        vtree = Vtree(element_vtree,vtree,None)
    vtree_right = vtree

    return Vtree(vtree_left,vtree_right,None)

# left linear vtree over variables [start,start+size)
def left_linear_vtree(start,size):
    vtree = Vtree(None,None,start)
    for var in xrange(start+1,start+size):
        var_vtree = Vtree(None,None,var)
        vtree = Vtree(vtree,var_vtree,None)
    return vtree

def left_linear_ordering_vtree(n):
    vtree = left_linear_vtree(1,n)
    for var in xrange(2,n+1):
        element_vtree = left_linear_vtree(n*(var-1)+1,n)
        vtree = Vtree(vtree,element_vtree,None)
    return vtree

def balanced_vtree(start,size):
    if size == 1: return Vtree(None,None,start)
    l_size = size/2 # integer division
    mid = start+l_size
    l_vtree = balanced_vtree(start,l_size)
    r_vtree = balanced_vtree(mid,size-l_size)
    return Vtree(l_vtree,r_vtree,None)

def balanced_ordering_vtree(n,start,size):
    if size == 1: return balanced_vtree(n*(start-1)+1,n)
    l_size = size/2 # integer division
    mid = start+l_size
    l_vtree = balanced_ordering_vtree(n,start,l_size)
    r_vtree = balanced_ordering_vtree(n,mid,size-l_size)
    return Vtree(l_vtree,r_vtree,None)

