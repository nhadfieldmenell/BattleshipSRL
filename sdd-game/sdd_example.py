#!/usr/bin/python
import sdd
from inf import models


def start_manager(num_vars):
    """Construct an SDD manager with num_vars variables.

    Args:
        num_vars: the number of variables to use in the SDD.

    Returns:
        An initialized SDD manager with a right vtree.
    """
    vtree = sdd.sdd_vtree_new(num_vars, "right")
    manager = sdd.sdd_manager_new(vtree)
    sdd.sdd_vtree_free(vtree)
    return manager


def main():
    num_vars = 5
    man = start_manager(num_vars)
    alpha = sdd.sdd_manager_true(manager)
    for i in range(num_vars):
        lit = sdd.sdd_manager_literal(i, manager)
        alpha = sdd.sdd_conjoin(alpha, lit, manager)

    for model in model.models(alpha, sdd.sdd_manager_vtree(manager)):
        print model

    print "yass"



if __name__ == '__main__':
    main()
