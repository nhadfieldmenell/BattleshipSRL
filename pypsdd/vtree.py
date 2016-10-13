#!/usr/bin/env python

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

    """in-order generator

    see also pre-order generator and post-order generator.  using a
    generator can lead to simpler code than a recursive function, but
    it is also slower than recursion.

    """
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

    """returns a list of vtree nodes, indexed by id"""
    def nodes(self):
        node_count = 2*self.var_count - 1
        nodes = [None]*node_count
        for node in self:
            nodes[node.id] = node
        return nodes

    def last_node(self):
        if self.is_leaf():
            return self
        else:
            return self.right.last_node()

    def height(self):
        if self.is_leaf():
            return 0
        else:
            return 1 + max(self.left.height(),self.right.height())

    """sets id's of vtree nodes using in-order traversal"""
    """
    def set_ids(self,start=0):
        for node_id,node in enumerate(self,start):
            node.id = node_id
    """

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

    """read an SDD from file"""
    @staticmethod
    def read(filename):
        for line in open(filename,'r'):
            node = None
            if line.startswith('c'): continue
            elif line.startswith('vtree'):
                node_count = int(line[5:])
                nodes = [None]*node_count
            elif line.startswith('L'):
                node_id,var = [int(x) for x in line[2:].split()]
                node = Vtree(None,None,var)
            elif line.startswith('I'):
                node_id,left_id,right_id = [int(x) for x in line[2:].split()]
                left,right = nodes[left_id],nodes[right_id]
                node = Vtree(left,right,None)
                left.parent = right.parent = node
            if node:
                node.id = node_id
                nodes[node_id] = node

        return nodes[node_id]

    def save(self,filename):
        #self.set_ids()

        # open, write header
        f = open(filename,'w')
        f.write(Vtree.vtree_file_header)
        node_count = 2*self.var_count - 1
        f.write('vtree %d\n' % node_count)

        # write nodes
        for n in self.post_order(): f.write('%s\n' % n)

        f.close()

    def __repr__(self):
        if self.is_leaf():
            st = 'L %d %d' % (self.id,self.var)
        else:
            st = 'I %d %d %d' % (self.id,self.left.id,self.right.id)
        return st
