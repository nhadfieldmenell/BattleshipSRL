import time
from pypsdd import *

if __name__ == '__main__':
    n = 3
    vtree_filename = 'pypsdd/tests/ranking-%d.vtree' % n
    sdd_filename = 'pypsdd/tests/ranking-%d.sdd' % n

    N = 2**10
    seed = 0

    # READ SDD
    start = time.time()
    vtree = Vtree.read(vtree_filename)
    manager = SddManager(vtree)
    alpha = SddNode.read(sdd_filename,manager)
    sdd_read_time = time.time()-start

    # PRINT SOME SDD STATS
    print "================================"
    print "  sdd read time: %.3fs" % sdd_read_time
    print "sdd model count: %d" % alpha.model_count()
    print " sdd node count: %d" % alpha.node_count()
    print "       sdd size: %d" % alpha.size()

    # CONVERT TO PSDD
    start = time.time()
    pmanager = PSddManager(vtree)
    psdd = pmanager.copy_and_normalize_sdd(alpha,vtree)
    # pmanager.make_unique_true_sdds(copy,make_true=False)
    psdd_conv_time = time.time()-start

    # PRINT SOME PSDD STATS
    print "================================"
    print " psdd conv time: %.3fs" % psdd_conv_time
    print "psdd node count: %d" % psdd.node_count()

    # SIMULATE DATASETS
    psdd.uniform_weights()
    training = DataSet.simulate(psdd,N,seed=seed)
    testing  = DataSet.simulate(psdd,N,seed=(seed+1))

    # DATASET STATS
    print "================================"
    print "   training size: %d" % training.N
    print "    testing size: %d" % testing.N
    print " unique training: %d" % len(training)
    print "  unique testing: %d" % len(testing)

    # LEARN A PSDD
    start = time.time()
    psi,scale = None,8.0
    psdd.learn(training,psi=psi,scale=scale,show_progress=False)
    train_ll = psdd.log_likelihood_alt(training)/training.N
    test_ll = psdd.log_likelihood_alt(testing)/testing.N
    learn_time = time.time()-start

    # DATASET STATS
    print "================================"
    print "   learning time: %.3f" % learn_time
    print "     training ll: %.8f" % train_ll
    print "      testing ll: %.8f" % test_ll
