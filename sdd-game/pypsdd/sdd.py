#!/usr/bin/env python

class SddNode:
    _FALSE,_TRUE,_LITERAL,_DECOMPOSITION = 0,1,2,3

########################################
# CONSTRUCTOR
########################################

    def __init__(self,node_type,alpha,vtree,manager):
        self.node_type = node_type
        self.vtree = vtree
        if self.is_false() or self.is_true():
            self.literal = None
            self.elements = None
        elif self.is_literal():
            self.literal = alpha
            self.elements = None
        else: # self.is_decomposition()
            self.literal = None
            self.elements = alpha
        self.id = manager.id_counter
        manager.id_counter += 1
        self.data = None
        self.bit = False
        self.array = None

    def is_false(self):
        return self.node_type is SddNode._FALSE

    def is_true(self):
        return self.node_type is SddNode._TRUE

    def is_literal(self):
        return self.node_type is SddNode._LITERAL

    def is_decomposition(self):
        return self.node_type is SddNode._DECOMPOSITION

########################################
# TRAVERSAL
########################################

    """post-order (bottom-up) generator (SLOW, use array if possible)"""
    def __iter__(self,first_call=True):
        if self.bit: return
        self.bit = True

        if self.is_decomposition():
            for p,s in self.elements:
                for node in p.__iter__(first_call=False): yield node
                for node in s.__iter__(first_call=False): yield node
        yield self

        if first_call: self.clear_bits()

    """pre-order generator (SLOW, use array if possible)"""
    def pre_order(self,first_call=True):
        if self.bit: return
        self.bit = True

        yield self
        if self.is_decomposition():
            for p,s in self.elements:
                for node in p.pre_order(first_call=False): yield node
                for node in s.pre_order(first_call=False): yield node

        if first_call: self.clear_bits()

    """linearize SDD"""
    def linearize(self):
        if self.array is not None: return
        node_count = self.node_count()
        self.array = [None] * node_count
        for i,node in enumerate(self):
            self.array[i] = node

    """recursively clears bits"""
    def clear_bits(self):
        if self.bit is False: return
        self.bit = False
        if self.is_decomposition():
            for p,s in self.elements:
                p.clear_bits()
                s.clear_bits()

    """recursively clears data
    AC: this is really slow, try not to use this"""
    def clear_data(self):
        for node in self: node.data = None

    def node_count(self):
        count = 0
        for node in self: count += 1
        return count

    def size(self):
        sdd_size = 0
        self.linearize()
        for node in self.array:
            if node.is_decomposition():
                sdd_size += len(node.elements)
        return sdd_size

    """AC: this needs to go away"""
    def set_ids(self):
        for node_id,node in enumerate(self.pre_order()):
            node.id = node_id

########################################
# QUERIES
########################################

    def model_count(self):
        self.linearize()
        for node in self.array:
            if node.is_false():
                count = 0
            elif node.is_true():
                count = 1 # AC: for trimmed SDDs
            elif node.is_literal():
                count = 1
            else: # node.is_decomposition()
                count = 0
                left_count  = node.vtree.left.var_count
                right_count = node.vtree.right.var_count
                for prime,sub in node.elements:
                    if sub.is_false(): continue
                    left_gap = left_count if prime.is_true() else \
                        left_count - prime.vtree.var_count
                    prime_mc = prime.data << left_gap
                    right_gap = right_count if sub.is_true() else \
                        right_count - sub.vtree.var_count
                    sub_mc = sub.data << right_gap

                    count += prime_mc*sub_mc
            node.data = count

        for node in self.array: node.data = None
        return count

    def is_model(self,instance):
        self.linearize()
        for node in self.array:
            if node.is_false():
                is_model = False
            elif node.is_true():
                is_model = True
            elif node.is_literal():
                var = node.vtree.var
                lit = var if instance[var-1] == 1 else -var
                is_model = lit == node.literal
            else: # node.is_decomposition()
                is_model = False
                for prime,sub in node.elements:
                    if sub.is_false(): continue
                    if prime.data and sub.data:
                        is_model =True
                        break
            node.data = is_model

        for node in self.array: node.data = None
        return is_model
        

