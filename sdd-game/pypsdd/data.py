#!/usr/bin/env python

import math
import random
from itertools import izip

from collections import defaultdict

class DataSet:
    def __init__(self,data,clone=True):
        if clone is True:
            self.data = DataSet._new_dict()
            self.data.update(data)
        else:
            self.data = data
        self.N = sum(self.data.values())
        self.is_flat = False

    def __iter__(self):
        if self.is_flat:
            for instance in self.data:
                yield (instance,1)
        else:
            for instance,count in self.data.iteritems():
                yield (instance,count)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        items = self.data.items()
        items.sort(cmp=lambda x,y:-cmp(x[1],y[1]))
        fmt = " %%%dd %%s" % len(str(items[0][1]))
        to_str = lambda val: str(val) if val >= 0 else '.'
        st = [ fmt % (count,"".join(map(to_str,instance))) 
                      for instance,count in items ]
        return "\n".join(st)

    @staticmethod
    def _new_dict():
        return defaultdict(lambda: 0)

    @staticmethod
    def to_dict(instances,counts=None):
        if counts == None:
            counts = [1]*len(instances)
        data = DataSet._new_dict()
        for instance,count in izip(instances,counts):
            data[instance] += count
        return DataSet(data,clone=False)

    """read a dataset from file"""
    @staticmethod
    def read(filename):
        # hash map of instances to counts, default count is 0
        data = DataSet._new_dict()
        for line in open(filename,'r'):
            if line.find(',') >= 0:
                instance = tuple( int(x) for x in line.split(',') )
            else:
                instance = tuple( int(x) for x in line.split(' ') )
            data[instance] += 1
        return DataSet(data,clone=False)

    @staticmethod
    def read_flat(filename):
        dataset = DataSet({})
        dataset.is_flat = True

        f = open(filename,'r')
        dataset.N = sum(1 for line in f)
        f.close()
        dataset.data = [None] * dataset.N

        f = open(filename,'r')
        for i,line in enumerate(f):
            if line.find(',') >= 0:
                instance = tuple( int(x) for x in line.split(',') )
            else:
                instance = tuple( int(x) for x in line.split(' ') )
            dataset.data[i] = instance
        f.close()
            
        return dataset

    @staticmethod
    def evidence(instance):
        var_count = len(instance)
        return dict( (var+1,instance[var]) for var in xrange(var_count) \
                     if instance[var] >= 0 )

    def to_csv(self,filename):
        instances = []
        for instance,count in self:
            for i in xrange(count):
                instances.append(instance)
        random.shuffle(instances)
        f = open(filename,'w')
        for instance in instances:
            #instance = [ x if x != -1 else '.' for x in instance ]
            f.write(",".join(str(x) for x in instance))
            f.write("\n")
        f.close()

    def log_likelihood(self):
        """log likelihood of a dataset, given the data distribution"""
        ll = 0.0
        N = float(self.N)
        for instance,count in self:
            p = count/N
            ll += count * math.log(p)
        return ll

    def split(self,p,seed=None):
        """split a dataset into two parts, of proportion p and 1-p"""
        if seed: random.seed(seed)
        d1,d2 = DataSet._new_dict(),DataSet._new_dict()
        instances = []
        for instance,count in self:
            for i in xrange(count):
                instances.append(instance)
        random.shuffle(instances)
        p1 = int(self.N*p)
        for instance in instances[:p1]:
            d1[instance] += 1
        for instance in instances[p1:]:
            d2[instance] += 1
        return DataSet(d1,clone=False),DataSet(d2,clone=False)

    @staticmethod
    def simulate(sdd,N,seed=None):
        if seed: random.seed(seed)

        data = DataSet._new_dict()
        for i in xrange(N):
            instance = tuple(sdd.simulate())
            data[instance] += 1
        return DataSet(data,clone=False)

    @staticmethod
    def simulate_flat(sdd,N,seed=None):
        if seed: random.seed(seed)
        data = [ tuple(sdd.simulate()) for i in xrange(N) ]
        return data

    def simulate_from_dataset(self,N,seed=None):
        if seed: random.seed(seed)

        data = DataSet._new_dict()
        for i in xrange(N):
            p = random.randint(1,self.N) - 1
            q = 0
            for instance,count in self.data.iteritems():
                q += count
                if p < q: break
            data[instance] += 1
        return DataSet(data,clone=False)

    def hide_values_at_random(self,p,seed=None):
        """for each instance, for each value, hide with probability p"""
        if seed: random.seed(seed)

        data = DataSet._new_dict()
        for complete_instance,count in self.data.iteritems():
            for i in xrange(count):
                instance = [ -1 if random.random() < p else val \
                             for val in complete_instance ]
                instance = tuple(instance)
                data[instance] += 1
        return DataSet(data,clone=False)

    @staticmethod
    def instances(var_count):
        inst = [0] * var_count
        done = False
        i = 0
        while i >= 0:
            yield inst

            i = var_count - 1
            while i >= 0:
                inst[i] += 1
                if inst[i] == 2:
                    inst[i] = 0
                else:
                    break
                i -= 1

    @staticmethod
    def union(dataset1,dataset2):
        data = DataSet._new_dict()
        data.update(dataset1)
        data.update(dataset2)
        return DataSet(data,clone=False)

    def ranking_encoding(self,n):
        """ranking dataset to encoded dataset"""
        data = DataSet._new_dict()
        for instance,count in self:
            encoded = [0] * (n*n)
            for i,j in enumerate(instance):
                encoded[ i*n+j ] = 1
            encoded = tuple(encoded)
            data[encoded] = count
        return DataSet(data,clone=False)

    def remap(self,mapping):
        data = DataSet._new_dict()
        for instance,count in self:
            remapped = [ mapping[item] for item in instance ]
            remapped = tuple(remapped)
            data[remapped] = count
        return DataSet(data,clone=False)