########################################
# I/O
########################################

    sdd_file_header = """c ids of sdd nodes start at 0
c sdd nodes appear bottom-up, children before parents
c
c file syntax:
c sdd count-of-sdd-nodes
c F id-of-false-sdd-node
c T id-of-true-sdd-node
c L id-of-literal-sdd-node id-of-vtree literal
c D id-of-decomposition-sdd-node id-of-vtree number-of-elements {id-of-prime id-of-sub}*
c
"""

    """this basically assumes a brand new manager, 
    with a correct vtree."""
    @staticmethod
    def read(filename,manager):
        vtree_nodes = manager.vtree.nodes()
        f = open(filename,'r')
        for line in f:
            node = None
            if line.startswith('c'): continue
            elif line.startswith('sdd'):
                node_count = int(line[3:])
                nodes = [None]*node_count
            elif line.startswith('F'):
                node_id = int(line[2:])
                node = manager.false
            elif line.startswith('T'):
                node_id = int(line[2:])
                node = manager.true
            elif line.startswith('L'):
                node_id,vtree_id,lit = [ int(x) for x in line[2:].split() ]
                node = manager.literals[lit]
            elif line.startswith('D'):
                line = [ int(x) for x in line[2:].split() ]
                node_id,vtree_id,size = line[:3]
                elements = [ nodes[my_id] for my_id in line[3:] ]
                vtree_node = vtree_nodes[vtree_id]
                node = manager.lookup_node(elements,vtree_node)
            if node:
                nodes[node_id] = node
        f.close()
        return node

    def __repr__(self):
        if self.is_false():
            st = 'F %d' % self.id
        elif self.is_true():
            st = 'T %d' % self.id
        elif self.is_literal():
            st = 'L %d %d %d' % (self.id,self.vtree.id,self.literal)
        else: # self.is_decomposition()
            self_size = len(self.elements)
            st = 'D %d %d %d ' % (self.id,self.vtree.id,self_size)
            st += " ".join( '%d %d' % (p.id,s.id) for p,s in self.elements )
        return st

    def save(self,filename):
        self.set_ids()

        # open, write header
        f = open(filename,'w')
        f.write(SddNode.sdd_file_header)
        f.write('sdd %d\n' % self.node_count())

        # write nodes
        for node in self: f.write('%s\n' % node)
        f.close()

    dot_node_format = '\nn%u [label= "%u",' \
        'style=filled,fillcolor=gray95,shape=circle,height=.25,width=.25]; '
    dot_element_format = '''\nn%ue%u
      [label= "<L>%s|<R>%s",
      shape=record,
      fontsize=20,
      fontname="Times-Italic",
      fillcolor=white,
      style=filled,
      fixedsize=true,
      height=.30,
      width=.65];
'''
    dot_or_format =    '\nn%u->n%ue%u [arrowsize=.50];'
    dot_prime_format = '\nn%ue%u:L:c->n%u ' \
        '[arrowsize=.50,tailclip=false,arrowtail=dot,dir=both];'
    dot_sub_format =   '\nn%ue%u:R:c->n%u ' \
        '[arrowsize=.50,tailclip=false,arrowtail=dot,dir=both];'
    dot_terminal_format = '\nn%u [label= "%s",shape=box]; '
    dot_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # AC
    dot_or_format_alt =    '\nn%u->n%ue%u [arrowsize=.50,label="%.2g"];'

    def save_as_dot(self,filename):
        self.set_ids()

        # open, write header
        f = open(filename,'w')
        f.write('\ndigraph sdd {')
        f.write('\n\noverlap=false')
        f.write('\n')
        if not self.is_decomposition():
            self.print_terminal_sdd_as_dot(f)
        self.print_node_ranks(f)

        # write nodes
        for node in self.pre_order():
            if not node.is_decomposition(): continue
            f.write(SddNode.dot_node_format % (node.id,node.vtree.id))
            
            #f.write('\nlab%u [label="%.2f"];\nn%u->lab%u ;' % \
            #        (node.id,node.pr_context,node.id,node.id))

            for i,(p,s) in enumerate(node.elements):
                p_label,s_label = p.node_label(),s.node_label()
                f.write(SddNode.dot_element_format % \
                            (node.id,i,p_label,s_label))
                if hasattr(node,'theta'):
                    theta = node.theta[(p,s)] #/node.theta_sum # AC
                else:
                    theta = 0
                f.write(SddNode.dot_or_format_alt % (node.id,node.id,i,theta))
                if p.is_decomposition():
                    f.write(SddNode.dot_prime_format % (node.id,i,p.id))
                if s.is_decomposition():
                    f.write(SddNode.dot_sub_format % (node.id,i,s.id))

        f.write('\n\n\n}')
        f.close()

    def print_node_ranks(self,f):
        pass

    def print_terminal_sdd_as_dot(self,f):
        label = self.node_label()
        f.write(SddNode.dot_terminal_format % (self.id,label))

    # return/create symbol for terminal SDD
    def node_label(self):
        if self.is_false(): return "&#8869;"
        elif self.is_true():
            #theta = self.theta[True]/self.theta_sum
            #label = SddNode.literal_label(self.vtree.var)
            #return "%.2g: %s" % (theta,label)
            return "&#8868;"
        elif self.is_literal(): return SddNode.literal_label(self.literal)
        else: return ""

    # return/create symbol for literal
    @staticmethod
    def literal_label(literal):
        var = abs(literal)
        neg_label = "&not;" if literal < 0 else ""
        var_label = SddNode.dot_names[var-1] if var <= 26 else str(var)
        return neg_label + var_label
